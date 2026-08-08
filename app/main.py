from fastapi import FastAPI

from app.routers.calls import router as calls_router


app = FastAPI(
    title="XLOGIX Call Trace Explorer",
    version="1.0.0",
)


app.include_router(calls_router)


@app.get("/health")
def health():
    return {
        "status": "ok"
    }