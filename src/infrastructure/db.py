"""Database engine and session factory.

This is the only place in the infrastructure layer that knows about
the database connection string and SQLAlchemy engine configuration.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import DatabaseConfig

# Import models so Base.metadata knows about all tables before create_all
from .models.whatsapp_models import Contact, Conversation, Media, Message  # noqa: F401
from .models.base import Base

_ssl_mode = DatabaseConfig.DB_SSL_MODE
_connect_args: dict = (
    {"ssl": "require"} if _ssl_mode and _ssl_mode != "disable" else {}
)

engine = create_async_engine(
    DatabaseConfig.get_async_database_url(),
    connect_args=_connect_args,
    echo=False,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_all_tables() -> None:
    """Create all ORM-mapped tables that don't yet exist.

    Called once at application startup. Safe to call repeatedly.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
