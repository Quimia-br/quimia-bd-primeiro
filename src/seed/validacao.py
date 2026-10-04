"""Validadores puros: não importam banco, Faker, configuração nem arquivos.

Cada validador tem duas formas:

- ``*_valido(valor) -> bool``: só responde se o valor é válido;
- ``validar_*(valor) -> valor``: devolve o valor normalizado ou levanta ``ValueError``
  com uma mensagem em português (usado pelos contratos Pydantic).
"""

import re
from datetime import date
from decimal import Decimal
from typing import Final

# ---------------------------------------------------------------------------
# CAS number
# ---------------------------------------------------------------------------

_CAS = re.compile(r"^(\d{2,7})-(\d{2})-(\d)$")
CAS_TAMANHO_MAXIMO: Final = 12


def cas_digito(corpo: str) -> int:
    """Dígito verificador do CAS a partir dos dígitos sem o verificador.

    Cada dígito é multiplicado pela sua posição contada da direita (1, 2, 3...);
    o verificador é a soma módulo 10.
    """
    return sum(posicao * int(d) for posicao, d in enumerate(reversed(corpo), start=1)) % 10


def cas_valido(valor: str) -> bool:
    """CAS no formato ``NNNNNNN-NN-N`` com o dígito verificador correto."""
    match = _CAS.fullmatch(valor)
    if match is None or len(valor) > CAS_TAMANHO_MAXIMO:
        return False
    corpo = match.group(1) + match.group(2)
    return cas_digito(corpo) == int(match.group(3))


def validar_cas(valor: str) -> str:
    if not cas_valido(valor):
        msg = "CAS inválido: use o formato NNNNNNN-NN-N com o dígito verificador correto"
        raise ValueError(msg)
    return valor


# ---------------------------------------------------------------------------
# CNPJ (numérico e alfanumérico, formato da Receita Federal em vigor desde 31/07/2026)
# ---------------------------------------------------------------------------

_CNPJ = re.compile(r"^[0-9A-Z]{12}[0-9]{2}$")
_PESOS_DV1: Final = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_PESOS_DV2: Final = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def _dv_cnpj(caracteres: str, pesos: tuple[int, ...]) -> str:
    # Cada caractere vale o código ASCII menos 48 ("0" = 0, "A" = 17, "Z" = 42).
    soma = sum((ord(c) - 48) * peso for c, peso in zip(caracteres, pesos, strict=True))
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def cnpj_digitos(base: str) -> str:
    """Os dois dígitos verificadores para uma base de 12 caracteres ``[0-9A-Z]``."""
    if not re.fullmatch(r"[0-9A-Z]{12}", base):
        msg = "a base do CNPJ precisa ter 12 caracteres entre 0-9 e A-Z"
        raise ValueError(msg)
    dv1 = _dv_cnpj(base, _PESOS_DV1)
    return dv1 + _dv_cnpj(base + dv1, _PESOS_DV2)


def cnpj_valido(valor: str) -> bool:
    """CNPJ de 14 caracteres, sem máscara, com os dígitos verificadores corretos."""
    if not _CNPJ.fullmatch(valor) or len(set(valor)) == 1:
        return False
    return cnpj_digitos(valor[:12]) == valor[12:]


def validar_cnpj(valor: str) -> str:
    if not cnpj_valido(valor):
        msg = (
            "CNPJ inválido: use 14 caracteres sem máscara (12 entre 0-9/A-Z e 2 dígitos) "
            "com os dígitos verificadores corretos"
        )
        raise ValueError(msg)
    return valor


# ---------------------------------------------------------------------------
# CEP, URL e coordenadas
# ---------------------------------------------------------------------------

_CEP = re.compile(r"^\d{8}$")


def cep_valido(valor: str) -> bool:
    """CEP com exatamente 8 dígitos, sem máscara."""
    return bool(_CEP.fullmatch(valor))


def validar_cep(valor: str) -> str:
    if not cep_valido(valor):
        msg = "CEP inválido: use 8 dígitos, sem hífen"
        raise ValueError(msg)
    return valor


def url_https_valida(valor: str) -> bool:
    """URL que começa com ``https://`` e tem um host."""
    return bool(re.fullmatch(r"https://[^\s/?#]+[^\s]*", valor))


def validar_url_https(valor: str) -> str:
    if not url_https_valida(valor):
        msg = "URL inválida: precisa começar com https:// e não pode ter espaços"
        raise ValueError(msg)
    return valor


LATITUDE_BRASIL: Final = (Decimal("-33.8"), Decimal("5.3"))
LONGITUDE_BRASIL: Final = (Decimal("-74.0"), Decimal("-34.8"))


def coordenadas_no_brasil(latitude: Decimal, longitude: Decimal) -> bool:
    """Indica se o ponto está dentro do retângulo que cobre o Brasil."""
    return (
        LATITUDE_BRASIL[0] <= latitude <= LATITUDE_BRASIL[1]
        and LONGITUDE_BRASIL[0] <= longitude <= LONGITUDE_BRASIL[1]
    )


# ---------------------------------------------------------------------------
# Datas e fusos
# ---------------------------------------------------------------------------


def idade_em(nascimento: date, referencia: date) -> int:
    """Idade completa em anos na data de referência."""
    aniversario_passou = (referencia.month, referencia.day) >= (nascimento.month, nascimento.day)
    return referencia.year - nascimento.year - (0 if aniversario_passou else 1)


UTC_ALIASES: Final = frozenset(
    {
        "utc",
        "etc/utc",
        "uct",
        "etc/uct",
        "gmt",
        "etc/gmt",
        "gmt0",
        "etc/gmt0",
        "gmt+0",
        "etc/gmt+0",
        "gmt-0",
        "etc/gmt-0",
        "greenwich",
        "etc/greenwich",
        "universal",
        "etc/universal",
        "zulu",
        "etc/zulu",
    }
)


def same_timezone(first: str, second: str) -> bool:
    """Indica se dois nomes de fuso são o mesmo (``UTC`` e ``Etc/UTC`` são iguais)."""
    a, b = first.strip().lower(), second.strip().lower()
    return a == b or (a in UTC_ALIASES and b in UTC_ALIASES)
