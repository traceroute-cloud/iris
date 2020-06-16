"""API Entrypoint."""

from diamond_miner.api import router, __version__
from diamond_miner.commons.redis import Redis

from fastapi import FastAPI

app = FastAPI(
    title="Diamond-Miner", description="Diamond-Miner API", version=__version__,
)
app.include_router(router, prefix="/v0")


@app.on_event("startup")
async def startup_event():
    app.redis = Redis("controller")
    await app.redis.connect("redis://redis")


@app.on_event("shutdown")
async def shutdown_event():
    try:
        await app.redis.close()
    except Exception:
        pass
