"""Carga: conversão das linhas, tradução de IDs e inserts, com uma conexão simulada."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.sql.dml import Insert

from seed import carga
from seed.config import Target
from seed.contratos import Localizacao, Usuario
from seed.dados import carregar_dados
from seed.generators import DadosGerados, gerar_tudo
from seed.modelos import Base

AGORA = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


class _Result:
    """Imita o Result do SQLAlchemy, inclusive ter ``keys()`` e não aceitar ``[]``.

    Por isso ``dict(result)`` falha aqui como falha no banco real: o código precisa
    chamar ``.all()`` antes.
    """

    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def keys(self) -> list[str]:
        return ["coluna"]

    def __iter__(self) -> Any:
        return iter(self._rows)

    def scalars(self) -> _Result:
        return self

    def all(self) -> list[Any]:
        return list(self._rows)

    def tuples(self) -> _Result:
        return self

    def scalar_one(self) -> Any:
        return self._rows[0]


class FakeConnection:
    """Grava cada insert e devolve IDs reais diferentes dos provisórios (1001, 1002...)."""

    def __init__(self, tipos_existentes: dict[str, int] | None = None) -> None:
        self.inserts: dict[str, list[dict[str, Any]]] = {}
        self.ids: dict[str, list[int]] = {}
        self.tipos = dict(tipos_existentes or {})
        self.sql: list[str] = []

    def execute(self, stmt: Any, params: Any = None) -> _Result:
        if isinstance(stmt, Insert) and isinstance(params, list):
            nome = stmt.table.name
            self.inserts[nome] = params
            if nome == "tipos_historicos":
                novos = [p["nome"] for p in params if p["nome"] not in self.tipos]
                for nome_tipo in novos:
                    self.tipos[nome_tipo] = 500 + len(self.tipos)
                return _Result([(n,) for n in novos])
            ids = [1000 * (len(self.ids) + 1) + i for i in range(1, len(params) + 1)]
            self.ids[nome] = ids
            return _Result(ids)
        texto = str(stmt)
        self.sql.append(texto)
        if "tipos_historicos" in texto:
            return _Result(list(self.tipos.items()))
        raise AssertionError(f"consulta inesperada: {texto}")


@pytest.fixture(scope="module")
def gerados() -> DadosGerados:
    dados = carregar_dados()
    return gerar_tudo(dados.referencia, dados.catalogo.produtos, "x", semente=42, agora=AGORA)


def test_para_banco_converts_dates_and_enums() -> None:
    usuario = Usuario(
        nome="Ana",
        data_nascimento=date(1990, 1, 1),
        email="ana.1@example.com",
        data_cadastro=datetime(2026, 1, 1, 3, 0, tzinfo=UTC),
        senha_hash="h",
        status="ATIVO",  # type: ignore[arg-type]
        url_foto=None,
    )

    linha = carga.para_banco(usuario, ZoneInfo("America/Sao_Paulo"))

    assert linha["data_cadastro"] == datetime(2026, 1, 1, 0, 0)  # 03:00 UTC = 00:00 em SP
    assert linha["data_cadastro"].tzinfo is None
    assert linha["status"] == "ATIVO" and type(linha["status"]) is str
    assert linha["data_nascimento"] == date(1990, 1, 1)


def test_para_banco_keeps_decimals() -> None:
    local = Localizacao(
        id_usuario=1, cep="01310100", latitude=Decimal("-23.5"), longitude=Decimal("-46.6")
    )
    assert carga.para_banco(local, ZoneInfo("UTC"))["latitude"] == Decimal("-23.5")


@pytest.mark.parametrize(
    ("tabela", "coluna", "alvo"),
    [
        ("produtos", "id_usuario_empresa", "usuarios_empresas"),
        ("historicos", "id_estante", "estantes"),
        ("historicos", "id_usuario", "usuarios"),
        ("historicos_produtos", "id_usuario", "usuarios"),  # via produtos_usuarios
        ("historicos_produtos", "id_produto", "produtos"),
        ("historicos_produtos", "id_historico", "historicos"),
        ("descartes_fds", "id_produto", "produtos"),
        ("produtos_estantes", "id_estante", "estantes"),
        ("historicos", "id_historico", None),  # a própria PK não é FK
        ("usuarios", "email", None),
    ],
)
def test_tabela_do_id(tabela: str, coluna: str, alvo: str | None) -> None:
    assert carga.tabela_do_id(Base.metadata.tables[tabela].c[coluna]) == alvo


def test_traduzir_ids_including_audit_record() -> None:
    registro = {"admins": [501, 502], "usuarios": [701, 702, 703]}
    linhas = [{"id_admin": 2, "tabela_afetada": "usuarios", "id_registro": 3}]

    assert carga.traduzir_ids("admin_log_edicoes", linhas, registro) == [
        {"id_admin": 502, "tabela_afetada": "usuarios", "id_registro": 703}
    ]


def test_traduzir_ids_keeps_null_foreign_keys() -> None:
    linhas = [{"id_estante": None, "id_usuario": 1, "id_tipo_historico": 1}]
    registro = {"usuarios": [9], "tipos_historicos": [4]}

    assert carga.traduzir_ids("historicos", linhas, registro)[0]["id_estante"] is None


def test_traduzir_ids_rejects_unknown_id() -> None:
    with pytest.raises(carga.CargaError, match="não está no registro"):
        carga.traduzir_ids("estantes", [{"id_usuario": 5, "comodo": "SALA"}], {"usuarios": [1]})


def test_carregar_inserts_every_table_with_real_ids(gerados: DadosGerados) -> None:
    conn = FakeConnection(tipos_existentes={"USO": 7})

    inseridas = carga.carregar(conn, gerados, ZoneInfo("UTC"))  # type: ignore[arg-type]

    assert inseridas["tipos_historicos"] == 4  # USO já existia
    assert all(inseridas[t] == 100 for t in inseridas if t != "tipos_historicos")
    # Ordem de carga, com o log de auditoria por último (id_registro não é FK).
    assert list(conn.inserts) == carga.ordem_de_insercao(list(gerados.tabelas))
    assert list(conn.inserts)[-1] == "admin_log_edicoes"

    # Nenhuma coluna identity é enviada.
    assert "id_usuario" not in conn.inserts["usuarios"][0]
    # As FKs usam os IDs reais devolvidos pelo RETURNING.
    ids_usuarios = set(conn.ids["usuarios"])
    assert {e["id_usuario"] for e in conn.inserts["estantes"]} <= ids_usuarios
    ids_tipos = set(conn.tipos.values())
    assert {h["id_tipo_historico"] for h in conn.inserts["historicos"]} <= ids_tipos
    for log in conn.inserts["admin_log_edicoes"]:
        assert log["id_registro"] in set(conn.ids.get(log["tabela_afetada"], conn.tipos.values()))


def test_carregar_maps_existing_history_types_by_name(gerados: DadosGerados) -> None:
    conn = FakeConnection(tipos_existentes={"MISTURA": 42})
    carga.carregar(conn, gerados, ZoneInfo("UTC"))  # type: ignore[arg-type]

    tipos = {t.nome: i + 1 for i, t in enumerate(gerados.tabelas["tipos_historicos"])}  # type: ignore[attr-defined]
    provisorio_mistura = tipos["MISTURA"]
    historicos = gerados.tabelas["historicos"]
    for gerado, inserido in zip(historicos, conn.inserts["historicos"], strict=True):
        if gerado.id_tipo_historico == provisorio_mistura:  # type: ignore[attr-defined]
            assert inserido["id_tipo_historico"] == 42


def test_esvaziar_is_blocked_outside_test() -> None:
    with pytest.raises(carga.CargaError, match="proibido"):
        carga.esvaziar(FakeConnection(), Target.MAIN)  # type: ignore[arg-type]


def test_audit_log_is_inserted_after_every_audited_table() -> None:
    ordem = carga.ordem_de_insercao(list(Base.metadata.tables))
    assert ordem[-1] == "admin_log_edicoes"
    for tabela in (
        "usuarios",
        "usuarios_empresas",
        "produtos",
        "descartes_fds",
        "tipos_historicos",
    ):
        assert ordem.index(tabela) < ordem.index("admin_log_edicoes")
