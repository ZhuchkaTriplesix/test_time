"""Глобальная конфигурация и фикстуры для тестового набора pytest.

Назначение:
- Создание изолированного асинхронного движка базы данных (PostgreSQL / SQLite in-memory).
- Настройка транзакционных фикстур `db_session` и асинхронного HTTP-клиента `async_client` (`httpx.AsyncClient`).
- Регистрация кросс-диалектной поддержки типов PostgreSQL в SQLite.
"""

import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.compiler import compiles

from src.configuration.app import App
from src.database.dependencies import get_db
from src.database.models import Base


# Register SQLite compilations for PostgreSQL dialect types
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "VARCHAR(36)"


# Determine test database URL
TEST_DB_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
if not TEST_DB_URL or "localhost" in TEST_DB_URL or "db:5432" in TEST_DB_URL:
    TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(TEST_DB_URL, echo=False)

    if "sqlite" in TEST_DB_URL:
        # Enable SQLite foreign keys and custom percentile_cont if needed
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
        # Clean up database after each test
        await session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest_asyncio.fixture
async def async_client(test_engine: AsyncEngine) -> AsyncGenerator[AsyncClient, None]:
    app_instance = App().app
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    # Override get_db dependency to supply a clean session per request
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app_instance.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app_instance.dependency_overrides.clear()
