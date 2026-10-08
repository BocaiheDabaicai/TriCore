# 单元执行器 —— 把一个单元跑起来：建上下文、按步执行、留痕、收尾
#
# 单元代码长这样（见 units/*.py）：
#     def run(ctx):
#         with ctx.step("open"):        # 声明了这几步，顺序必须一致
#             ctx.page.goto(...)
#         with ctx.step("fill"):
#             ...
# ctx.step 用 with 语法：进来自动标"进行中"，出来自动标"成功"；出异常自动标"失败"并留现场截图。

import threading
import time

from core.browser import worker
from services import run_service


class Canceled(Exception):
    """人工取消（在步骤之间检查，不会强行打断正在进行的页面操作）"""


class StepOrderError(Exception):
    """单元代码里 ctx.step() 的顺序与 UNIT 里声明的步骤对不上——声明和代码漂移了，必须立刻暴露"""


# 每个正在排队的运行一个取消开关；跑完就清掉
_cancel_events: dict[int, threading.Event] = {}


def new_cancel_event(run_id: int) -> threading.Event:
    event = threading.Event()
    _cancel_events[run_id] = event
    return event


def cancel_run(run_id: int) -> bool:
    event = _cancel_events.get(run_id)
    if not event:
        return False
    event.set()
    return True


class StepHandle:
    """一步的句柄：with 进出自带状态记录"""

    def __init__(self, ctx, idx: int, step_key: str, cn_name: str):
        self.ctx = ctx
        self.idx = idx
        self.step_key = step_key
        self.cn_name = cn_name
        self._t0 = 0.0

    def __enter__(self):
        self.ctx.touch()
        self.ctx.check_cancel()
        self.ctx.begin_step_capture()
        run_service.step_started(self.ctx.run_id, self.idx, self.cn_name)
        self._t0 = time.time()
        return self

    def __exit__(self, exc_type, exc, tb):
        ms = int((time.time() - self._t0) * 1000)
        if exc_type is None:
            # 这一步里单元主动截的图（比如"填完的样子"），挂到步骤上给界面看
            run_service.step_finished(self.ctx.run_id, self.idx, "success", ms,
                                      screenshot=self.ctx.last_step_shot)
            return False

        if issubclass(exc_type, Canceled):
            run_service.step_finished(self.ctx.run_id, self.idx, "skipped", ms, error="已取消")
            return False

        # 失败即留现场：截图 + 页面 HTML，排查时能回答"当时页面上到底是什么"
        shot = self.ctx.snap("failed")
        self.ctx.dump_html("failed")
        msg = str(exc)[:500] or exc_type.__name__
        run_service.step_finished(self.ctx.run_id, self.idx, "failed", ms, screenshot=shot, error=msg)
        self.ctx.failed_step = self.idx
        self.ctx.failed_msg = msg
        return False


class UnitContext:
    """单元运行时能用的东西：页面、输入、分步、日志、截图"""

    def __init__(self, run_id: int, unit, inputs: dict, page, cancel_event: threading.Event):
        self.run_id = run_id
        self.unit = unit
        self.inputs = inputs
        self.page = page
        self._cancel = cancel_event
        self._idx = 0            # 下一个该执行的步骤下标
        self._current_idx = 0
        self.last_step_shot: str | None = None   # 本步最后一次截图的文件名
        self.failed_step: int | None = None
        self.failed_msg: str = ""
        self._run_dir = None

    # ---- 分步 ----

    def step(self, step_key: str) -> StepHandle:
        """开启一步；step_key 必须与 UNIT["steps"] 声明的顺序一致（漂移立刻报错，不做兼容）"""
        declared = self.unit.steps
        if self._idx >= len(declared):
            raise StepOrderError(f"单元 {self.unit.key} 多执行了一步 {step_key}（只声明了 {len(declared)} 步）")
        expect = declared[self._idx]
        if expect["key"] != step_key:
            raise StepOrderError(
                f"单元 {self.unit.key} 第 {self._idx + 1} 步对不上：代码里是 {step_key}，声明里是 {expect['key']}")
        self._current_idx = self._idx
        self._idx += 1
        return StepHandle(self, self._current_idx, expect["key"], expect["cn_name"])

    # ---- 工具 ----

    def log(self, msg: str) -> None:
        run_service.append_log(self.run_id, f"  {msg}")

    def touch(self) -> None:
        """刷新心跳（长步骤里也调一下，界面就知道执行器还活着）"""
        worker.touch()

    def check_cancel(self) -> None:
        if self._cancel.is_set():
            raise Canceled("已取消")

    def begin_step_capture(self) -> None:
        """每进入一步就清空"本步截图"记录（截图归属当前这一步）"""
        self.last_step_shot = None

    @property
    def run_dir(self):
        if self._run_dir is None:
            from core.config import RUNS_DIR
            self._run_dir = RUNS_DIR / str(self.run_id)
            self._run_dir.mkdir(parents=True, exist_ok=True)
        return self._run_dir

    def snap(self, name: str) -> str | None:
        """截图并存进本次运行的产物目录，返回文件名（数据库只存文件名，前端按 run_id + 文件名取图）"""
        filename = f"{self._current_idx}_{name}.png"
        try:
            self.page.screenshot(path=str(self.run_dir / filename))
            self.last_step_shot = filename
            return filename
        except Exception as e:
            self.log(f"截图失败：{e}")
            return None

    def dump_html(self, name: str) -> None:
        """把当前页面 HTML 存下来（失败排查用：截图看现象，HTML 看结构）"""
        try:
            (self.run_dir / f"{self._current_idx}_{name}.html").write_text(
                self.page.content(), encoding="utf-8")
        except Exception:
            pass


def run_job(unit, run_id: int, inputs: dict, cancel_event: threading.Event) -> None:
    """
    投递到浏览器队列的"任务体"：先保证浏览器可用，再执行单元
    浏览器起不来的话也必须给这次运行一个结论——否则记录停在"排队中"，
    界面上就是一个永远转圈的僵尸（用户关掉浏览器窗口后跑单元，就是这个场景）
    """
    try:
        page = worker.ensure_page()
    except Exception as e:
        run_service.append_log(run_id, f"浏览器启动失败：{e}")
        run_service.finish_run(run_id, "failed", error_msg=f"浏览器启动失败：{str(e)[:400]}")
        _cancel_events.pop(run_id, None)
        return
    execute(unit, run_id, inputs, page, cancel_event)


def execute(unit, run_id: int, inputs: dict, page, cancel_event: threading.Event) -> None:
    """跑一个单元（在浏览器线程里执行，由 api 层投递）；所有结果都写进运行记录，不向上抛异常"""
    ctx = UnitContext(run_id, unit, inputs, page, cancel_event)
    run_service.mark_running(run_id)
    try:
        unit.run(ctx)
    except Canceled:
        run_service.finish_run(run_id, "canceled")
    except Exception as e:
        step = ctx.failed_step if ctx.failed_step is not None else None
        run_service.finish_run(run_id, "failed", error_step=step,
                               error_msg=ctx.failed_msg or str(e)[:500])
    else:
        run_service.finish_run(run_id, "success")
    finally:
        _cancel_events.pop(run_id, None)
