from pathlib import Path

import pytest

from seed.config import ConfigError, Target, get_settings, load_settings, mask_host, resolve_target
from tests.conftest import FAKE_HOST, FAKE_PASSWORD


def _write_env(directory: Path, target: Target, **values: str) -> None:
    lines = [f"SEED_{name.upper()}={value}" for name, value in values.items()]
    (directory / target.env_file_name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _complete_env(ca_file: Path, db_name: str, host: str = FAKE_HOST) -> dict[str, str]:
    return {
        "db_host": host,
        "db_port": "15432",
        "db_user": "avnadmin",
        "db_password": FAKE_PASSWORD,
        "db_name": db_name,
        "db_sslrootcert": str(ca_file),
    }


@pytest.mark.usefixtures("seed_env")
def test_defaults() -> None:
    settings = load_settings(Target.TEST)

    assert settings.target is Target.TEST
    assert settings.db_port == 15432
    assert settings.db_schema == "public"
    assert settings.db_sslmode == "verify-full"
    assert settings.db_pool_size == 2
    assert settings.db_max_overflow == 1
    assert settings.batch_size == 1000
    assert settings.timezone == "UTC"
    assert settings.migration_db_user is None


@pytest.mark.parametrize("target", list(Target))
def test_reads_env_file_of_target(tmp_path: Path, ca_file: Path, target: Target) -> None:
    _write_env(tmp_path, Target.TEST, **_complete_env(ca_file, "banco_test"))
    main_env = _complete_env(ca_file, "banco_main", host="pg-principal.example.com")
    _write_env(tmp_path, Target.MAIN, **main_env)

    settings = load_settings(target)

    assert settings.target is target
    assert settings.db_name == f"banco_{target.value}"


def test_real_env_var_overrides_file(
    tmp_path: Path, ca_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_env(tmp_path, Target.TEST, **_complete_env(ca_file, "do_arquivo"))
    monkeypatch.setenv("SEED_DB_NAME", "do_ambiente")

    assert load_settings(Target.TEST).db_name == "do_ambiente"


def test_seed_target_env_does_not_override_explicit_target(
    seed_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SEED_TARGET", "main")

    assert load_settings(Target.TEST).target is Target.TEST


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, Target.TEST), ("main", Target.MAIN), (" TEST ", Target.TEST)],
)
def test_resolve_target(raw: str | None, expected: Target, monkeypatch: pytest.MonkeyPatch) -> None:
    if raw is None:
        assert resolve_target() is expected
    else:
        monkeypatch.setenv("SEED_TARGET", raw)
        assert resolve_target() is expected


def test_resolve_target_invalid() -> None:
    with pytest.raises(ConfigError, match="Alvo inválido"):
        resolve_target("producao")


def test_missing_variables_are_listed_without_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEED_DB_PASSWORD", FAKE_PASSWORD)

    with pytest.raises(ConfigError) as info:
        load_settings(Target.TEST)

    message = str(info.value)
    assert ".env.test não encontrado" in message
    assert "SEED_DB_HOST: obrigatória e não definida" in message
    assert "SEED_DB_SSLROOTCERT" in message
    assert FAKE_PASSWORD not in message
    assert info.value.__cause__ is None


@pytest.mark.usefixtures("seed_env")
def test_invalid_value_message_hides_input(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEED_DB_PORT", "porta-secreta")

    with pytest.raises(ConfigError) as info:
        load_settings(Target.TEST)

    assert "SEED_DB_PORT" in str(info.value)
    assert "porta-secreta" not in str(info.value)


@pytest.mark.usefixtures("seed_env")
@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("SEED_DB_SSLMODE", "require"),
        ("SEED_DB_SSLMODE", "disable"),
        ("SEED_DB_SCHEMA", "public; drop table usuarios"),
        ("SEED_DB_SCHEMA", "Public"),
        ("SEED_TIMEZONE", "Brasil/Inventado"),
        ("SEED_DB_POOL_SIZE", "0"),
        ("SEED_BATCH_SIZE", "0"),
    ],
)
def test_rejects_invalid_values(monkeypatch: pytest.MonkeyPatch, variable: str, value: str) -> None:
    monkeypatch.setenv(variable, value)

    with pytest.raises(ConfigError, match=variable):
        load_settings(Target.TEST)


@pytest.mark.usefixtures("seed_env")
@pytest.mark.parametrize("target", list(Target))
def test_password_plain_accepted_in_both_targets(
    monkeypatch: pytest.MonkeyPatch, target: Target
) -> None:
    monkeypatch.setenv("SEED_PASSWORD_PLAIN", "senha-de-teste")

    settings = load_settings(target)

    assert settings.password_plain is not None
    assert "senha-de-teste" not in repr(settings)


@pytest.mark.usefixtures("seed_env")
def test_migration_credentials_must_come_together(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEED_MIGRATION_DB_USER", "usuario_migracao")

    with pytest.raises(ConfigError, match="juntas"):
        load_settings(Target.TEST)


@pytest.mark.usefixtures("seed_env")
def test_secrets_do_not_leak_in_repr() -> None:
    settings = load_settings(Target.TEST)

    assert FAKE_PASSWORD not in repr(settings)
    assert FAKE_PASSWORD not in str(settings)


@pytest.mark.usefixtures("seed_env")
def test_redact_removes_host_ip_and_password() -> None:
    settings = load_settings(Target.TEST)
    message = (
        f'connection to server at "{FAKE_HOST}" (203.0.113.7), port 15432 failed: '
        f"password {FAKE_PASSWORD} rejected"
    )

    redacted = settings.redact(message)

    assert FAKE_HOST not in redacted
    assert "203.0.113.7" not in redacted
    assert FAKE_PASSWORD not in redacted
    assert "pg-***.example.com" in redacted


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("pg-quimia-test-proj.aivencloud.com", "pg-***.aivencloud.com"),
        ("localhost", "loc***"),
        ("db.example", "db***"),
        ("203.0.113.7", "***"),
        ("::1", "***"),
    ],
)
def test_mask_host(host: str, expected: str) -> None:
    assert mask_host(host) == expected


@pytest.mark.usefixtures("seed_env")
def test_get_settings_is_cached() -> None:
    assert get_settings(Target.TEST) is get_settings(Target.TEST)
    get_settings.cache_clear()
    assert get_settings(Target.TEST).db_name == "defaultdb"


def test_main_target_reads_plain_env_file() -> None:
    assert Target.MAIN.env_file_name == ".env"
    assert Target.TEST.env_file_name == ".env.test"


@pytest.mark.usefixtures("seed_env")
def test_test_target_aborts_when_pointing_to_main_server(tmp_path: Path) -> None:
    # Simula o .env do principal com o mesmo servidor que o ambiente resolveu para test.
    (tmp_path / ".env").write_text(
        f"SEED_DB_HOST={FAKE_HOST.upper()}\nSEED_DB_PORT=15432\n", encoding="utf-8"
    )

    with pytest.raises(ConfigError, match="mesmo servidor do banco principal") as info:
        load_settings(Target.TEST)

    assert FAKE_HOST not in str(info.value)


@pytest.mark.usefixtures("seed_env")
@pytest.mark.parametrize(
    "main_env",
    [
        "SEED_DB_HOST=pg-principal.example.com\nSEED_DB_PORT=15432\n",
        f"SEED_DB_HOST={FAKE_HOST}\nSEED_DB_PORT=25432\n",
        "OUTRA_VARIAVEL=1\n",
    ],
)
def test_test_target_allows_different_main_server(tmp_path: Path, main_env: str) -> None:
    (tmp_path / ".env").write_text(main_env, encoding="utf-8")

    assert load_settings(Target.TEST).target is Target.TEST


@pytest.mark.usefixtures("seed_env")
def test_main_target_is_not_blocked_by_guard(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(f"SEED_DB_HOST={FAKE_HOST}\nSEED_DB_PORT=15432\n")

    assert load_settings(Target.MAIN).target is Target.MAIN
