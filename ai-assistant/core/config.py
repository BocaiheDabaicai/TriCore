# 配置模块 —— 和 kb-agent 同一个套路：从 .env 读配置
# key 不写死在代码里，换环境只改 .env 文件

import os
from dotenv import load_dotenv

# 把环境变量的值读出来
load_dotenv()

# LLM 配置（DeepSeek，OpenAI 兼容接口）
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")

# kb-agent 服务地址 —— 调度器通过 HTTP 调用它
KB_AGENT_URL = os.getenv("KB_AGENT_URL", "http://localhost:8000")
