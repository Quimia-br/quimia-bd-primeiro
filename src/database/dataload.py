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

def rand_id_or_none(tabela: str, prob_nulo: float = 0.0):
    if random.random() < prob_nulo:
        return None
    return random.choice(ids[tabela])


def pares_unicos(tabela_a: str, tabela_b: str, qtd: int) -> list[tuple[int, int]]:
    """Sorteia qtd pares (id_a, id_b) sem repetir combinacao."""
    pares = set()
    while len(pares) < qtd:
        pares.add((rand_id_or_none(tabela_a), rand_id_or_none(tabela_b)))
    return list(pares)


def inserir_associativa(conn, tabela: str, pk_col: str, col_a: str, tabela_a: str, col_b: str, tabela_b: str):
    """Insere uma tabela associativa (n:n) sorteando pares unicos entre tabela_a e tabela_b."""
    rows = load_json(tabela)
    for row, (id_a, id_b) in zip(rows, pares_unicos(tabela_a, tabela_b, len(rows))):
        row[col_a] = id_a
        row[col_b] = id_b
    inserir(conn, tabela, pk_col, rows)



def main():
    conn = get_connection()

    try:
        # limpa o banco antes de popular, pra poder rodar o script quantas vezes quiser
        execute_sql(conn, f"TRUNCATE {', '.join(TABELAS)} RESTART IDENTITY CASCADE;")

        # nivel 0 --> sem fk

        inserir(conn, "usuario_empresa", "id_usuario_empresa", load_json("usuario_empresa"))
        inserir(conn, "superficie", "id_superficie", load_json("superficie"))
        inserir(conn, "tipo_historico", "id_tipo_historico", load_json("tipo_historico"))
        inserir(conn, "usuario", "id_usuario", load_json("usuario"))
        inserir(conn, "comodo", "id_comodo", load_json("comodo"))

        # nivel 1

        inserir(
            conn, "produto", "id_produto", load_json("produto"),
            extra_cols_fn=lambda row: {"id_usuario_empresa": rand_id_or_none("usuario_empresa")},
        )

        inserir(
            conn, "estante", "id_estante", load_json("estante"),
            extra_cols_fn=lambda row: {
                "id_usuario": rand_id_or_none("usuario"),
                "id_comodo": rand_id_or_none("comodo", prob_nulo=0.1),
            },
        )

        inserir(
            conn, "localizacao", "id_localizacao", load_json("localizacao"),
            extra_cols_fn=lambda row: {"id_usuario": rand_id_or_none("usuario", prob_nulo=0.1)},
        )

        # nivel 2

        # produto_usuario e produto_superficie sao associativas: sorteia pares
        # sem repetir combinacao, pra nao vincular o mesmo usuario/superficie 2x ao mesmo produto.
        inserir_associativa(conn, "produto_usuario", "id_produto_usuario", "id_produto", "produto", "id_usuario", "usuario")
        inserir_associativa(conn, "produto_superficie", "id_produto_superficie", "id_produto", "produto", "id_superficie", "superficie")

        # descarte_fds tem id_produto UNIQUE -> nao pode repetir produto.
        # sorteia sem reposicao a partir da lista de produtos.
        produtos_disponiveis = ids["produto"][:]
        random.shuffle(produtos_disponiveis)
        descarte_rows = load_json("descarte_fds")
        for row, id_produto in zip(descarte_rows, produtos_disponiveis):
            row["id_produto"] = id_produto
        inserir(conn, "descarte_fds", "id_descarte_fds", descarte_rows)

        # nivel 3

        inserir(
            conn, "historico", "id_historico", load_json("historico"),
            extra_cols_fn=lambda row: {
                "id_estante": rand_id_or_none("estante"),
                "id_usuario": rand_id_or_none("usuario", prob_nulo=0.15),
                "id_tipo_historico": rand_id_or_none("tipo_historico"),
                "id_produto_superficie": rand_id_or_none("produto_superficie", prob_nulo=0.3),
                "id_produto_usuario": rand_id_or_none("produto_usuario", prob_nulo=0.3),
            },
        )

        # nivel 4 - tabela associativa (PK composta, sem duplicar par)

        for id_produto, id_historico in pares_unicos("produto", "historico", len(ids["historico"])):
            query = """
                INSERT INTO historico_produto_mistura (id_produto, id_historico)
                VALUES (%s, %s);
            """
            execute_sql(conn, query, [id_produto, id_historico])
        print(f"[OK] historico_produto_mistura: {len(ids['historico'])} registros inseridos")

        conn.commit()
        print("\nPopulacao concluida com sucesso.")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERRO] Populacao abortada, rollback executado: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()