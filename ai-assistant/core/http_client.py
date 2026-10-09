# 全局共享的 httpx.Client —— 调度器所有出站调用（registry / admin 代理）都走它
# 为什么不用 module-level 的 httpx.get/post/delete：
#   那种写法每次调用都新建一个客户端（含事件循环），Windows 上实测每次多花 ~1.3 秒
#   （复用同一个 Client 后每次只要毫秒级）——之前每个 kb 调用都白等一秒多，
#   管理端经代理的请求也受影响
# 连接池本身也是复用收益：同一台主机的请求不再每次重新握手

import httpx

# 默认超时 30 秒；各调用按需覆盖（探活 1s、问答 60s、起草 120s 等）
client = httpx.Client(timeout=30.0)
