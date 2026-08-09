from fastapi import FastAPI
from src.app.settings import settings

app = FastAPI(
    title="FastChat",
    version=settings.version
)