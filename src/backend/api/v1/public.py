from fastapi import APIRouter

public_router = APIRouter()

@public_router.get("/trades/debug-alive", include_in_schema=False)
async def debug_alive():
    return {"status": "trades router is active"}

@public_router.get("/ping", include_in_schema=False)
async def ping():
    return {"pong": True}

__all__ = ["public_router"] 