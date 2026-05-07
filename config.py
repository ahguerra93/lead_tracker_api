"""Configuration - Database and application settings.

This file manages all configuration from environment variables.
Environment variables allow different settings per environment (dev, staging, prod).
"""
import os
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()


class DatabaseConfig:
    # If DATABASE_URL is set, it is used directly (recommended for Supabase).
    # Otherwise, individual DB_* variables are used to build the URL.
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_SSL_MODE = os.getenv("DB_SSL_MODE", "require")

    @classmethod
    def get_async_database_url(cls) -> str:
        """Return the async database URL.

        If DATABASE_URL is provided, swap the scheme to postgresql+asyncpg.
        Otherwise, build the URL from individual DB_* variables.
        """
        if cls.DATABASE_URL:
            # Replace postgres:// or postgresql:// with the asyncpg variant.
            url = cls.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url

        from sqlalchemy.engine.url import URL
        return str(
            URL.create(
                drivername="postgresql+asyncpg",
                username=cls.DB_USER,
                password=cls.DB_PASSWORD,
                host=cls.DB_HOST,
                port=int(cls.DB_PORT),
                database=cls.DB_NAME,
            )
        )


class WebhookConfig:
    # Set WHATSAPP_VERIFY_TOKEN in your .env file for production.
    VERIFY_TOKEN: str = os.getenv(
        "WHATSAPP_VERIFY_TOKEN", "my_super_duper_looper_secret_token_123"
    )
