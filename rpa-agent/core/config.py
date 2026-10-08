# 配置模块 —— 从 .env 读取配置（和 kb-agent 同一套做法）
# .env 放"网址、开关"这类环境相关的东西，不写死在代码里，换环境只改 .env

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# 项目根目录（本文件在 rpa-agent/core/ 下，往上一层就是 rpa-agent/）
ROOT = Path(__file__).resolve().parent.parent

# 要操作的外部系统地址（不配也能跑：打开浏览器时先落在空白页，人工登录时自己输网址）
KINGDEE_URL = os.getenv("KINGDEE_URL", "")
OA_URL = os.getenv("OA_URL", "")

# 用哪个浏览器：msedge / chrome 用系统已装的（免下载）；留空则用 Playwright 自带的 chromium
# 为什么默认系统 Edge：Playwright 自带 chromium 要额外下载一百多 MB，而本机本来就有 Edge
BROWSER_CHANNEL = os.getenv("BROWSER_CHANNEL", "msedge")

# 页面操作的默认等待上限（毫秒）：等不到就报错并截图，而不是无限挂着
PAGE_TIMEOUT_MS = int(os.getenv("PAGE_TIMEOUT_MS", "15000"))

# 运行期数据目录（全部不进 git：浏览器 profile 含登录 cookie、截图含企业数据）
DATA_DIR = ROOT / "data"
PROFILE_DIR = DATA_DIR / "browser_profile"   # 登录态持久化在这里，服务重启不用重新登录
RUNS_DIR = DATA_DIR / "runs"                 # 每次运行的截图与产物：runs/{run_id}/
SHOTS_DIR = DATA_DIR / "shots"               # 操作台上传的页面截图（给人看、给 AI 识别用）
LOGS_DIR = ROOT / "logs"                     # 每次运行的逐步日志：logs/run_{id}.log
STATIC_DIR = ROOT / "static"                 # 演示单元用的本地页面

for _d in (DATA_DIR, PROFILE_DIR, RUNS_DIR, SHOTS_DIR, LOGS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
