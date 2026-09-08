import psycopg2.extras

def execute_sql(conn, query: str, params: list | None = None) -> list[dict]:

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, params or [])

        if cur.description:  # tem colunas para retornar (SELECT / RETURNING)
            return cur.fetchall()
        return []