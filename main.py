from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CorsConfig
from src.infrastructure.db import create_all_tables
from src.presentation.api.whatsapp import router as whatsapp_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all_tables()
    yield


app = FastAPI(lifespan=lifespan)

if CorsConfig.ALLOW_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CorsConfig.ALLOW_ORIGINS,
        allow_credentials=CorsConfig.ALLOW_CREDENTIALS,
        allow_methods=CorsConfig.ALLOW_METHODS,
        allow_headers=CorsConfig.ALLOW_HEADERS,
    )

app.include_router(whatsapp_router)