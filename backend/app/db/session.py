from collections.abc import Iterator
from functools import lru_cache
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings


@lru_cache
def get_engine():
    settings = get_settings()
    return create_engine(settings.database_url, **build_engine_kwargs(settings))


def build_engine_kwargs(settings: Settings, database_url: str | None = None) -> dict:
    url = database_url or settings.database_url
    connect_args: dict[str, object] = {
        "connect_timeout": settings.db_connect_timeout_seconds,
    }

    if settings.db_statement_timeout_ms > 0:
        connect_args["options"] = f"-c statement_timeout={settings.db_statement_timeout_ms}"

    kwargs: dict[str, object] = {"connect_args": connect_args}

    if should_use_transaction_pooler(settings, url):
        kwargs["poolclass"] = NullPool
        connect_args["prepare_threshold"] = None
    else:
        kwargs["pool_pre_ping"] = True

    return kwargs


def should_use_transaction_pooler(settings: Settings, database_url: str | None = None) -> bool:
    url = database_url or settings.database_url
    parsed = urlparse(url)
    return settings.db_pool_mode == "transaction" or parsed.port == 6543


@lru_cache
def get_session_factory():
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def get_db_session() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def reset_database_state() -> None:
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    get_settings.cache_clear()
