"""manager 的进程管理层：各 Agent 服务的启动、停止、探活与自动重启

manager 是唯一手动启动的根进程，其它服务都是它的子进程——
它持有每个子进程的引用，所以只有它知道"谁在跑、谁死了"。
"""
import json
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import httpx
import psutil

ROOT = Path(__file__).resolve().parent.parent      # 项目根目录（manager/ 的上一级）
LOGS_DIR = Path(__file__).resolve().parent / "logs"


def resolve_python(cwd: Path) -> str:
    """{python} 占位符 → 各服务自己的 venv 解释器；跨平台差异只在这里做适配"""
    if sys.platform == "win32":
        return str(cwd / ".venv" / "Scripts" / "python.exe")
    return str(cwd / ".venv" / "bin" / "python")


class ProcessManager:
    def __init__(self, config_path: Path | None = None):
        config_path = config_path or (Path(__file__).resolve().parent / "services.json")
        config = json.loads(config_path.read_text(encoding="utf-8"))

        self.probe_interval = config.get("probe_interval", 5)
        self.probe_timeout = config.get("probe_timeout", 2)
        self.startup_timeout = config.get("startup_timeout", 30)
        self.max_restarts = config.get("max_restarts", 5)

        LOGS_DIR.mkdir(exist_ok=True)
        self.services = {}
        for item in config["services"]:
            self.services[item["name"]] = {
                "config": item,
                "proc": None,               # subprocess 进程对象
                "status": "stopped",        # stopped / starting / running / error
                "managed": False,           # True=期望运行；手动 stop 后为 False，监控不拉起
                "started_at": None,
                "restarts": 0,              # 累计自动重启次数
                "consecutive_failures": 0,  # 连续失败计数，超过上限放弃自动重启
                "stable_probes": 0,         # 连续探活成功次数（连续 2 轮才清零失败计数）
            }

        self._stop_event = threading.Event()
        self._monitor_thread = None

    # ---------- 对外操作（API 层调用） ----------

    def start(self, name: str) -> dict:
        svc = self.services[name]
        if self._alive(svc):
            return self._status_of(name)
        svc["managed"] = True
        return self._spawn(name)

    def stop(self, name: str) -> dict:
        svc = self.services[name]
        svc["managed"] = False          # 用户手动停 → 监控不再自动拉起
        self._kill_tree(svc)
        svc["status"] = "stopped"
        svc["stable_probes"] = 0
        return self._status_of(name)

    def restart(self, name: str) -> dict:
        self.stop(name)
        return self.start(name)

    def start_all(self) -> list[dict]:
        for name, svc in self.services.items():
            if svc["config"].get("auto_start") and not self._alive(svc):
                svc["managed"] = True
                self._spawn(name)
        return self.status_all()

    def stop_all(self) -> list[dict]:
        for svc in self.services.values():
            svc["managed"] = False
            self._kill_tree(svc)
            svc["status"] = "stopped"
            svc["stable_probes"] = 0
        return self.status_all()

    def status_all(self) -> list[dict]:
        return [self._status_of(name) for name in self.services]

    def logs(self, name: str, lines: int = 100) -> dict:
        path = LOGS_DIR / f"{name}.log"
        if not path.exists():
            return {"lines": [], "total": 0}
        content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return {"lines": content[-lines:], "total": len(content)}

    # ---------- 监控 ----------

    def start_monitor(self):
        # 开启线程，让它自己在后台跑，不占用服务接口
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def shutdown(self):
        # 关闭线程
        self._stop_event.set()
        self.stop_all()

    def _monitor_loop(self):
        # 每五秒嗅探线程状态，并将状态JSON返回
        while not self._stop_event.is_set():
            time.sleep(self.probe_interval)
            for name, svc in self.services.items():
                if not svc["managed"] or svc["status"] == "starting":
                    continue
                if self._probe(name):
                    # 连续 2 轮探活成功才清零失败计数，防止"起来又立刻死"的崩溃循环
                    svc["stable_probes"] += 1
                    if svc["stable_probes"] >= 2:
                        svc["consecutive_failures"] = 0
                    svc["status"] = "running"
                    continue
                # 探活失败 = 进程死了 → 自动重启；连续失败超上限则放弃，转 error 等人工处理
                svc["stable_probes"] = 0
                svc["consecutive_failures"] += 1
                if svc["consecutive_failures"] > self.max_restarts:
                    svc["status"] = "error"
                    continue
                svc["restarts"] += 1
                svc["status"] = "starting"
                self._spawn(name)

    # ---------- 内部工具 ----------

    def _spawn(self, name: str) -> dict:
        # 清理旧进程、生成进程、关闭父句柄（防止漏洞出现）、进入进程观察
        svc = self.services[name]
        self._kill_tree(svc)              # 先清残留进程，避免端口占用
        cfg = svc["config"]
        cwd = ROOT / cfg["cwd"]
        command = cfg["command"].replace("{python}", resolve_python(cwd))

        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        log_file = open(LOGS_DIR / f"{name}.log", "a", encoding="utf-8")
        proc = subprocess.Popen(
            command.split(), cwd=cwd,
            stdout=log_file, stderr=subprocess.STDOUT, **kwargs,
        )
        log_file.close()                  # 子进程持有自己的句柄，父进程这头可以关掉

        svc["proc"] = proc
        svc["started_at"] = datetime.now()
        svc["status"] = "starting"

        if self._wait_ready(name, self.startup_timeout):
            svc["status"] = "running"
            svc["stable_probes"] = 1
        else:
            svc["status"] = "error"       # 起不来（端口占用/启动报错），看日志
        return self._status_of(name)

    def _wait_ready(self, name: str, timeout: int) -> bool:
        # 等待观察，持续检测服务是否启动成功，并发出返回值；超时，则失败
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._probe(name):
                return True
            time.sleep(1)
        return False

    def _probe(self, name: str) -> bool:
        # 嗅探探针，通过发起请求，判断是否服务返回响应，来判断服务是否存活
        port = self.services[name]["config"]["port"]
        try:
            resp = httpx.get(f"http://127.0.0.1:{port}/docs", timeout=self.probe_timeout)
            return resp.status_code < 500    # 只要服务有响应就算活着
        except httpx.HTTPError:
            return False

    def _kill_tree(self, svc: dict):
        # 递归清理进程，从子进程开始，最后杀父进程
        proc = svc["proc"]
        svc["proc"] = None
        if proc is None or proc.poll() is not None:
            return
        try:
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
            parent.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            pass

    def _alive(self, svc: dict) -> bool:
        # 通过 poll 方法判断进行是否还存在（通过能不能返回内容判断）
        return svc["proc"] is not None and svc["proc"].poll() is None

    def _status_of(self, name: str) -> dict:
        # 将服务的状态转换为JSON格式返回
        svc = self.services[name]
        item = {
            "name": name,
            "port": svc["config"]["port"],
            "status": svc["status"],
            "auto_start": svc["config"].get("auto_start", False),
            "restarts": svc["restarts"],
        }
        if self._alive(svc) and svc["started_at"]:
            item["pid"] = svc["proc"].pid
            item["uptime_seconds"] = int((datetime.now() - svc["started_at"]).total_seconds())
        return item
