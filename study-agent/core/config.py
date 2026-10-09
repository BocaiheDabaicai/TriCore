# 配置模块 —— 从 .env 文件读取配置项（照 kb-agent 的模式）
# .env 放"密钥、地址"这类敏感/环境相关配置：不写死在代码里，换环境只改 .env

import os
from dotenv import load_dotenv

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")
