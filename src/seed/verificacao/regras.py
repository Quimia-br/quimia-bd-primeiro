"""Regras de negócio conferidas no banco pelo ``seed verificar`` (somente leitura).

Cada regra conta as linhas que a violam: zero é aprovado. As consultas valem para o
banco inteiro (inclusive dados que não vieram do seed). Datas são comparadas com o
momento atual no ``SEED_TIMEZONE``, o fuso em que as colunas ``TIMESTAMP`` são gravadas.
"""

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import Connection, exists, func, select, text

from seed import validacao
from seed.config import IDADE_MINIMA, Settings
from seed.dados import Referencia
from seed.modelos import Base


@dataclass(frozen=True, slots=True)
class ResultadoRegra:
    """Resultado de uma regra: aprovada quando não há violações."""

    nome: str
    violacoes: int

    @property
    def aprovada(self) -> bool:
        return self.violacoes == 0


def _contar(conn: Connection, sql: str, **params: object) -> int:
    return int(conn.execute(text(sql), params).scalar_one())


# Interpolado nas consultas (constante); o fuso vai como parâmetro :tz.
_AGORA = "(now() AT TIME ZONE :tz)"


def _estante_do_usuario(conn: Connection, **_: object) -> int:
    return _contar(
        conn,
        """SELECT count(*) FROM historicos h
           JOIN estantes e ON e.id_estante = h.id_estante
           WHERE e.id_usuario <> h.id_usuario""",
    )


def _produto_do_historico(conn: Connection, **_: object) -> int:
    return _contar(
        conn,
        """SELECT count(*) FROM historicos_produtos hp
           JOIN historicos h ON h.id_historico = hp.id_historico
           LEFT JOIN produtos_usuarios pu
                  ON pu.id_usuario = hp.id_usuario AND pu.id_produto = hp.id_produto
           WHERE hp.id_usuario <> h.id_usuario OR pu.id_usuario IS NULL""",
    )


def _produto_na_estante_do_dono(conn: Connection, **_: object) -> int:
    return _contar(
        conn,
        """SELECT count(*) FROM produtos_estantes pe
           JOIN estantes e ON e.id_estante = pe.id_estante
           LEFT JOIN produtos_usuarios pu
                  ON pu.id_usuario = e.id_usuario AND pu.id_produto = pe.id_produto
           WHERE pu.id_usuario IS NULL""",
    )


def _data_adicao(conn: Connection, tz: str, **_: object) -> int:
    return _contar(
        conn,
        f"""SELECT count(*) FROM produtos_estantes pe
            JOIN estantes e ON e.id_estante = pe.id_estante
            JOIN usuarios u ON u.id_usuario = e.id_usuario
            WHERE pe.data_adicao < u.data_cadastro OR pe.data_adicao > {_AGORA}""",
        tz=tz,
    )


def _regras_por_tipo(conn: Connection, referencia: Referencia, **_: object) -> int:
    """Quantidade de produtos e estante obrigatória de cada tipo (regras do YAML)."""
    linhas = conn.execute(
        text(
            """SELECT h.id_historico, t.nome, h.id_estante, count(hp.id_produto)
               FROM historicos h
               JOIN tipos_historicos t ON t.id_tipo_historico = h.id_tipo_historico
               LEFT JOIN historicos_produtos hp ON hp.id_historico = h.id_historico
               GROUP BY h.id_historico, t.nome, h.id_estante"""
        )
    ).tuples()
    regras = {r.nome: r for r in referencia.tipos_historicos}
    violacoes = 0
    for _id, nome, id_estante, produtos in linhas:
        regra = regras.get(nome)
        if regra is None:
            continue  # tipo que não está no YAML: fora das regras do seed
        if (
            not regra.produtos_min <= produtos <= regra.produtos_max
            or regra.estante_obrigatoria
            and id_estante is None
        ):
            violacoes += 1
    return violacoes


def _produtos_na_estante_do_historico(conn: Connection, referencia: Referencia, **_: object) -> int:
    """Nos tipos com estante obrigatória, o produto está na estante desde antes do histórico."""
    obrigatorios = [r.nome for r in referencia.tipos_historicos if r.estante_obrigatoria]
    if not obrigatorios:
        return 0
    return _contar(
        conn,
        """SELECT count(*) FROM historicos h
           JOIN tipos_historicos t ON t.id_tipo_historico = h.id_tipo_historico
           JOIN historicos_produtos hp ON hp.id_historico = h.id_historico
           LEFT JOIN produtos_estantes pe
                  ON pe.id_estante = h.id_estante AND pe.id_produto = hp.id_produto
           WHERE t.nome = ANY(:tipos)
             AND (pe.id_estante IS NULL OR pe.data_adicao > h.data_execucao)""",
        tipos=obrigatorios,
    )


def _mistura(conn: Connection, **_: object) -> int:
    return _contar(
        conn,
        """SELECT count(*) FROM (
               SELECT h.id_historico FROM historicos h
               JOIN tipos_historicos t ON t.id_tipo_historico = h.id_tipo_historico
               LEFT JOIN historicos_produtos hp ON hp.id_historico = h.id_historico
               WHERE t.nome = 'MISTURA'
               GROUP BY h.id_historico HAVING count(hp.id_produto) < 2) AS m""",
    )


def _descarte_por_produto(conn: Connection, **_: object) -> int:
    return _contar(
        conn,
        """SELECT count(*) FROM produtos p
           LEFT JOIN descartes_fds d ON d.id_produto = p.id_produto
           WHERE d.id_produto IS NULL""",
    )


def _datas(conn: Connection, tz: str, **_: object) -> int:
    return _contar(
        conn,
        f"""SELECT
              (SELECT count(*) FROM usuarios WHERE data_cadastro > {_AGORA})
            + (SELECT count(*) FROM admins WHERE data_cadastro > {_AGORA})
            + (SELECT count(*) FROM usuarios_empresas WHERE data_cadastro > {_AGORA})
            + (SELECT count(*) FROM historicos h JOIN usuarios u ON u.id_usuario = h.id_usuario
               WHERE h.data_execucao < u.data_cadastro OR h.data_execucao > {_AGORA})""",
        tz=tz,
    )


def _idade_minima(conn: Connection, **_: object) -> int:
    return _contar(
        conn,
        """SELECT count(*) FROM usuarios
           WHERE data_nascimento IS NOT NULL
             AND age(data_cadastro::date, data_nascimento) < make_interval(years => :idade)""",
        idade=IDADE_MINIMA,
    )


def _estante_por_comodo(conn: Connection, **_: object) -> int:
    return _contar(
        conn,
        """SELECT count(*) FROM (SELECT 1 FROM estantes
           GROUP BY id_usuario, comodo HAVING count(*) > 1) AS d""",
    )


def _logs(conn: Connection, referencia: Referencia, **_: object) -> int:
    """INSERT sem dado_anterior, data após o cadastro do admin e registro existente."""
    violacoes = _contar(
        conn,
        """SELECT count(*) FROM admin_log_edicoes l
           JOIN admins a ON a.id_admin = l.id_admin
           WHERE (l.acao = 'INSERT' AND l.dado_anterior IS NOT NULL)
              OR (l.acao <> 'INSERT' AND l.dado_anterior IS NULL)
              OR l.data_edicao < a.data_cadastro""",
    )
    logs = Base.metadata.tables["admin_log_edicoes"]
    for nome in referencia.tabelas_auditaveis:
        tabela = Base.metadata.tables[nome]
        pk = next(iter(tabela.primary_key.columns))
        violacoes += int(
            conn.execute(
                select(func.count())
                .select_from(logs)
                .where(
                    logs.c.tabela_afetada == nome,
                    logs.c.acao != "DELETE",
                    ~exists().where(pk == logs.c.id_registro),
                )
            ).scalar_one()
        )
    return violacoes


def _emails(conn: Connection, **_: object) -> int:
    violacoes = 0
    for tabela in ("usuarios", "admins", "usuarios_empresas"):
        violacoes += _contar(
            conn,
            f"""SELECT (SELECT count(*) FROM {tabela} WHERE email <> lower(email))
                     + (SELECT count(*) FROM (SELECT 1 FROM {tabela}
                        GROUP BY lower(email) HAVING count(*) > 1) AS d)""",
        )
    return violacoes


def _cnpj_e_cas(conn: Connection, **_: object) -> int:
    cnpjs = conn.execute(text("SELECT cnpj FROM usuarios_empresas")).scalars()
    cas = conn.execute(text("SELECT cas_number FROM produtos")).scalars()
    return sum(not validacao.cnpj_valido(c) for c in cnpjs) + sum(
        not validacao.cas_valido(c) for c in cas
    )


REGRAS: tuple[tuple[str, Callable[..., int]], ...] = (
    ("Estante do histórico é do mesmo usuário", _estante_do_usuario),
    ("Produto do histórico pertence ao usuário do histórico", _produto_do_historico),
    ("Produto na estante pertence ao dono da estante", _produto_na_estante_do_dono),
    ("data_adicao entre o cadastro do dono e agora", _data_adicao),
    ("Quantidade de produtos e estante por tipo de histórico", _regras_por_tipo),
    ("Produto do histórico com estante já estava na estante", _produtos_na_estante_do_historico),
    ("MISTURA tem 2 ou mais produtos", _mistura),
    ("Todo produto tem um descarte", _descarte_por_produto),
    ("Datas de cadastro e execução coerentes", _datas),
    (f"Idade mínima de {IDADE_MINIMA} anos no cadastro", _idade_minima),
    ("Uma estante por cômodo de cada usuário", _estante_por_comodo),
    ("Logs de auditoria coerentes", _logs),
    ("E-mails em minúsculas e únicos sem diferenciar maiúsculas", _emails),
    ("CNPJ e CAS válidos pelo dígito verificador", _cnpj_e_cas),
)


def verificar_regras(
    conn: Connection, settings: Settings, referencia: Referencia
) -> list[ResultadoRegra]:
    """Roda todas as regras e devolve o resultado de cada uma."""
    return [
        ResultadoRegra(nome, regra(conn, tz=settings.timezone, referencia=referencia))
        for nome, regra in REGRAS
    ]


def contagens(conn: Connection) -> dict[str, int]:
    """Número de linhas de cada tabela dos modelos (``seed stats``)."""
    return {
        nome: int(conn.execute(select(func.count()).select_from(tabela)).scalar_one())
        for nome, tabela in Base.metadata.tables.items()
    }
