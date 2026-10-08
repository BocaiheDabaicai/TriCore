# 浏览器执行器 —— 整个服务里唯一碰 Playwright 的地方
#
# 两条设计理由（这是本服务最重要的结构决定）：
# 1. **Playwright 的同步 API 锁死在一条专用线程里**。同步 API 会阻塞调用它的线程，
#    如果直接在 FastAPI 路由里调用，就会冻住事件循环——kb-agent 踩过这个坑
#    （上传接口冻住事件循环 → manager 探活 2 秒超时 → 判定服务死亡并反复重启）。
#    把 Playwright 关进一条线程后，"冻住事件循环"这个 bug 机械上就写不出来了。
# 2. **所有任务走同一条队列，串行执行**。浏览器同一时刻只能被一个操作驱动
#    （两个任务抢同一个页面必然互相踩），串行由队列天然保证，不需要另外加锁。
#
# 别的线程只能通过 submit() 投递任务，不能直接碰 Playwright 对象。

import json
import os
import queue
import subprocess
import threading
import time

from core.config import BROWSER_CHANNEL, PAGE_TIMEOUT_MS, PROFILE_DIR


class BrowserBusy(Exception):
    """浏览器正在执行别的任务（一次只干一件事）"""


class ProfileLocked(Exception):
    """浏览器用户目录被占用：多半是上次的浏览器进程没退干净"""


class BrowserWorker:
    def __init__(self):
        self._q: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._pw = None            # Playwright 驱动对象
        self._context = None       # 持久化浏览器上下文（登录态存在它的 user_data_dir 里）
        self._page = None          # 我们驱动的那个页面

        # 状态快照：worker 线程写、其它线程读，用锁保护
        self._state_lock = threading.Lock()
        self._state = {
            "launched": False,        # 浏览器是否已经开着
            "busy": False,            # 是否有任务在执行
            "current_job": "",        # 当前任务名（给界面显示）
            "heartbeat": 0.0,         # 最后一次"活着"的时间戳（长任务里每步刷新）
            "last_error": "",
            "profile_locked": False,
        }

    # ---------------- 状态（任何线程可读，只读快照） ----------------

    def status(self) -> dict:
        with self._state_lock:
            st = dict(self._state)
        st["queued"] = self._q.qsize()
        st["heartbeat_ago"] = round(time.time() - st["heartbeat"], 1) if st["heartbeat"] else None
        st["profile_dir"] = str(PROFILE_DIR)
        return st

    def _set(self, **kw) -> None:
        with self._state_lock:
            self._state.update(kw)

    def touch(self) -> None:
        """刷新心跳 —— 长任务里每走一步都调一次，界面据此判断"执行器是不是卡住了\""""
        self._set(heartbeat=time.time())

    # ---------------- 任务投递 ----------------

    def _ensure_thread(self) -> None:
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._loop, name="browser-worker", daemon=True)
            self._thread.start()

    def _loop(self) -> None:
        """worker 线程主循环：取一个任务、跑完、再取下一个"""
        while True:
            job = self._q.get()
            if job is None:
                break
            self._set(busy=True)
            self.touch()
            try:
                job()
            except Exception as e:   # 任务自己该处理的异常都处理了，这里是兜底，别让线程死掉
                # flush=True 很重要：进程输出被重定向到文件时是块缓冲的，不 flush 日志会"迟到"
                print(f"警告：浏览器任务未捕获异常：{e}", flush=True)
            finally:
                self.touch()
                self._set(busy=False, current_job="")

    def submit(self, name: str, job, wait: bool = True, timeout: float = 180.0):
        """
        投递一个任务（job 是零参可调用对象，会在 worker 线程里执行）
        - 队列非空或正在执行 → 抛 BrowserBusy，调用方返回 409，不排队
          （不排队的理由：RPA 操作有前后依赖，悄悄排队会让用户以为没点上）
        - wait=True 等任务结束才返回（打开/关闭浏览器用），异常会抛回调用方
        - wait=False 立即返回（跑单元用，进度靠轮询数据库）
        """
        with self._state_lock:
            if self._state["busy"] or not self._q.empty():
                raise BrowserBusy(f"浏览器正忙：{self._state['current_job'] or '有其他任务在队列里'}")
            self._state["current_job"] = name

        done = threading.Event()
        box: dict = {}

        def wrapper():
            try:
                job()
            except Exception as e:
                box["error"] = e
            finally:
                done.set()

        self._ensure_thread()
        self._q.put(wrapper)

        if not wait:
            return None
        if not done.wait(timeout):
            raise TimeoutError(f"任务超时（{timeout:.0f} 秒）：{name}")
        if "error" in box:
            raise box["error"]
        return None

    # ---------------- 浏览器本体（下面这些只能在 worker 线程里调用） ----------------

    def _launch(self):
        """启动持久化浏览器上下文（登录态存在 PROFILE_DIR 里，跨服务重启保留）"""
        try:
            return self._pw.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,                    # 有界面：验证码要人工过、执行过程要能盯着
                channel=BROWSER_CHANNEL or None,   # msedge = 用系统装的 Edge，免下载
                viewport={"width": 1440, "height": 900},
            )
        except Exception as e:
            self._set(last_error=str(e))
            raise

    def _find_profile_pids(self) -> list[int]:
        """
        找出命令行里带本服务 profile 目录的浏览器进程（只认自己的目录，不碰用户日常开的浏览器）
        匹配放在 Python 里做：路径有反斜杠/正斜杠两种写法，交给 PowerShell 的 -like 会漏掉
        （踩过：手工用正斜杠启动的浏览器匹配不上，杀不干净）
        """
        if os.name != "nt":
            return []
        ps = ("Get-CimInstance Win32_Process -Filter \"Name='msedge.exe' or Name='chrome.exe'\" | "
              "Select-Object ProcessId, CommandLine | ConvertTo-Json -Compress")
        try:
            out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                                 capture_output=True, text=True, timeout=30).stdout
            data = json.loads(out) if out.strip() else []
        except Exception as e:
            print(f"提示：查询浏览器进程失败：{e}", flush=True)
            return []
        if isinstance(data, dict):      # 只有一个进程时 ConvertTo-Json 返回对象而不是数组
            data = [data]

        needle = str(PROFILE_DIR).replace("\\", "/").lower()
        pids = []
        for item in data:
            cmd = (item.get("CommandLine") or "").replace("\\", "/").lower()
            if needle in cmd:
                pids.append(int(item["ProcessId"]))
        return pids

    def _kill_profile_processes(self, wait_seconds: float = 12.0) -> list[int]:
        """
        反复清理，直到没有残留进程（或超时）
        为什么不能杀一遍就走：主进程被杀后子进程还会零星存活几秒，
        这时启动浏览器会"发现已有实例"而立刻退出，报一个很难看懂的错
        """
        killed: list[int] = []
        deadline = time.time() + wait_seconds
        while True:
            pids = self._find_profile_pids()
            if not pids:
                break
            for pid in pids:
                if pid not in killed:
                    killed.append(pid)
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=15)
            if time.time() > deadline:
                break
            time.sleep(0.7)
        return killed

    def context_alive(self) -> bool:
        """浏览器还活着吗（进程在、连接没断）"""
        if self._context is None:
            return False
        try:
            browser = self._context.browser
            return bool(browser and browser.is_connected())
        except Exception:
            return False

    def ensure_page(self):
        """
        确保浏览器已启动、且有一个可用的页面：
        - 还没启动 → 启动（headful，用户能看见、能人工登录）
        - 浏览器被外部关掉/崩了 → 丢掉旧引用重新启动（人是会随手关窗口的，不能当没看见）
        - 页面被单独关掉 → 复用上下文里的页面或新开一个
        只能在 worker 线程里调用（Playwright 对象有线程归属）
        """
        if self._pw is None:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()

        # 外部把浏览器关了：旧 context 已经失效，必须整块重来，否则后面每一步都会报
        # "Target page, context or browser has been closed"
        if self._context is not None and not self.context_alive():
            print("提示：浏览器已被关闭（或崩溃），重新启动", flush=True)
            self._context = None
            self._page = None
            self._set(launched=False)

        if self._context is None:
            try:
                self._context = self._launch()
            except Exception as first:
                # 启动失败的头号原因是"上次的浏览器没退干净，占着用户目录"
                # （表现常常是 Edge 发现已有实例后立刻退出 → Playwright 报 browser has been closed）。
                # 清理一遍再试，把"卡住要人来救"变成"自己就恢复了"
                print(f"提示：浏览器启动失败，清理残留进程后重试一次（{str(first)[:100]}）", flush=True)
                self._kill_profile_processes()
                try:
                    self._context = self._launch()
                except Exception as second:
                    self._set(profile_locked=True, last_error=str(second))
                    raise ProfileLocked(
                        "浏览器启动失败：多半是上次的浏览器没退干净、占着用户目录；"
                        "已自动清理重试仍未成功，可点「强制结束残留进程」后再试"
                    ) from second

        if self._page is None or self._page.is_closed():
            pages = [p for p in self._context.pages if not p.is_closed()]
            self._page = pages[0] if pages else self._context.new_page()
            self._page.set_default_timeout(PAGE_TIMEOUT_MS)

        self._set(launched=True, profile_locked=False)
        return self._page

    def open(self, url: str = "") -> dict:
        """打开浏览器（可选顺带打开某个网址）——人工登录就是在这里做的"""

        def job():
            page = self.ensure_page()
            if url:
                page.goto(url, wait_until="domcontentloaded")
            page.bring_to_front()
            self._set(last_error="", profile_locked=False)

        self.submit("打开浏览器", job, wait=True, timeout=120.0)
        return self.status()

    def _teardown(self) -> None:
        """
        收拾 Playwright 这一侧的连接（必须在 worker 线程里跑）
        注意要真的调 stop() 停掉驱动进程：只把引用置空的话，驱动会一直挂着，
        下次再 start() 会在同一线程里起第二个驱动，出各种说不清的怪问题
        """
        try:
            if self._context is not None:
                self._context.close()
        except Exception as e:
            print(f"提示：关闭浏览器上下文时出错（忽略）：{e}", flush=True)
        try:
            if self._pw is not None:
                self._pw.stop()
        except Exception as e:
            print(f"提示：停止 Playwright 驱动时出错（忽略）：{e}", flush=True)
        self._context = None
        self._pw = None
        self._page = None
        self._set(launched=False)

    def close(self) -> dict:
        """关掉浏览器（登录态已在 profile 目录里落盘，下次打开还在）"""
        self.submit("关闭浏览器", self._teardown, wait=True, timeout=120.0)
        return self.status()

    def kill_orphans(self) -> dict:
        """
        强制结束占用本服务 profile 目录的残留浏览器进程
        为什么需要它：服务被 manager 重启（或崩溃）时，浏览器子进程不会自动退出，
        它死抓着 profile 目录，下次启动浏览器会直接失败——这是这类工具的头号运维坑
        注意：不等队列，就是用来救"卡住了"的场面的，所以正在执行任务时拒绝
        """
        with self._state_lock:
            if self._state["busy"]:
                raise BrowserBusy("有任务正在执行，不能强制结束浏览器")

        if os.name != "nt":
            raise RuntimeError("目前只实现了 Windows 下的残留进程清理")

        # 先把 Playwright 侧的连接干净地收掉（借着当前空闲的 worker 线程），再动进程
        # 收不掉也无所谓（可能浏览器已经崩了），所以异常一律忽略，下面照样杀进程
        try:
            self.submit("清理浏览器连接", self._teardown, wait=True, timeout=60.0)
        except Exception:
            pass

        try:
            killed = self._kill_profile_processes()
        except Exception as e:
            raise RuntimeError(f"清理残留进程失败：{e}") from e

        self._set(profile_locked=False)
        return {"killed": killed, **self.status()}


# 全局单例：服务里所有人共用同一个浏览器
worker = BrowserWorker()
