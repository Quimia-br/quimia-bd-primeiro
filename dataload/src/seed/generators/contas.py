"""Geradores de contas: usuarios_empresas, admins, usuarios e localizacoes."""

import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import quote

from pwdlib.hashers.argon2 import Argon2Hasher

from seed import validacao
from seed.config import (
    FOTO_EMPRESA,
    FOTO_USUARIO,
    FOTO_USUARIO_GENEROS,
    FOTO_USUARIO_INDICES,
    FRACAO_CNPJ_ALFANUMERICO,
    FRACAO_LOCALIZACAO_COM_COORDENADAS,
    FRACAO_SEM_DATA_NASCIMENTO,
    IDADE_MAXIMA,
    IDADE_MINIMA,
    JANELA_CADASTRO_DIAS,
)
from seed.contratos import Admin, Localizacao, PorteEmpresa, Usuario, UsuarioEmpresa
from seed.dados import Referencia
from seed.generators.contexto import Contexto, provisional_id

_COORDENADA = Decimal("0.000001")


def gerar_senha_hash(senha: str, rng: random.Random) -> str:
    """Hash argon2 da senha de teste, gerado uma vez por carga e reutilizado.

    O salt vem da semente, para a mesma semente produzir o mesmo hash (determinismo).
    A senha é a mesma para todas as contas sintéticas, então o salt fixo não reduz a
    segurança de nada que já não fosse conhecido.
    """
    return Argon2Hasher().hash(senha, salt=rng.randbytes(16))


def _cadastro(ctx: Contexto) -> datetime:
    return ctx.momento_entre(ctx.agora - timedelta(days=JANELA_CADASTRO_DIAS))


def _cnpj(ctx: Contexto, usados: set[str]) -> str:
    while True:
        if ctx.rng.random() < FRACAO_CNPJ_ALFANUMERICO:
            alfabeto = string.digits + string.ascii_uppercase
        else:
            alfabeto = string.digits
        base = "".join(ctx.rng.choice(alfabeto) for _ in range(12))
        cnpj = base + validacao.cnpj_digitos(base)
        if cnpj not in usados and validacao.cnpj_valido(cnpj):
            usados.add(cnpj)
            return cnpj


def gerar_empresas(ctx: Contexto, quantidade: int, senha_hash: str) -> list[UsuarioEmpresa]:
    """Empresas com CNPJ válido (parte alfanumérica) e avatar com as iniciais."""
    usados: set[str] = set()
    empresas = []
    for indice in range(quantidade):
        nome = ctx.fake.company()[:150]
        empresas.append(
            UsuarioEmpresa(
                cnpj=_cnpj(ctx, usados),
                nome=nome,
                email=ctx.email(nome, indice + 1, prefixo="contato."),
                porte=ctx.rng.choice(list(PorteEmpresa)),
                data_cadastro=_cadastro(ctx),
                senha_hash=senha_hash,
                status=ctx.status(),
                url_foto=FOTO_EMPRESA.format(nome=quote(nome)),
            )
        )
    return empresas


def gerar_admins(ctx: Contexto, quantidade: int, senha_hash: str) -> list[Admin]:
    """Administradores (a tabela não tem foto)."""
    admins = []
    for indice in range(quantidade):
        nome = ctx.fake.name()[:150]
        admins.append(
            Admin(
                nome=nome,
                data_cadastro=_cadastro(ctx),
                email=ctx.email(nome, indice + 1, prefixo="admin."),
                senha_hash=senha_hash,
                status=ctx.status(),
            )
        )
    return admins


def gerar_usuarios(ctx: Contexto, quantidade: int, senha_hash: str) -> list[Usuario]:
    """Usuários: foto do mesmo gênero do nome, sem repetir índice; idade mínima no cadastro.

    Exatamente ``FRACAO_SEM_DATA_NASCIMENTO`` dos usuários ficam sem data de nascimento.
    """
    indices_foto = ctx.rng.sample(list(FOTO_USUARIO_INDICES), k=quantidade)
    sem_nascimento = set(
        ctx.rng.sample(range(quantidade), k=round(quantidade * FRACAO_SEM_DATA_NASCIMENTO))
    )
    usuarios = []
    for indice in range(quantidade):
        genero = ctx.rng.choice(sorted(FOTO_USUARIO_GENEROS))
        primeiro = (
            ctx.fake.first_name_female() if genero == "feminino" else ctx.fake.first_name_male()
        )
        nome = f"{primeiro} {ctx.fake.last_name()}"[:150]
        cadastro = _cadastro(ctx)
        nascimento = None
        if indice not in sem_nascimento:
            dia_cadastro = cadastro.date()
            idade = ctx.rng.randint(IDADE_MINIMA, IDADE_MAXIMA)
            nascimento = dia_cadastro - timedelta(days=idade * 365 + ctx.rng.randint(0, 364))
            while validacao.idade_em(nascimento, dia_cadastro) < IDADE_MINIMA:
                nascimento -= timedelta(days=1)
        usuarios.append(
            Usuario(
                nome=nome,
                data_nascimento=nascimento,
                email=ctx.email(nome, indice + 1),
                data_cadastro=cadastro,
                senha_hash=senha_hash,
                status=ctx.status(),
                url_foto=FOTO_USUARIO.format(
                    genero=FOTO_USUARIO_GENEROS[genero], indice=indices_foto[indice]
                ),
            )
        )
    return usuarios


def gerar_localizacoes(
    ctx: Contexto, usuarios: list[Usuario], referencia: Referencia
) -> list[Localizacao]:
    """Uma localização por usuário (1:1), com CEP dentro da faixa da cidade sorteada."""
    localizacoes = []
    raio = float(referencia.raio_graus)
    for posicao in range(len(usuarios)):
        cidade = ctx.rng.choice(referencia.cidades)
        cep = f"{ctx.rng.randint(int(cidade.cep_inicio), int(cidade.cep_fim)):08d}"
        latitude = longitude = None
        if ctx.rng.random() < FRACAO_LOCALIZACAO_COM_COORDENADAS:
            latitude = (cidade.latitude + Decimal(ctx.rng.uniform(-raio, raio))).quantize(
                _COORDENADA
            )
            longitude = (cidade.longitude + Decimal(ctx.rng.uniform(-raio, raio))).quantize(
                _COORDENADA
            )
        localizacoes.append(
            Localizacao(
                id_usuario=provisional_id(posicao), cep=cep, latitude=latitude, longitude=longitude
            )
        )
    return localizacoes
