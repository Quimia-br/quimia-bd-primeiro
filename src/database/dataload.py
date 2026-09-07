import json
import random
from pathlib import Path

from connection import get_connection
from execute_sql import execute_sql

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "database" / "seeds" / "dev"

TABELAS = [
    "usuario_empresa", "superficie", "tipo_historico", "usuario", "comodo",
    "produto", "produto_usuario", "produto_superficie", "descarte_fds",
    "estante", "localizacao", "historico", "historico_produto_mistura",
]

ids: dict[str, list[int]] = {}


def load_json(tabela: str) -> list[dict]:
    path = DATA_DIR / f"{tabela}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)
