from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base
from config import settings
from routers import users, food, nutrition, workouts, progress, ai, knowledge


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (use Alembic for prod migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
def health():
    return {"status": "ok"}
