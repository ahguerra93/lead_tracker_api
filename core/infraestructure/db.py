from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import sys
from pathlib import Path

# Add the project root to the path so imports work correctly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import DatabaseConfig

# Import models so Base.metadata knows about all tables before create_all is called
from core.infraestructure.models.whatsapp_models import Contact, Conversation, Message, Media  # noqa: F401
from core.infraestructure.models.base import Base

_ssl_mode = DatabaseConfig.DB_SSL_MODE
_connect_args: dict = {"ssl": "require"} if _ssl_mode and _ssl_mode != "disable" else {}

# Use URL.create() so credentials with special characters (?, #, @, etc.) are
# handled correctly without manual URL-encoding.
_db_url = URL.create(
    drivername="postgresql+asyncpg",
    username=DatabaseConfig.DB_USER,
    password=DatabaseConfig.DB_PASSWORD,
    host=DatabaseConfig.DB_HOST,
    port=int(DatabaseConfig.DB_PORT),
    database=DatabaseConfig.DB_NAME,
)

engine = create_async_engine(
    _db_url,
    connect_args=_connect_args,
    echo=False,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_all_tables() -> None:
    """Create all tables defined in the ORM models if they don't exist yet.

    Called at application startup. Safe to call repeatedly — it is a no-op
    when the tables already exist.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
