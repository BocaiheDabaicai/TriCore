# 浏览器接口 —— 操作台用来打开/关闭浏览器、看状态
# 人工登录（输账号、过验证码）就是在「打开浏览器」之后、在这个真实窗口里做的

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.browser import BrowserBusy, ProfileLocked, worker
from core.config import BROWSER_CHANNEL, KINGDEE_URL, OA_URL

router = APIRouter(prefix="/api/v1/browser", tags=["浏览器"])


class OpenRequest(BaseModel):
    url: str = ""      # 不传就打开空白页（自己在窗口里输网址登录）


def status_payload() -> dict:
    st = worker.status()
    st["channel"] = BROWSER_CHANNEL or "chromium（自带）"
    st["kingdee_url"] = KINGDEE_URL
    st["oa_url"] = OA_URL
    return st


@router.get("")
def get_status():
    """浏览器当前状态（打开没有、忙不忙、心跳多久没动）"""
    return {"message": "ok", "data": status_payload()}


@router.post("/open")
def open_browser(req: OpenRequest):
    """
    打开浏览器（懒启动：服务启动时不拉浏览器，第一次点这里才拉）
    为什么懒启动：headful 浏览器冷启动要 1~3 秒，放服务启动路径会拖超 manager 的 30 秒启动窗口
    """
    try:
        worker.open(req.url or "")
    except BrowserBusy as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ProfileLocked as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"打开浏览器失败：{e}")
    return {"message": "浏览器已打开", "data": status_payload()}


@router.post("/close")
def close_browser():
    """关闭浏览器（登录态已经存在 profile 目录里，下次打开还在）"""
    try:
        worker.close()
    except BrowserBusy as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"关闭浏览器失败：{e}")
    return {"message": "浏览器已关闭", "data": status_payload()}


@router.post("/kill-orphans")
def kill_orphans():
    """
    强制结束残留的浏览器进程（服务被重启后，上次的浏览器可能还占着 profile 目录）
    这是运维救急按钮：正常情况用不到，遇到了它比手动去任务管理器里翻要快
    """
    try:
        result = worker.kill_orphans()
    except BrowserBusy as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    killed = result.get("killed", [])
    return {"message": f"已结束 {len(killed)} 个残留浏览器进程", "data": status_payload()}
