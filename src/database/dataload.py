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

def inserir(conn, tabela: str, pk_col: str, rows: list[dict], extra_cols_fn=None):

    novos_ids = []
    for row in rows:
        row = dict(row)  # copia para nao mutar o original
        if extra_cols_fn:
            row.update(extra_cols_fn(row))

        colunas = list(row.keys())
        valores = [row[c] for c in colunas]
        placeholders = ", ".join(["%s"] * len(colunas))
        query = f"""
            INSERT INTO {tabela} ({', '.join(colunas)})
            VALUES ({placeholders})
            RETURNING {pk_col};
        """
        resultado = execute_sql(conn, query, valores)
        novos_ids.append(resultado[0][pk_col])

    ids[tabela] = novos_ids
    print(f"[OK] {tabela}: {len(novos_ids)} registros inseridos")
