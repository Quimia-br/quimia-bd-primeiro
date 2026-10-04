"""Geradores de produtos: produtos, descartes_fds e produtos_usuarios."""

from seed.contratos import DescarteFds, Produto, ProdutoUsuario
from seed.dados import EntradaCatalogo
from seed.generators.contexto import Contexto, provisional_id

PRODUTOS_POR_DONO: tuple[int, int] = (2, 4)
"""Quantos produtos cada usuário dono tem (mínimo e máximo).

Os produtos ficam concentrados numa parte dos usuários: com 100 posses para 100
usuários, cada dono precisa de pelo menos 2 produtos para existirem misturas, e os
demais usuários ficam sem produtos (e, portanto, sem históricos com produtos).
"""


def chave_natural_produto(entrada: EntradaCatalogo) -> str:
    """Chave natural de ``produtos``: hoje, o CAS (``cas_number`` é UNIQUE).

    Se o time mudar o UNIQUE (pauta, item 1), basta mudar esta função e o limite em
    ``limite_produtos``; o resto dos geradores e da carga não muda.
    """
    return entrada.cas_number


def limite_produtos(entradas: list[EntradaCatalogo]) -> int:
    """Quantos produtos distintos o catálogo permite (um por chave natural)."""
    return len({chave_natural_produto(e) for e in entradas})


def gerar_produtos(
    ctx: Contexto, entradas: list[EntradaCatalogo], quantidade_empresas: int
) -> list[Produto]:
    """Um produto por entrada do catálogo, com a empresa dona sorteada."""
    if quantidade_empresas < 1:
        msg = "produtos precisam de pelo menos uma empresa"
        raise ValueError(msg)
    return [
        Produto(
            id_usuario_empresa=provisional_id(ctx.rng.randrange(quantidade_empresas)),
            cas_number=entrada.cas_number,
            nome=entrada.nome,
            marca=entrada.marca,
            instrucao_de_uso=entrada.instrucao_de_uso,
            dosagem_tecnica=entrada.dosagem_tecnica,
        )
        for entrada in entradas
    ]


def gerar_descartes(entradas: list[EntradaCatalogo]) -> list[DescarteFds]:
    """Um registro de descarte por produto, com os textos do catálogo (nunca gerados)."""
    return [
        DescarteFds(
            id_produto=provisional_id(posicao),
            metodo_descarte_produto=entrada.metodo_descarte_produto,
            metodo_descarte_embalagem=entrada.metodo_descarte_embalagem,
            restricao_descarte=entrada.restricao_descarte,
            precaucao_ambiental=entrada.precaucao_ambiental,
        )
        for posicao, entrada in enumerate(entradas)
    ]


def gerar_produtos_usuarios(
    ctx: Contexto, quantidade: int, quantidade_usuarios: int, quantidade_produtos: int
) -> list[ProdutoUsuario]:
    """``quantidade`` posses concentradas em donos com 2 a 4 produtos distintos cada."""
    minimo, maximo = PRODUTOS_POR_DONO
    if quantidade_produtos < maximo:
        msg = f"são necessários pelo menos {maximo} produtos para gerar as posses"
        raise ValueError(msg)
    menor_numero_de_donos = -(-quantidade // maximo)  # arredonda para cima
    maior_numero_de_donos = min(quantidade // minimo, quantidade_usuarios)
    if menor_numero_de_donos > maior_numero_de_donos:
        msg = (
            f"não dá para distribuir {quantidade} posses entre {quantidade_usuarios} "
            f"usuários com {minimo} a {maximo} produtos cada"
        )
        raise ValueError(msg)

    centro = (menor_numero_de_donos + maior_numero_de_donos) // 2
    numero_de_donos = ctx.rng.randint(menor_numero_de_donos, max(menor_numero_de_donos, centro))
    donos = ctx.rng.sample(range(quantidade_usuarios), k=numero_de_donos)

    # Todos começam com o mínimo; o restante é distribuído sem passar do máximo.
    por_dono = dict.fromkeys(donos, minimo)
    restantes = quantidade - minimo * numero_de_donos
    while restantes > 0:
        dono = ctx.rng.choice([d for d in donos if por_dono[d] < maximo])
        por_dono[dono] += 1
        restantes -= 1

    posses = []
    for dono in donos:
        for produto in ctx.rng.sample(range(quantidade_produtos), k=por_dono[dono]):
            posses.append(
                ProdutoUsuario(id_produto=provisional_id(produto), id_usuario=provisional_id(dono))
            )
    return posses
