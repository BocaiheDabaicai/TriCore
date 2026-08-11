from fastapi import APIRouter

router = APIRouter(prefix="/bibilabu", tags=["我要我的滋味"])


@router.get("/v1")
async def bibilabu():
    return {
        "data": "bibilabu"
    }
