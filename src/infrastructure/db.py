"""Database engine and session factory.

This is the only place in the infrastructure layer that knows about
the database connection string and SQLAlchemy engine configuration.
"""
from sqlalchemy.engine.url import make_url
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
_safe_database_target = make_url(DatabaseConfig.get_async_database_url()).render_as_string(
    hide_password=True
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
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        raise RuntimeError(
            "Database startup failed for "
            f"{_safe_database_target}. Check the deployed DATABASE_URL/DB_* values. "
            "Supabase shared pooler URLs use the project ref in the username "
            "(postgres.<project-ref>), while direct or dedicated connections use "
            "the plain postgres username."
        ) from exc
