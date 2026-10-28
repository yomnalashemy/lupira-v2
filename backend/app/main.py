from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models.db import init_db
from .routes import explain, health, npsle, predict


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from .services.classifier import load_model

    load_model()  # fail fast at startup if artifacts are missing/broken
    yield


app = FastAPI(title="Lupira API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(predict.router, prefix="/api")
app.include_router(explain.router, prefix="/api")
app.include_router(npsle.router, prefix="/api")
app.include_router(health.router, prefix="/api")
