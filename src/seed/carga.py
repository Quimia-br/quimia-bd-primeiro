"""Carga no banco: inserts em lote com o Core, numa única transação.

Fluxo (``carregar``):

1. cada tabela é inserida na ordem de carga (com ``admin_log_edicoes`` no fim, ver
   ``ordem_de_insercao``) com ``insert(tabela)`` e uma lista de
   dicionários (um único comando por tabela, com ``RETURNING`` das PKs identity);
2. os IDs devolvidos, na ordem das linhas, formam o **registro de IDs**: a posição
   ``i`` da lista é o ID real da linha com ID provisório ``i + 1``;
3. as chaves estrangeiras das tabelas seguintes são traduzidas por esse registro;
4. ``tipos_historicos`` usa ``ON CONFLICT (nome) DO NOTHING`` e depois busca os IDs
   pelo nome (os tipos podem já existir no banco).

As datas chegam com fuso dos contratos e são gravadas sem fuso, no ``SEED_TIMEZONE``.
Tudo roda dentro da transação que quem chama abriu (``engine.begin()``): se qualquer
tabela falhar, nada fica gravado.
"""

from collections.abc import Mapping
from datetime import datetime
from enum import Enum
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import Column, Connection, Table, func, insert, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from seed.config import Target
from seed.contratos import Contrato
from seed.generators import DadosGerados
from seed.modelos import Base, table_names

TABELA_DE_REFERENCIA = "tipos_historicos"

CHAVES_NATURAIS: Mapping[str, tuple[str, ...]] = {
    "usuarios_empresas": ("cnpj", "email"),
    "admins": ("email",),
    "usuarios": ("email",),
    "produtos": ("cas_number",),
}
"""Colunas UNIQUE que identificam uma linha; usadas para recusar duplicatas no main."""


class CargaError(Exception):
    """O destino não está pronto para a carga (a mensagem diz o motivo)."""


# ---------------------------------------------------------------------------
# Conversão de linhas
# ---------------------------------------------------------------------------


def para_banco(linha: Contrato, zona: ZoneInfo) -> dict[str, Any]:
    """Dicionário pronto para o insert: datas sem fuso no ``zona`` e enums como texto."""
    valores: dict[str, Any] = {}
    for coluna, valor in linha.model_dump().items():
        if isinstance(valor, datetime):
            valor = valor.astimezone(zona).replace(tzinfo=None)
        elif isinstance(valor, Enum):
            valor = valor.value
        valores[coluna] = valor
    return valores


def _identity_pk(tabela: Table) -> Column[Any] | None:
    colunas = list(tabela.primary_key.columns)
    if len(colunas) == 1 and colunas[0].identity is not None:
        return colunas[0]
    return None


def tabela_do_id(coluna: Column[Any]) -> str | None:
    """Tabela cuja PK identity a coluna referencia (seguindo FKs compostas).

    ``historicos_produtos.id_usuario`` aponta para ``produtos_usuarios.id_usuario``,
    que por sua vez aponta para ``usuarios.id_usuario``: o resultado é ``usuarios``.
    """
    for fk in sorted(coluna.foreign_keys, key=lambda f: f.target_fullname):
        alvo = fk.column
        if alvo.identity is not None:
            return alvo.table.name
        seguinte = tabela_do_id(alvo)
        if seguinte is not None:
            return seguinte
    return None


def traduzir_ids(
    tabela: str, linhas: list[dict[str, Any]], registro: Mapping[str, list[int]]
) -> list[dict[str, Any]]:
    """Troca os IDs provisórios das chaves estrangeiras pelos IDs reais."""
    modelo = Base.metadata.tables[tabela]
    mapa = {c.name: alvo for c in modelo.columns if (alvo := tabela_do_id(c)) is not None}
    traduzidas = []
    for linha in linhas:
        nova = dict(linha)
        for coluna, alvo in mapa.items():
            if nova.get(coluna) is not None:
                nova[coluna] = _real(registro, alvo, nova[coluna])
        if tabela == "admin_log_edicoes":
            # id_registro não é FK: aponta para a tabela citada em tabela_afetada.
            nova["id_registro"] = _real(registro, nova["tabela_afetada"], nova["id_registro"])
        traduzidas.append(nova)
    return traduzidas


def _real(registro: Mapping[str, list[int]], tabela: str, provisorio: int) -> int:
    try:
        return registro[tabela][provisorio - 1]
    except KeyError, IndexError:
        msg = f"ID provisório {provisorio} de {tabela} não está no registro de IDs"
        raise CargaError(msg) from None


# ---------------------------------------------------------------------------
# Conferência do destino
# ---------------------------------------------------------------------------


def problemas_do_destino(conn: Connection, gerados: DadosGerados, target: Target) -> list[str]:
    """Motivos que impedem a carga, sem alterar nada.

    - test: as tabelas precisam estar vazias (exceto ``tipos_historicos``); use
      ``seed reset`` antes.
    - main: a carga é aditiva; ela é recusada se algum e-mail, CNPJ ou CAS gerado já
      existir, para nunca sobrescrever nem misturar registros.
    """
    problemas = []
    for nome, linhas in gerados.tabelas.items():
        if not linhas or nome == TABELA_DE_REFERENCIA:
            continue
        tabela = Base.metadata.tables[nome]
        if target is Target.TEST:
            total = conn.execute(select(func.count()).select_from(tabela)).scalar_one()
            if total:
                problemas.append(f"{nome} já tem {total} linhas (rode seed reset antes)")
            continue
        for coluna in CHAVES_NATURAIS.get(nome, ()):
            valores = [getattr(linha, coluna) for linha in linhas]
            existentes = conn.execute(
                select(func.count()).select_from(tabela).where(tabela.c[coluna].in_(valores))
            ).scalar_one()
            if existentes:
                problemas.append(f"{nome}.{coluna}: {existentes} valores gerados já existem")
    return problemas


# ---------------------------------------------------------------------------
# Inserts
# ---------------------------------------------------------------------------


TABELA_DE_AUDITORIA = "admin_log_edicoes"


def ordem_de_insercao(tabelas: list[str]) -> list[str]:
    """Ordem de carga com ``admin_log_edicoes`` no fim.

    ``admin_log_edicoes.id_registro`` não é FK, então a ordem calculada pelas FKs não
    sabe que ele aponta para ``produtos``, ``descartes_fds`` etc. O log só pode ser
    inserido depois de todas as tabelas auditáveis, para os IDs reais já existirem.
    """
    return [t for t in tabelas if t != TABELA_DE_AUDITORIA] + [
        t for t in tabelas if t == TABELA_DE_AUDITORIA
    ]


def carregar(conn: Connection, gerados: DadosGerados, zona: ZoneInfo) -> dict[str, int]:
    """Insere todas as tabelas geradas e devolve quantas linhas cada uma recebeu."""
    registro: dict[str, list[int]] = {}
    inseridas: dict[str, int] = {}
    for nome in ordem_de_insercao(list(gerados.tabelas)):
        linhas = gerados.tabelas[nome]
        if not linhas:
            inseridas[nome] = 0
            continue
        tabela = Base.metadata.tables[nome]
        valores = traduzir_ids(nome, [para_banco(linha, zona) for linha in linhas], registro)
        if nome == TABELA_DE_REFERENCIA:
            registro[nome], inseridas[nome] = _inserir_tipos(conn, tabela, valores)
            continue
        pk = _identity_pk(tabela)
        if pk is None:
            conn.execute(insert(tabela), valores)
        else:
            resultado = conn.execute(
                insert(tabela).returning(pk, sort_by_parameter_order=True), valores
            )
            registro[nome] = list(resultado.scalars().all())
            if len(registro[nome]) != len(valores):
                msg = (
                    f"{nome}: o RETURNING devolveu {len(registro[nome])} IDs "
                    f"para {len(valores)} linhas"
                )
                raise CargaError(msg)
        inseridas[nome] = len(valores)
    return inseridas


def _inserir_tipos(
    conn: Connection, tabela: Table, valores: list[dict[str, Any]]
) -> tuple[list[int], int]:
    """Insere os tipos que faltam e devolve os IDs de todos, na ordem do YAML."""
    resultado = conn.execute(
        pg_insert(tabela).on_conflict_do_nothing(index_elements=["nome"]).returning(tabela.c.nome),
        valores,
    )
    novos = len(resultado.all())
    nomes = [v["nome"] for v in valores]
    ids = dict(
        conn.execute(
            select(tabela.c.nome, tabela.c.id_tipo_historico).where(tabela.c.nome.in_(nomes))
        ).tuples()
    )
    return [ids[nome] for nome in nomes], novos


def esvaziar(conn: Connection, target: Target) -> list[str]:
    """``TRUNCATE`` das tabelas dos modelos, reiniciando as identities. Só no alvo test."""
    if target is not Target.TEST:
        msg = "reset é proibido fora do alvo test"
        raise CargaError(msg)
    nomes = sorted(table_names())
    lista = ", ".join(f'"{nome}"' for nome in nomes)  # nomes fixos dos modelos
    conn.execute(text(f"TRUNCATE TABLE {lista} RESTART IDENTITY CASCADE"))
    return nomes
