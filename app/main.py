from fastapi import FastAPI

from app.core.config import config
from app.db import create_db_and_tables
from app.routes.auth import router as auth_router

app = FastAPI(title=config.NAME)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
