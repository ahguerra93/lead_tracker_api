from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.infrastructure.db import create_all_tables
from src.presentation.api.whatsapp import router as whatsapp_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(whatsapp_router)