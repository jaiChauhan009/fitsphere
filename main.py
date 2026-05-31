from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from database import engine, Base
from config import settings
from routers import users, food, nutrition, workouts, progress, ai, knowledge
from sqlalchemy import text
import time


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"[startup] DB init warning: {e}")
    yield
    await engine.dispose()


app = FastAPI(
    title="FitSphere API",
    version="1.0.0",
    description="Complete fitness ecosystem — nutrition, workouts, AI recommendations",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(food.router)
app.include_router(nutrition.router)
app.include_router(workouts.router)
app.include_router(progress.router)
app.include_router(ai.router)
app.include_router(knowledge.router)


@app.get("/")
def root():
    return {"app": "FitSphere API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health():
    """Health check used by Render. Verifies API + DB connectivity."""
    start = time.monotonic()
    db_ok = False
    db_error = None
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_error = str(e)

    latency_ms = round((time.monotonic() - start) * 1000, 1)
    payload = {
        "status": "ok" if db_ok else "degraded",
        "api": "ok",
        "database": "ok" if db_ok else f"error: {db_error}",
        "latency_ms": latency_ms,
        "version": "1.0.0",
    }
    status_code = 200 if db_ok else 503
    return JSONResponse(content=payload, status_code=status_code)
