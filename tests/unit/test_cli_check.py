from dataclasses import replace

import pytest
from sqlalchemy.exc import OperationalError
from typer.testing import CliRunner

from seed.cli import ExitCode, app, connection_hint
from seed.config import Settings
from seed.db import diagnostics
from seed.db.diagnostics import ServerInfo
from tests.conftest import FAKE_HOST, FAKE_PASSWORD

runner = CliRunner()

HEALTHY = ServerInfo(
    database="defaultdb",
    user="avnadmin",
    current_schema="public",
    server_version="17.6",
    max_connections=20,
    open_connections=3,
    database_size_bytes=8 * 1024 * 1024,
    timezone="UTC",
    alembic_revision="0001_baseline",
    missing_tables=(),
)


def _fake_fetch(info: ServerInfo, monkeypatch: pytest.MonkeyPatch) -> list[Settings]:
    calls: list[Settings] = []

    def fake(settings: Settings) -> ServerInfo:
        calls.append(settings)
        return info

    monkeypatch.setattr(diagnostics, "fetch_server_info", fake)
    return calls


@pytest.mark.usefixtures("seed_env")
def test_check_shows_diagnostic_without_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _fake_fetch(HEALTHY, monkeypatch)

    result = runner.invoke(app, ["check"])

    assert result.exit_code == ExitCode.OK
    assert calls[0].target == "test"
    assert "Banco de teste" in result.output
    assert "pg-***.example.com" in result.output
    assert "17.6" in result.output
    assert "3 abertas de 20" in result.output
    assert "8.0 MB" in result.output
    assert "todas as 13 presentes" in result.output
    assert "Aviso" not in result.output
    assert FAKE_HOST not in result.output
    assert FAKE_PASSWORD not in result.output


@pytest.mark.usefixtures("seed_env")
def test_check_main_shows_red_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _fake_fetch(HEALTHY, monkeypatch)

    result = runner.invoke(app, ["--target", "main", "check"])

    assert result.exit_code == ExitCode.OK
    assert calls[0].target == "main"
    assert "banco PRINCIPAL (main)" in result.output


@pytest.mark.usefixtures("seed_env")
def test_check_target_from_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _fake_fetch(HEALTHY, monkeypatch)
    monkeypatch.setenv("SEED_TARGET", "main")

    runner.invoke(app, ["check"])

    assert calls[0].target == "main"


@pytest.mark.usefixtures("seed_env")
def test_check_warns_on_timezone_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_fetch(replace(HEALTHY, timezone="America/Sao_Paulo"), monkeypatch)

    result = runner.invoke(app, ["check"])

    assert result.exit_code == ExitCode.OK
    assert "fuso do servidor (America/Sao_Paulo)" in result.output


@pytest.mark.usefixtures("seed_env")
def test_check_accepts_utc_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_fetch(replace(HEALTHY, timezone="Etc/UTC"), monkeypatch)

    result = runner.invoke(app, ["check"])

    assert "fuso do servidor" not in result.output


@pytest.mark.usefixtures("seed_env")
def test_check_warns_on_missing_tables_and_alembic(monkeypatch: pytest.MonkeyPatch) -> None:
    info = replace(HEALTHY, missing_tables=("admins", "usuarios"), alembic_revision=None)
    _fake_fetch(info, monkeypatch)

    result = runner.invoke(app, ["check"])

    assert "11 de 13 presentes" in result.output
    assert "admins, usuarios" in result.output
    assert "sem alembic_version" in result.output


@pytest.mark.usefixtures("seed_env")
def test_check_connection_failure_is_redacted(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing(settings: Settings) -> ServerInfo:
        cause = Exception(
            f'connection to server at "{FAKE_HOST}" (203.0.113.7), port 15432 failed: timeout'
        )
        raise OperationalError("SELECT 1", {}, cause)

    monkeypatch.setattr(diagnostics, "fetch_server_info", failing)

    result = runner.invoke(app, ["check"])

    assert result.exit_code == ExitCode.CONEXAO
    assert "Falha ao conectar" in result.output
    assert "allowlist" in result.output
    assert FAKE_HOST not in result.output
    assert "203.0.113.7" not in result.output


def test_check_without_configuration_exits_with_config_code() -> None:
    result = runner.invoke(app, ["check"])

    assert result.exit_code == ExitCode.CONFIGURACAO
    assert "SEED_DB_HOST" in result.output


def test_invalid_target_is_usage_error() -> None:
    result = runner.invoke(app, ["--target", "producao", "check"])

    assert result.exit_code == ExitCode.USO


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("certificate contains IP address with invalid length 16", "SEED_DB_SSLMODE"),
        ("SSL error: certificate verify failed", "SEED_DB_SSLROOTCERT"),
        ('password authentication failed for user "avnadmin"', "SEED_DB_PASSWORD"),
        ('database "outro" does not exist', "SEED_DB_NAME"),
        ('could not translate host name "x" to address', "SEED_DB_HOST"),
        ("timeout expired", "allowlist"),
    ],
)
def test_connection_hint(message: str, expected: str) -> None:
    assert expected in connection_hint(message)
