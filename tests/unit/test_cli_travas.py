"""Comandos run, reset, verificar e stats, e as travas do main (banco simulado)."""

import re
from dataclasses import replace

import pytest
from typer.testing import CliRunner

from seed import dados
from seed.cli import ExitCode, app
from seed.verificacao import ResultadoRegra
from tests.unit.conftest import FakeDb

runner = CliRunner()
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _invoke(args: list[str], entrada: str | None = None) -> tuple[int, str]:
    result = runner.invoke(app, args, input=entrada)
    return result.exit_code, _ANSI.sub("", result.output)


@pytest.fixture(autouse=True)
def _ambiente(seed_env: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEED_PASSWORD_PLAIN", "senha-de-teste")


def _catalogo_revisado(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simula um catálogo inteiramente revisado (só para os testes do main)."""
    carregados = dados.carregar_dados()
    revisados = [p.model_copy(update={"revisado": True}) for p in carregados.catalogo.produtos]
    catalogo = carregados.catalogo.model_copy(update={"produtos": revisados})
    monkeypatch.setattr(dados, "carregar_dados", lambda: replace(carregados, catalogo=catalogo))


# ------------------------------------------------------------------ run no test


def test_dry_run_generates_without_connecting(fake_db: FakeDb) -> None:
    codigo, saida = _invoke(["run", "--dry-run"])

    assert codigo == ExitCode.OK
    assert "nada foi gravado" in saida
    assert "semente 42" in saida
    assert fake_db.conexoes == [] and fake_db.carregados == []


def test_run_loads_everything_in_one_transaction(fake_db: FakeDb) -> None:
    codigo, saida = _invoke(["run", "--seed", "7"])

    assert codigo == ExitCode.OK, saida
    assert fake_db.conexoes == [True]  # uma conexão, com transação
    gerados = fake_db.carregados[0]
    assert gerados.semente == 7
    assert gerados.contagens()["admin_log_edicoes"] == 100
    assert "Carga concluída" in saida


def test_run_requires_password_for_synthetic_accounts(
    fake_db: FakeDb, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SEED_PASSWORD_PLAIN")

    codigo, saida = _invoke(["run"])

    assert codigo == ExitCode.CONFIGURACAO
    assert "SEED_PASSWORD_PLAIN" in saida


def test_run_refuses_schema_divergence(fake_db: FakeDb) -> None:
    fake_db.divergencias = ["usuarios.email: tipo VARCHAR(200) no banco, VARCHAR(150) no modelo"]

    codigo, saida = _invoke(["run"])

    assert codigo == ExitCode.SCHEMA
    assert "VARCHAR(200)" in saida
    assert fake_db.carregados == []


def test_run_refuses_non_empty_destination(fake_db: FakeDb) -> None:
    fake_db.problemas = ["usuarios já tem 100 linhas (rode seed reset antes)"]

    codigo, saida = _invoke(["run"])

    assert codigo == ExitCode.BLOQUEADO
    assert "seed reset" in saida
    assert fake_db.carregados == []


def test_run_refuses_timezone_mismatch(fake_db: FakeDb) -> None:
    fake_db.info = replace(fake_db.info, timezone="America/Sao_Paulo")

    codigo, saida = _invoke(["run"])
    assert codigo == ExitCode.BLOQUEADO
    assert "--ignorar-fuso" in saida
    assert fake_db.carregados == []

    codigo, _ = _invoke(["run", "--ignorar-fuso"])
    assert codigo == ExitCode.OK
    assert len(fake_db.carregados) == 1


# ------------------------------------------------------------------ run no main


def test_main_without_synthetic_loads_only_history_types(fake_db: FakeDb) -> None:
    codigo, saida = _invoke(["--target", "main", "run"], entrada="defaultdb\n")

    assert codigo == ExitCode.OK, saida
    contagens = fake_db.carregados[0].contagens()
    assert contagens["tipos_historicos"] == 5
    assert sum(contagens.values()) == 5
    assert "banco PRINCIPAL" in saida


def test_main_requires_database_name(fake_db: FakeDb) -> None:
    codigo, saida = _invoke(["--target", "main", "run"], entrada="outro_banco\n")

    assert codigo == ExitCode.BLOQUEADO
    assert "não confere" in saida
    assert fake_db.carregados == [] and fake_db.conexoes == []


def test_main_synthetic_requires_second_confirmation(fake_db: FakeDb) -> None:
    codigo, saida = _invoke(["--target", "main", "run", "--allow-synthetic"], entrada="n\n")

    assert codigo == ExitCode.BLOQUEADO
    assert "SINTÉTICOS" in saida
    assert fake_db.carregados == []


def test_main_synthetic_never_includes_audit_logs(
    fake_db: FakeDb, monkeypatch: pytest.MonkeyPatch
) -> None:
    _catalogo_revisado(monkeypatch)

    codigo, saida = _invoke(
        ["--target", "main", "run", "--allow-synthetic"], entrada="y\ndefaultdb\n"
    )

    assert codigo == ExitCode.OK, saida
    contagens = fake_db.carregados[0].contagens()
    assert contagens["admin_log_edicoes"] == 0
    assert contagens["usuarios"] == 100


def test_main_synthetic_needs_reviewed_catalog(fake_db: FakeDb) -> None:
    # O catálogo real ainda não tem entradas revisadas: não há produtos para o main.
    codigo, saida = _invoke(
        ["--target", "main", "run", "--allow-synthetic"], entrada="y\ndefaultdb\n"
    )

    assert codigo == ExitCode.DADOS
    assert "sem quebrar as regras" in saida
    assert fake_db.carregados == []


def test_main_dry_run_does_not_ask_database_name(fake_db: FakeDb) -> None:
    codigo, saida = _invoke(["--target", "main", "run", "--dry-run"])

    assert codigo == ExitCode.OK
    assert "Digite o nome do banco" not in saida


# ------------------------------------------------------------------ reset


def test_reset_is_blocked_on_main(fake_db: FakeDb) -> None:
    codigo, saida = _invoke(["--target", "main", "reset", "--yes"])

    assert codigo == ExitCode.BLOQUEADO
    assert "proibido" in saida
    assert fake_db.esvaziados == [] and fake_db.conexoes == []


def test_reset_asks_confirmation(fake_db: FakeDb) -> None:
    codigo, _ = _invoke(["reset"], entrada="n\n")
    assert codigo == ExitCode.BLOQUEADO
    assert fake_db.esvaziados == []

    codigo, saida = _invoke(["reset"], entrada="y\n")
    assert codigo == ExitCode.OK
    assert "13 tabelas esvaziadas" in saida


def test_reset_yes_skips_confirmation(fake_db: FakeDb) -> None:
    codigo, _ = _invoke(["reset", "--yes"])

    assert codigo == ExitCode.OK
    assert len(fake_db.esvaziados) == 1


# ------------------------------------------------------------------ verificar e stats


def test_verificar_all_approved(fake_db: FakeDb) -> None:
    fake_db.regras = [ResultadoRegra("Regra A", 0), ResultadoRegra("Regra B", 0)]

    codigo, saida = _invoke(["verificar"])

    assert codigo == ExitCode.OK
    assert "Todas as regras aprovadas" in saida


def test_verificar_reports_failures(fake_db: FakeDb) -> None:
    fake_db.regras = [ResultadoRegra("Regra A", 0), ResultadoRegra("Regra B", 3)]

    codigo, saida = _invoke(["verificar"])

    assert codigo == ExitCode.REGRAS
    assert "reprovada" in saida
    assert "1 regra(s) reprovada(s)" in saida


def test_stats_shows_counts(fake_db: FakeDb) -> None:
    fake_db.contagens = {"usuarios": 100, "tipos_historicos": 5}

    codigo, saida = _invoke(["stats"])

    assert codigo == ExitCode.OK
    assert "usuarios" in saida and "100" in saida
