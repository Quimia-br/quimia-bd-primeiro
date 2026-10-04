"""Constantes e fixtures compartilhadas.

O isolamento do ambiente (sem ``SEED_*`` reais, pasta temporária) fica em
``tests/unit/conftest.py``. Os testes de integração usam o ``.env.test`` real.
"""

from pathlib import Path
from typing import Final

import pytest

PROJECT_ROOT: Final = Path(__file__).resolve().parents[1]
SQL_DIR: Final = PROJECT_ROOT / "sql"

FAKE_HOST = "pg-ficticio.example.com"
FAKE_PASSWORD = "senha-ficticia-123"


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
