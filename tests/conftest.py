"""Fixtures compartilhadas.

Todo teste roda isolado: sem variáveis ``SEED_*`` do ambiente real, numa pasta
temporária (então nunca lê o ``.env.test`` nem o ``.env`` do projeto) e com o
cache de ``get_settings`` limpo.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from seed.config import get_settings

FAKE_HOST = "pg-ficticio.example.com"
FAKE_PASSWORD = "senha-ficticia-123"
FAKE_MIGRATION_PASSWORD = "senha-migracao-ficticia"


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    for name in list(os.environ):
        if name.upper().startswith("SEED_"):
            monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def ca_file(tmp_path: Path) -> Path:
    path = tmp_path / "certs" / "ca-test.pem"
    path.parent.mkdir()
    path.write_text("certificado fictício", encoding="utf-8")
    return path


@pytest.fixture
def seed_env(monkeypatch: pytest.MonkeyPatch, ca_file: Path) -> dict[str, str]:
    """Variáveis mínimas válidas, todas fictícias."""
    values = {
        "SEED_DB_HOST": FAKE_HOST,
        "SEED_DB_PORT": "15432",
        "SEED_DB_USER": "avnadmin",
        "SEED_DB_PASSWORD": FAKE_PASSWORD,
        "SEED_DB_NAME": "defaultdb",
        "SEED_DB_SSLROOTCERT": str(ca_file),
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    return values
