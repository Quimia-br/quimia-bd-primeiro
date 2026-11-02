"""Geradores de históricos: tipos_historicos, historicos, historicos_produtos e admin_log_edicoes.

As regras de cada tipo vêm de ``data/reference/tipos_historicos.yaml``:

- ``produtos_min``/``produtos_max``: quantos produtos o histórico tem;
- ``estante_obrigatoria``: o histórico aponta para uma estante do usuário, e os
  produtos dele são produtos guardados nessa estante, com ``data_adicao`` até a data
  do histórico (é o que torna um ARMAZENAMENTO ou uma VERIFICACAO coerentes).

Nos tipos sem estante obrigatória, os produtos são do usuário (``produtos_usuarios``)
e a estante, quando informada, é uma estante dele.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from seed.config import FRACAO_HISTORICO_SEM_DESCRICAO
from seed.contratos import (
    AcaoLog,
    Admin,
    AdminLogEdicao,
    Estante,
    Historico,
    HistoricoProduto,
    ProdutoEstante,
    ProdutoUsuario,
    TipoHistorico,
    Usuario,
)
from seed.dados import Referencia, RegraTipoHistorico
from seed.generators.contexto import Contexto, provisional_id

# Frases neutras e não instrucionais: registram que algo aconteceu, sem descrever
# reações, efeitos nem procedimentos.
DESCRICOES: dict[str, tuple[str, ...]] = {
    "USO": ("Uso registrado.", "Uso registrado pelo usuário.", "Registro de uso concluído."),
    "DESCARTE": ("Descarte registrado.", "Descarte registrado pelo usuário."),
    "ARMAZENAMENTO": ("Produto guardado na estante.", "Armazenamento registrado."),
    "VERIFICACAO": ("Estante verificada.", "Verificação registrada sem observações."),
    "MISTURA": ("Mistura registrada pelo usuário.", "Registro de mistura concluído."),
}
DESCRICAO_PADRAO = ("Registro de histórico concluído.",)


class HistoricoImpossivel(ValueError):
    """As regras não permitem gerar a quantidade pedida (o seed avisa em vez de quebrar)."""


def gerar_tipos(referencia: Referencia) -> list[TipoHistorico]:
    """Os tipos de histórico de ``data/reference`` (sem gerar nada)."""
    return [TipoHistorico(nome=t.nome) for t in referencia.tipos_historicos]


@dataclass
class _Inventario:
    """Produtos de cada usuário e de cada estante, com a data em que foram guardados."""

    estantes_do_usuario: dict[int, list[int]] = field(default_factory=lambda: defaultdict(list))
    produtos_do_usuario: dict[int, list[int]] = field(default_factory=lambda: defaultdict(list))
    produtos_da_estante: dict[int, list[tuple[int, datetime]]] = field(
        default_factory=lambda: defaultdict(list)
    )
    estante_do_produto: dict[tuple[int, int], int] = field(default_factory=dict)


def _inventario(
    estantes: list[Estante], posses: list[ProdutoUsuario], guardados: list[ProdutoEstante]
) -> _Inventario:
    inv = _Inventario()
    for posicao, estante in enumerate(estantes):
        inv.estantes_do_usuario[estante.id_usuario].append(provisional_id(posicao))
    for posse in posses:
        inv.produtos_do_usuario[posse.id_usuario].append(posse.id_produto)
    for guardado in guardados:
        inv.produtos_da_estante[guardado.id_estante].append(
            (guardado.id_produto, guardado.data_adicao)
        )
        dono = estantes[guardado.id_estante - 1].id_usuario
        inv.estante_do_produto[(dono, guardado.id_produto)] = guardado.id_estante
    return inv


def _planejar(
    ctx: Contexto,
    regras: list[RegraTipoHistorico],
    quantidade: int,
    total_produtos: int,
    capacidade_estante: int,
    capacidade_usuario: int,
) -> list[tuple[RegraTipoHistorico, int]]:
    """Escolhe o tipo e o número de produtos de cada histórico, somando ``total_produtos``."""

    def teto(regra: RegraTipoHistorico) -> int:
        disponivel = capacidade_estante if regra.estante_obrigatoria else capacidade_usuario
        return min(regra.produtos_max, disponivel)

    viaveis = [r for r in regras if r.produtos_min <= teto(r)]
    if not viaveis:
        msg = "nenhum tipo de histórico é viável com os produtos e estantes gerados"
        raise HistoricoImpossivel(msg)

    tipos = [ctx.rng.choice(viaveis) for _ in range(quantidade)]
    menor_minimo = min(viaveis, key=lambda r: r.produtos_min)
    maior_teto = max(viaveis, key=teto)
    # Ajusta a mistura de tipos até a soma pedida caber entre os mínimos e os tetos.
    for _ in range(quantidade * 2):
        soma_min = sum(t.produtos_min for t in tipos)
        soma_teto = sum(teto(t) for t in tipos)
        if soma_min > total_produtos:
            i = max(range(quantidade), key=lambda k: (tipos[k].produtos_min, -k))
            tipos[i] = menor_minimo
        elif soma_teto < total_produtos:
            i = min(range(quantidade), key=lambda k: (teto(tipos[k]), k))
            tipos[i] = maior_teto
        else:
            break
    soma_min = sum(t.produtos_min for t in tipos)
    soma_teto = sum(teto(t) for t in tipos)
    if not soma_min <= total_produtos <= soma_teto:
        msg = (
            f"as regras dos tipos de histórico não permitem {quantidade} históricos com "
            f"exatamente {total_produtos} produtos (mínimo {soma_min}, máximo {soma_teto})"
        )
        raise HistoricoImpossivel(msg)

    contagens = [t.produtos_min for t in tipos]
    restantes = total_produtos - soma_min
    while restantes > 0:
        i = ctx.rng.choice([k for k in range(quantidade) if contagens[k] < teto(tipos[k])])
        contagens[i] += 1
        restantes -= 1
    return list(zip(tipos, contagens, strict=True))


def gerar_historicos(
    ctx: Contexto,
    quantidade: int,
    quantidade_produtos: int,
    referencia: Referencia,
    usuarios: list[Usuario],
    estantes: list[Estante],
    posses: list[ProdutoUsuario],
    guardados: list[ProdutoEstante],
) -> tuple[list[Historico], list[HistoricoProduto]]:
    """``quantidade`` históricos com exatamente ``quantidade_produtos`` produtos no total."""
    inv = _inventario(estantes, posses, guardados)
    id_tipo = {t.nome: provisional_id(i) for i, t in enumerate(referencia.tipos_historicos)}
    capacidade_estante = max((len(v) for v in inv.produtos_da_estante.values()), default=0)
    capacidade_usuario = max((len(v) for v in inv.produtos_do_usuario.values()), default=0)
    plano = _planejar(
        ctx,
        referencia.tipos_historicos,
        quantidade,
        quantidade_produtos,
        capacidade_estante,
        capacidade_usuario,
    )

    historicos: list[Historico] = []
    vinculos: list[HistoricoProduto] = []
    for regra, n_produtos in plano:
        if regra.estante_obrigatoria:
            opcoes = [e for e, itens in inv.produtos_da_estante.items() if len(itens) >= n_produtos]
            if n_produtos == 0:
                opcoes = [provisional_id(i) for i in range(len(estantes))]
            if not opcoes:
                msg = f"não há estante com {n_produtos} produtos para um histórico {regra.nome}"
                raise HistoricoImpossivel(msg)
            estante_escolhida = ctx.rng.choice(sorted(opcoes))
            id_estante: int | None = estante_escolhida
            id_usuario = estantes[estante_escolhida - 1].id_usuario
            escolhidos = ctx.rng.sample(inv.produtos_da_estante[estante_escolhida], k=n_produtos)
            produtos = [p for p, _ in escolhidos]
            inicio = max([usuarios[id_usuario - 1].data_cadastro, *(d for _, d in escolhidos)])
        else:
            donos = [u for u, ps in inv.produtos_do_usuario.items() if len(ps) >= n_produtos]
            if n_produtos == 0:
                donos = [provisional_id(i) for i in range(len(usuarios))]
            if not donos:
                msg = f"não há usuário com {n_produtos} produtos para um histórico {regra.nome}"
                raise HistoricoImpossivel(msg)
            id_usuario = ctx.rng.choice(sorted(donos))
            produtos = ctx.rng.sample(inv.produtos_do_usuario[id_usuario], k=n_produtos)
            id_estante = _estante_opcional(ctx, inv, id_usuario, produtos)
            inicio = usuarios[id_usuario - 1].data_cadastro

        descricao = None
        if ctx.rng.random() >= FRACAO_HISTORICO_SEM_DESCRICAO:
            descricao = ctx.rng.choice(DESCRICOES.get(regra.nome, DESCRICAO_PADRAO))
        historicos.append(
            Historico(
                id_estante=id_estante,
                id_usuario=id_usuario,
                id_tipo_historico=id_tipo[regra.nome],
                data_execucao=ctx.momento_entre(inicio),
                descricao_resultado=descricao,
            )
        )
        id_historico = len(historicos)
        vinculos.extend(
            HistoricoProduto(id_produto=p, id_historico=id_historico, id_usuario=id_usuario)
            for p in produtos
        )
    return historicos, vinculos


def _estante_opcional(
    ctx: Contexto, inv: _Inventario, id_usuario: int, produtos: list[int]
) -> int | None:
    """Estante de um histórico em que ela é opcional: às vezes nenhuma.

    Com um produto só, prefere a estante onde ele está guardado; senão, qualquer
    estante do usuário.
    """
    estantes = inv.estantes_do_usuario.get(id_usuario, [])
    if not estantes or ctx.rng.random() < 0.5:
        return None
    if len(produtos) == 1 and (id_usuario, produtos[0]) in inv.estante_do_produto:
        return inv.estante_do_produto[(id_usuario, produtos[0])]
    return ctx.rng.choice(estantes)


def gerar_logs(
    ctx: Contexto,
    quantidade: int,
    admins: list[Admin],
    criacao_por_tabela: dict[str, list[datetime | None]],
) -> list[AdminLogEdicao]:
    """Logs de INSERT: um por registro sorteado, sem repetir registro.

    ``criacao_por_tabela`` traz, para cada tabela auditável, o momento de criação de
    cada linha (posição = ID provisório - 1), ou ``None`` se a tabela não guarda data.
    Com data, ``data_edicao`` é igual a ela e o admin já estava cadastrado; sem data,
    ``data_edicao`` fica entre o cadastro do admin e o momento da carga.
    """
    candidatos: list[tuple[str, int, datetime | None]] = [
        (tabela, provisional_id(posicao), criacao)
        for tabela, criacoes in criacao_por_tabela.items()
        for posicao, criacao in enumerate(criacoes)
    ]
    ctx.rng.shuffle(candidatos)
    cadastros = [a.data_cadastro for a in admins]

    logs: list[AdminLogEdicao] = []
    for tabela, id_registro, criacao in candidatos:
        if len(logs) == quantidade:
            break
        if criacao is None:
            id_admin = provisional_id(ctx.rng.randrange(len(admins)))
            data_edicao = ctx.momento_entre(cadastros[id_admin - 1])
        else:
            aptos = [i for i, c in enumerate(cadastros) if c <= criacao]
            if not aptos:
                continue
            id_admin = provisional_id(ctx.rng.choice(aptos))
            data_edicao = criacao
        logs.append(
            AdminLogEdicao(
                id_admin=id_admin,
                tabela_afetada=tabela,
                id_registro=id_registro,
                acao=AcaoLog.INSERT,
                dado_anterior=None,
                data_edicao=data_edicao,
            )
        )
    if len(logs) < quantidade:
        msg = f"só há {len(logs)} registros auditáveis compatíveis para {quantidade} logs"
        raise HistoricoImpossivel(msg)
    return logs
