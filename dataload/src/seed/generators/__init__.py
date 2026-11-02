"""Geradores de dados sintéticos, um módulo por grupo de tabelas.

Todos usam Faker ``pt_BR`` e ``random.Random`` com a semente única da carga, recebem
os pais já gerados como parâmetro e devolvem linhas validadas pelos contratos
(``seed.contratos``). ``tipos_historicos`` não tem gerador: vem de ``data/reference``.

- ``contas``: usuarios, admins, usuarios_empresas, localizacoes
- ``produtos``: produtos, descartes_fds, produtos_usuarios
- ``estantes``: estantes, produtos_estantes
- ``historicos``: historicos, historicos_produtos, admin_log_edicoes

As chaves estrangeiras usam IDs provisórios (ver ``contexto.py``).
"""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from seed.config import QUANTIDADES
from seed.contratos import Contrato
from seed.dados import EntradaCatalogo, Referencia
from seed.generators import contas, estantes, historicos, produtos
from seed.generators.contexto import Contexto
from seed.modelos import load_order


@dataclass(frozen=True, slots=True)
class DadosGerados:
    """Linhas geradas, por tabela, na ordem de carga."""

    semente: int
    agora: datetime
    tabelas: dict[str, list[Contrato]]

    def contagens(self) -> dict[str, int]:
        return {tabela: len(linhas) for tabela, linhas in self.tabelas.items()}

    def hash_conteudo(self) -> str:
        """SHA-256 do conteúdo: a mesma semente e o mesmo ``agora`` dão o mesmo hash."""
        conteudo = {
            tabela: [linha.model_dump(mode="json") for linha in linhas]
            for tabela, linhas in self.tabelas.items()
        }
        texto = json.dumps(conteudo, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def gerar_tudo(
    referencia: Referencia,
    catalogo: list[EntradaCatalogo],
    senha: str,
    *,
    semente: int,
    agora: datetime | None = None,
    auditoria: bool = True,
    quantidades: Mapping[str, int] = QUANTIDADES,
) -> DadosGerados:
    """Gera todas as tabelas, com dados sintéticos.

    ``auditoria=False`` deixa ``admin_log_edicoes`` vazia (obrigatório no alvo main).
    O número de produtos é limitado pelo catálogo (um produto por chave natural).
    """
    ctx = Contexto.criar(semente, agora)
    senha_hash = contas.gerar_senha_hash(senha, ctx.rng)

    entradas = catalogo[: min(quantidades["produtos"], produtos.limite_produtos(catalogo))]

    empresas = contas.gerar_empresas(ctx, quantidades["usuarios_empresas"], senha_hash)
    admins = contas.gerar_admins(ctx, quantidades["admins"], senha_hash)
    tipos = historicos.gerar_tipos(referencia)
    usuarios = contas.gerar_usuarios(ctx, quantidades["usuarios"], senha_hash)

    lista_produtos = produtos.gerar_produtos(ctx, entradas, len(empresas))
    localizacoes = contas.gerar_localizacoes(ctx, usuarios, referencia)
    posses = produtos.gerar_produtos_usuarios(
        ctx, quantidades["produtos_usuarios"], len(usuarios), len(lista_produtos)
    )
    lista_estantes = estantes.gerar_estantes(
        ctx, quantidades["estantes"], len(usuarios), posses, list(referencia.comodos)
    )
    descartes = produtos.gerar_descartes(entradas)
    guardados = estantes.gerar_produtos_estantes(ctx, lista_estantes, posses, usuarios)
    lista_historicos, vinculos = historicos.gerar_historicos(
        ctx,
        quantidades["historicos"],
        quantidades["historicos_produtos"],
        referencia,
        usuarios,
        lista_estantes,
        posses,
        guardados,
    )

    logs = []
    if auditoria:
        criacao: dict[str, list[datetime | None]] = {
            "usuarios": [u.data_cadastro for u in usuarios],
            "usuarios_empresas": [e.data_cadastro for e in empresas],
            "produtos": [None] * len(lista_produtos),
            "descartes_fds": [None] * len(descartes),
            "tipos_historicos": [None] * len(tipos),
        }
        auditaveis = {t: criacao[t] for t in referencia.tabelas_auditaveis if t in criacao}
        logs = historicos.gerar_logs(ctx, quantidades["admin_log_edicoes"], admins, auditaveis)

    por_tabela: dict[str, list[Contrato]] = {
        "usuarios_empresas": list(empresas),
        "admins": list(admins),
        "tipos_historicos": list(tipos),
        "usuarios": list(usuarios),
        "produtos": list(lista_produtos),
        "admin_log_edicoes": list(logs),
        "localizacoes": list(localizacoes),
        "estantes": list(lista_estantes),
        "produtos_usuarios": list(posses),
        "descartes_fds": list(descartes),
        "produtos_estantes": list(guardados),
        "historicos": list(lista_historicos),
        "historicos_produtos": list(vinculos),
    }
    tabelas = {tabela: por_tabela[tabela] for tabela in load_order()}
    return DadosGerados(semente=semente, agora=ctx.agora, tabelas=tabelas)


def gerar_referencia(
    referencia: Referencia, *, semente: int, agora: datetime | None = None
) -> DadosGerados:
    """Só os dados de referência (tipos de histórico); as demais tabelas ficam vazias.

    É o que o alvo main recebe sem ``--allow-synthetic``: os produtos do catálogo
    precisam de uma empresa dona, e as empresas são sintéticas.
    """
    tabelas: dict[str, list[Contrato]] = {nome: [] for nome in load_order()}
    tabelas["tipos_historicos"] = list(historicos.gerar_tipos(referencia))
    return DadosGerados(semente=semente, agora=agora or datetime.now(UTC), tabelas=tabelas)
