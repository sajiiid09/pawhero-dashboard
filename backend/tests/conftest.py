from __future__ import annotations

import os
from collections.abc import Iterator
from uuid import uuid4

import psycopg
import pytest
from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command
from app.db.seed import seed_demo_data
from app.db.session import reset_database_state
from app.main import app
from app.services.auth import create_access_token

DEMO_OWNER_ID = "owner-demo"


@pytest.fixture(scope="session")
def test_database_url() -> Iterator[str]:
    database_name = f"pawhero_test_{uuid4().hex[:8]}"
    admin_dsn = "dbname=postgres"

    with psycopg.connect(admin_dsn, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE DATABASE "{database_name}"')

    database_url = f"postgresql+psycopg:///{database_name}"
    previous_database_url = os.environ.get("DATABASE_URL")
    previous_migration_database_url = os.environ.get("MIGRATION_DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    os.environ["MIGRATION_DATABASE_URL"] = database_url
    reset_database_state()

    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "head")
    seed_demo_data()

    try:
        yield database_url
    finally:
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url
        if previous_migration_database_url is None:
            os.environ.pop("MIGRATION_DATABASE_URL", None)
        else:
            os.environ["MIGRATION_DATABASE_URL"] = previous_migration_database_url
        reset_database_state()
        with psycopg.connect(admin_dsn, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s",
                    (database_name,),
                )
                cursor.execute(f'DROP DATABASE IF EXISTS "{database_name}"')


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    token = create_access_token(DEMO_OWNER_ID)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def client(test_database_url: str) -> Iterator[TestClient]:
    del test_database_url
    with TestClient(app) as api_client:
        yield api_client
