from datetime import date
from decimal import Decimal

import pytest

from seed.validacao import (
    cas_digito,
    cas_valido,
    cep_valido,
    cnpj_digitos,
    cnpj_valido,
    coordenadas_no_brasil,
    idade_em,
    url_https_valida,
    validar_cas,
    validar_cnpj,
)

# ------------------------------------------------------------------ CAS


@pytest.mark.parametrize(
    "cas",
    [
        "64-17-5",  # etanol
        "7732-18-5",  # água
        "7681-52-9",  # hipoclorito de sódio
        "1310-73-2",  # hidróxido de sódio
        "67-63-0",  # isopropanol
        "7647-01-0",  # ácido clorídrico
        "151-21-3",  # dodecilsulfato de sódio
        "5989-27-5",  # D-limoneno
    ],
)
def test_real_cas_numbers_are_valid(cas: str) -> None:
    assert cas_valido(cas)
    assert validar_cas(cas) == cas


@pytest.mark.parametrize(
    "cas",
    [
        "64-17-4",  # dígito errado
        "7732-18-6",  # dígito errado
        "6417-5",  # sem o grupo do meio
        "1-17-5",  # primeiro grupo curto
        "12345678-17-5",  # primeiro grupo longo
        "64-1-5",  # grupo do meio curto
        "64175",  # sem hífens
        " 64-17-5",  # espaço
        "AB-17-5",  # letras
        "",
    ],
)
def test_invalid_cas_numbers(cas: str) -> None:
    assert not cas_valido(cas)
    with pytest.raises(ValueError, match="CAS inválido"):
        validar_cas(cas)


def test_cas_digit() -> None:
    # 7732-18-5: 8×1 + 1×2 + 2×3 + 3×4 + 7×5 + 7×6 = 105 → 5
    assert cas_digito("773218") == 5


# ------------------------------------------------------------------ CNPJ


@pytest.mark.parametrize(
    "cnpj",
    [
        "11222333000181",  # numérico
        "11444777000161",  # numérico
        "12ABC34501DE35",  # exemplo oficial da Receita Federal (12.ABC.345/01DE-35)
    ],
)
def test_valid_cnpjs(cnpj: str) -> None:
    assert cnpj_valido(cnpj)
    assert validar_cnpj(cnpj) == cnpj


def test_official_alphanumeric_example_digits() -> None:
    assert cnpj_digitos("12ABC34501DE") == "35"


@pytest.mark.parametrize(
    "cnpj",
    [
        "11222333000182",  # segundo dígito errado
        "12ABC34501DE36",  # dígito errado no alfanumérico
        "12ABC34501DEAB",  # verificadores precisam ser numéricos
        "12abc34501de35",  # letras minúsculas não são aceitas
        "11.222.333/0001-81",  # com máscara
        "1122233300018",  # 13 caracteres
        "00000000000000",  # todos iguais
        "",
    ],
)
def test_invalid_cnpjs(cnpj: str) -> None:
    assert not cnpj_valido(cnpj)
    with pytest.raises(ValueError, match="CNPJ inválido"):
        validar_cnpj(cnpj)


def test_cnpj_digits_rejects_bad_base() -> None:
    with pytest.raises(ValueError, match="12 caracteres"):
        cnpj_digitos("12abc34501de")


# ------------------------------------------------------------------ CEP, URL, coordenadas


@pytest.mark.parametrize(("cep", "valido"), [("01310100", True), ("01310-100", False),
                                             ("1310100", False), ("0131010A", False)])  # fmt: skip
def test_cep(cep: str, valido: bool) -> None:
    assert cep_valido(cep) is valido


@pytest.mark.parametrize(
    ("url", "valida"),
    [
        ("https://randomuser.me/api/portraits/women/1.jpg", True),
        ("https://ui-avatars.com/api/?name=Limpa%20Bem&size=256", True),
        ("http://randomuser.me/api/portraits/women/1.jpg", False),
        ("https://", False),
        ("https://exemplo.com/foto com espaço.jpg", False),
        ("ftp://exemplo.com/a.jpg", False),
    ],
)
def test_url_https(url: str, valida: bool) -> None:
    assert url_https_valida(url) is valida


@pytest.mark.parametrize(
    ("latitude", "longitude", "dentro"),
    [
        ("-23.550520", "-46.633308", True),  # São Paulo
        ("-3.731862", "-38.526669", True),  # Fortaleza
        ("-30.034647", "-51.217658", True),  # Porto Alegre
        ("40.712776", "-74.005974", False),  # Nova York
        ("-46.633308", "-23.550520", False),  # latitude e longitude trocadas
    ],
)
def test_coordinates_in_brazil(latitude: str, longitude: str, dentro: bool) -> None:
    assert coordenadas_no_brasil(Decimal(latitude), Decimal(longitude)) is dentro


# ------------------------------------------------------------------ idade


@pytest.mark.parametrize(
    ("nascimento", "referencia", "idade"),
    [
        (date(2006, 5, 10), date(2024, 5, 10), 18),  # aniversário no dia
        (date(2006, 5, 10), date(2024, 5, 9), 17),  # véspera
        (date(2004, 2, 29), date(2022, 2, 28), 17),  # nascido em 29/02
        (date(2004, 2, 29), date(2022, 3, 1), 18),
    ],
)
def test_age_at(nascimento: date, referencia: date, idade: int) -> None:
    assert idade_em(nascimento, referencia) == idade
