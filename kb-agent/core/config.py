# 配置模块 —— 从 .env 文件读取配置项
# .env 是放"密钥、地址"这类敏感/环境相关配置的标准做法
# 好处：key 不写死在代码里，换环境只改 .env 文件

import os
from dotenv import load_dotenv

# 加载项目根目录的 .env 文件，把里面的配置变成环境变量
load_dotenv()

# 用 os.getenv 读取，第二个参数是"没读到时的默认值"
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")

# Embedding（向量嵌入）配置 —— 用于语义检索
# 例：硅基流动 SiliconFlow 免费提供 bge-m3：
#   EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1  EMBEDDING_MODEL=BAAI/bge-m3
# 例：通义千问：
#   EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  EMBEDDING_MODEL=text-embedding-v3
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "")
