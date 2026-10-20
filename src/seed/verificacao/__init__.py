"""Consultas somente leitura no banco, em três partes:

- ``diagnostico``: versão, conexões, tamanho e fuso do servidor (``seed check``);
- ``schema``: comparação dos modelos com as tabelas reais (``seed check`` e ``seed run``);
- ``regras``: regras de negócio (``seed verificar``) e contagens (``seed stats``).
"""

from seed.verificacao.diagnostico import ServerInfo, collect_server_info, fetch_server_info
from seed.verificacao.regras import REGRAS, ResultadoRegra, contagens, verificar_regras
from seed.verificacao.schema import comparar_schema

__all__ = [
    "REGRAS",
    "ResultadoRegra",
    "ServerInfo",
    "collect_server_info",
    "comparar_schema",
    "contagens",
    "fetch_server_info",
    "verificar_regras",
]
