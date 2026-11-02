"""Isolamento dos testes unitários.

Todo teste unitário roda sem variáveis ``SEED_*`` do ambiente real, numa pasta
temporária (então nunca lê o ``.env.test`` nem o ``.env`` do projeto) e com o
cache de ``get_settings`` limpo. Nenhum teste unitário conecta a banco.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from seed import carga, verificacao
from seed.cli import auxiliares
from seed.config import Target, get_settings
from seed.generators import DadosGerados
from seed.verificacao import ResultadoRegra, ServerInfo


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    for name in list(os.environ):
        if name.upper().startswith("SEED_"):
            monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@dataclass
class FakeDb:
    """Banco simulado para os testes da CLI: nada conecta de verdade.

    Os campos controlam o que cada consulta "devolve" e registram o que foi chamado.
    """

    info: ServerInfo
    divergencias: list[str] = field(default_factory=list)
    problemas: list[str] = field(default_factory=list)
    regras: list[ResultadoRegra] = field(default_factory=list)
    contagens: dict[str, int] = field(default_factory=dict)
    conexoes: list[bool] = field(default_factory=list)
    carregados: list[DadosGerados] = field(default_factory=list)
    esvaziados: list[Target] = field(default_factory=list)


HEALTHY = ServerInfo(
    database="defaultdb",
    user="avnadmin",
    current_schema="public",
    server_version="17.6",
    max_connections=20,
    open_connections=3,
    database_size_bytes=8 * 1024 * 1024,
    timezone="UTC",
    missing_tables=(),
)


@pytest.fixture
def fake_db(monkeypatch: pytest.MonkeyPatch) -> FakeDb:
    """Troca toda função que tocaria o banco por versões em memória."""
    db = FakeDb(info=HEALTHY)

    @contextmanager
    def conexao(settings: object, *, transacao: bool = False) -> Iterator[object]:
        db.conexoes.append(transacao)
        yield object()

    def carregar(conn: object, gerados: DadosGerados, zona: object) -> dict[str, int]:
        db.carregados.append(gerados)
        return gerados.contagens()

    def esvaziar(conn: object, target: Target) -> list[str]:
        if target is not Target.TEST:
            raise carga.CargaError("reset é proibido fora do alvo test")
        db.esvaziados.append(target)
        return ["t"] * 13

    monkeypatch.setattr(auxiliares, "conexao", conexao)
    monkeypatch.setattr(verificacao, "fetch_server_info", lambda settings: db.info)
    monkeypatch.setattr(verificacao, "comparar_schema", lambda conn, schema: db.divergencias)
    monkeypatch.setattr(verificacao, "verificar_regras", lambda conn, s, r: db.regras)
    monkeypatch.setattr(verificacao, "contagens", lambda conn: db.contagens)
    monkeypatch.setattr(carga, "problemas_do_destino", lambda conn, g, t: db.problemas)
    monkeypatch.setattr(carga, "carregar", carregar)
    monkeypatch.setattr(carga, "esvaziar", esvaziar)
    return db
