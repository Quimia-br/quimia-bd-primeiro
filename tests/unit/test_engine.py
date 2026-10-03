from pathlib import Path

import pytest

from seed.config import ConfigError, Target, load_settings
from seed.db.engine import build_url, connect_args, create_db_engine
from tests.conftest import FAKE_MIGRATION_PASSWORD, FAKE_PASSWORD

pytestmark = pytest.mark.usefixtures("seed_env")


def test_seed_url(ca_file: Path) -> None:
    url = build_url(load_settings(Target.TEST))

    assert url.drivername == "postgresql+psycopg"
    assert url.username == "avnadmin"
    assert url.port == 15432
    assert url.database == "defaultdb"
    assert url.query == {"sslmode": "verify-ca", "sslrootcert": str(ca_file)}


def test_url_hides_password_when_rendered() -> None:
    url = build_url(load_settings(Target.TEST))

    assert url.password == FAKE_PASSWORD
    assert FAKE_PASSWORD not in str(url)
    assert FAKE_PASSWORD not in repr(url)
    assert FAKE_PASSWORD not in url.render_as_string(hide_password=True)


def test_migration_url_uses_migration_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEED_MIGRATION_DB_USER", "usuario_migracao")
    monkeypatch.setenv("SEED_MIGRATION_DB_PASSWORD", FAKE_MIGRATION_PASSWORD)

    url = build_url(load_settings(Target.TEST), role="migration")

    assert url.username == "usuario_migracao"
    assert url.password == FAKE_MIGRATION_PASSWORD


def test_migration_url_falls_back_to_seed_credentials() -> None:
    url = build_url(load_settings(Target.TEST), role="migration")

    assert url.username == "avnadmin"
    assert url.password == FAKE_PASSWORD


def test_connect_args() -> None:
    args = connect_args(load_settings(Target.TEST))

    assert args == {
        "application_name": "quimia-seed",
        "connect_timeout": 10,
        "options": "-c search_path=public",
    }


def test_engine_uses_small_pool_without_connecting() -> None:
    engine = create_db_engine(load_settings(Target.TEST))
    try:
        assert engine.pool.size() == 2  # type: ignore[attr-defined]
        assert engine.pool.checkedout() == 0  # type: ignore[attr-defined]
    finally:
        engine.dispose()


def test_engine_requires_ca_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SEED_DB_SSLROOTCERT", str(tmp_path / "certs" / "nao-existe.pem"))

    with pytest.raises(ConfigError, match="Arquivo do CA não encontrado"):
        create_db_engine(load_settings(Target.TEST))
