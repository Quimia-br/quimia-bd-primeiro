"""Geradores de estantes: estantes e produtos_estantes."""

from collections import defaultdict

from seed.contratos import Estante, ProdutoEstante, ProdutoUsuario, Usuario
from seed.generators.contexto import Contexto, provisional_id

ESTANTES_POR_DONO: tuple[int, int] = (1, 3)
ESTANTES_POR_OUTRO_USUARIO: tuple[int, int] = (1, 2)


def gerar_estantes(
    ctx: Contexto,
    quantidade: int,
    quantidade_usuarios: int,
    posses: list[ProdutoUsuario],
    comodos: list[str],
) -> list[Estante]:
    """Estantes com no máximo uma por cômodo de cada usuário.

    Todo usuário que tem produtos recebe pelo menos uma estante (os produtos dele são
    guardados lá); as estantes restantes vão para outros usuários, ainda vazias.
    """
    donos = sorted({p.id_usuario for p in posses})
    limite = len(comodos)
    if len(donos) > quantidade:
        msg = f"{len(donos)} donos de produtos precisam de estante, mas só há {quantidade} estantes"
        raise ValueError(msg)
    if quantidade > quantidade_usuarios * limite:
        msg = (
            f"{quantidade} estantes não cabem em {quantidade_usuarios} usuários × {limite} cômodos"
        )
        raise ValueError(msg)

    por_usuario: dict[int, int] = {}
    restantes = quantidade
    for posicao, dono in enumerate(donos):
        # Reserva uma estante para cada dono que ainda não foi atendido.
        reservadas = len(donos) - posicao - 1
        maximo = min(ESTANTES_POR_DONO[1], restantes - reservadas, limite)
        por_usuario[dono] = ctx.rng.randint(ESTANTES_POR_DONO[0], maximo)
        restantes -= por_usuario[dono]

    outros = [
        provisional_id(u)
        for u in range(quantidade_usuarios)
        if provisional_id(u) not in por_usuario
    ]
    ctx.rng.shuffle(outros)
    while restantes > 0:
        candidatos = outros or [u for u in por_usuario if por_usuario[u] < limite]
        usuario = candidatos.pop(0) if outros else ctx.rng.choice(candidatos)
        atual = por_usuario.get(usuario, 0)
        extra = min(ctx.rng.randint(*ESTANTES_POR_OUTRO_USUARIO), restantes, limite - atual)
        por_usuario[usuario] = atual + extra
        restantes -= extra

    estantes = []
    for usuario in sorted(por_usuario):
        for comodo in ctx.rng.sample(comodos, k=por_usuario[usuario]):
            estantes.append(Estante(id_usuario=usuario, comodo=comodo))
    return estantes


def gerar_produtos_estantes(
    ctx: Contexto,
    estantes: list[Estante],
    posses: list[ProdutoUsuario],
    usuarios: list[Usuario],
) -> list[ProdutoEstante]:
    """Cada produto possuído fica numa estante do próprio dono (uma linha por posse).

    ``data_adicao`` fica entre o cadastro do dono e o momento da carga.
    """
    estantes_do_usuario: dict[int, list[int]] = defaultdict(list)
    for posicao, estante in enumerate(estantes):
        estantes_do_usuario[estante.id_usuario].append(provisional_id(posicao))

    linhas = []
    for posse in posses:
        opcoes = estantes_do_usuario.get(posse.id_usuario)
        if not opcoes:
            msg = f"o usuário {posse.id_usuario} tem produtos, mas nenhuma estante"
            raise ValueError(msg)
        cadastro = usuarios[posse.id_usuario - 1].data_cadastro
        linhas.append(
            ProdutoEstante(
                id_estante=ctx.rng.choice(opcoes),
                id_produto=posse.id_produto,
                data_adicao=ctx.momento_entre(cadastro),
            )
        )
    return linhas
