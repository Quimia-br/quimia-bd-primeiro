"""Contratos Pydantic: alinhamento com os modelos/DDL e regras de cada tabela."""

import json
import re
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any, get_args

import annotated_types
import pytest
from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo
from sqlalchemy import String

from seed.contratos import (
    CONTRATOS,
    AcaoLog,
    AdminLogEdicao,
    Localizacao,
    PorteEmpresa,
    Produto,
    StatusConta,
    Usuario,
    UsuarioEmpresa,
)
from seed.modelos import Base
from tests.conftest import SQL_DIR

AGORA = datetime(2026, 1, 15, 14, 30, tzinfo=UTC)
DDL = (SQL_DIR / "01_ddl.sql").read_text(encoding="utf-8")


def _constraints(annotation: object) -> list[object]:
    """Metadados de um tipo, inclusive dentro de ``Annotated[...] | None``."""
    found: list[object] = []
    for arg in get_args(annotation):
        if isinstance(arg, FieldInfo):
            found.extend(arg.metadata)
        else:
            found.extend(_constraints(arg))
    return found


def _max_length(contract: type[BaseModel], field: str) -> int | None:
    info = contract.model_fields[field]
    metadata = [*info.metadata, *_constraints(info.annotation)]
    lengths = [m.max_length for m in metadata if isinstance(m, annotated_types.MaxLen)]
    return lengths[0] if lengths else None


# ------------------------------------------------------------------ alinhamento com o modelo


def test_every_table_has_a_contract() -> None:
    assert set(CONTRATOS) == set(Base.metadata.tables)


@pytest.mark.parametrize("table_name", sorted(CONTRATOS))
def test_contract_fields_match_model_columns(table_name: str) -> None:
    table = Base.metadata.tables[table_name]
    identity = {c.name for c in table.columns if c.identity is not None}
    expected = [c.name for c in table.columns if c.name not in identity]

    assert list(CONTRATOS[table_name].model_fields) == expected


@pytest.mark.parametrize("table_name", sorted(CONTRATOS))
def test_contract_max_length_matches_column_size(table_name: str) -> None:
    contract = CONTRATOS[table_name]
    for column in Base.metadata.tables[table_name].columns:
        if column.name not in contract.model_fields:
            continue
        size = column.type.length if isinstance(column.type, String) else None
        assert _max_length(contract, column.name) == size, f"{table_name}.{column.name}"


@pytest.mark.parametrize("table_name", sorted(CONTRATOS))
def test_optional_fields_match_nullable_columns(table_name: str) -> None:
    contract = CONTRATOS[table_name]
    for column in Base.metadata.tables[table_name].columns:
        if column.name not in contract.model_fields:
            continue
        accepts_none = not contract.model_fields[column.name].is_required() or (
            "None" in str(contract.model_fields[column.name].annotation)
        )
        assert accepts_none is bool(column.nullable), f"{table_name}.{column.name}"


@pytest.mark.parametrize(
    ("enum", "column"),
    [(StatusConta, "status"), (PorteEmpresa, "porte"), (AcaoLog, "acao")],
)
def test_enums_match_ddl_checks(enum: type[StrEnum], column: str) -> None:
    checks = re.findall(rf"CHECK\s*\(\s*{column} IN \(([^)]*)\)", DDL)
    assert checks, f"CHECK de {column} não encontrado no DDL"
    for check in checks:
        values = {v.strip().strip("'") for v in check.split(",")}
        assert values == {e.value for e in enum}


# ------------------------------------------------------------------ regras por tabela


def _empresa(**overrides: Any) -> dict[str, Any]:
    return {
        "cnpj": "12ABC34501DE35",
        "nome": "Limpa Bem Ltda",
        "email": "contato@example.com",
        "porte": "MICRO",
        "data_cadastro": AGORA,
        "senha_hash": "$argon2id$v=19$hash-ficticio",
        "status": "ATIVO",
        "url_foto": "https://ui-avatars.com/api/?name=Limpa%20Bem&size=256",
        **overrides,
    }


def _usuario(**overrides: Any) -> dict[str, Any]:
    return {
        "nome": "Ana Souza",
        "data_nascimento": date(1990, 3, 1),
        "email": "ana.souza@example.org",
        "data_cadastro": AGORA,
        "senha_hash": "$argon2id$v=19$hash-ficticio",
        "status": "ATIVO",
        "url_foto": "https://randomuser.me/api/portraits/women/12.jpg",
        **overrides,
    }


def test_valid_company() -> None:
    empresa = UsuarioEmpresa.model_validate(_empresa())
    assert empresa.porte is PorteEmpresa.MICRO


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("cnpj", "12ABC34501DE36", "CNPJ inválido"),
        ("nome", "x" * 151, "at most 150"),
        ("email", "contato@empresa.com.br", "domínios"),
        ("email", "Contato@example.com", "minúsculas"),
        ("porte", "ENORME", "PEQUENO"),
        ("status", "ativo", "ATIVO"),
        ("url_foto", "http://ui-avatars.com/api/?name=X", "https://"),
        ("data_cadastro", datetime(2026, 1, 15, 14, 30), "timezone"),  # sem fuso
        ("data_cadastro", datetime.now(UTC) + timedelta(days=1), "futuro"),
    ],
)
def test_invalid_company(field: str, value: object, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        UsuarioEmpresa.model_validate(_empresa(**{field: value}))


def test_extra_field_is_rejected() -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        UsuarioEmpresa.model_validate(_empresa(id_usuario_empresa=1))


def test_user_minimum_age_is_checked_at_signup_date() -> None:
    cadastro = datetime(2024, 5, 10, 12, 0, tzinfo=UTC)

    Usuario.model_validate(_usuario(data_nascimento=date(2006, 5, 10), data_cadastro=cadastro))
    with pytest.raises(ValidationError, match="pelo menos 18 anos"):
        Usuario.model_validate(_usuario(data_nascimento=date(2006, 5, 11), data_cadastro=cadastro))


def test_user_age_uses_generation_timezone() -> None:
    # 02:00 UTC de 10/05 ainda é 09/05 em São Paulo: o usuário ainda tem 17 anos.
    cadastro = datetime(2024, 5, 10, 2, 0, tzinfo=UTC)
    with pytest.raises(ValidationError, match="pelo menos 18 anos"):
        Usuario.model_validate(_usuario(data_nascimento=date(2006, 5, 10), data_cadastro=cadastro))


def test_user_without_birth_date_is_accepted() -> None:
    assert Usuario.model_validate(_usuario(data_nascimento=None)).data_nascimento is None


def test_product_requires_valid_cas() -> None:
    base = {
        "id_usuario_empresa": 1,
        "nome": "Álcool 70%",
        "marca": "Marca Fictícia",
        "instrucao_de_uso": "pendente de revisão",
        "dosagem_tecnica": "pendente de revisão",
    }
    assert Produto.model_validate({**base, "cas_number": "64-17-5"}).cas_number == "64-17-5"
    with pytest.raises(ValidationError, match="CAS inválido"):
        Produto.model_validate({**base, "cas_number": "64-17-4"})
    with pytest.raises(ValidationError, match="greater than 0"):
        Produto.model_validate({**base, "cas_number": "64-17-5", "id_usuario_empresa": 0})


@pytest.mark.parametrize(
    ("latitude", "longitude", "message"),
    [
        (Decimal("-23.550520"), None, "juntas"),
        (Decimal("40.712776"), Decimal("-74.005974"), "Brasil"),
        (Decimal("-23.5505201"), Decimal("-46.633308"), "decimal places"),
    ],
)
def test_invalid_location(latitude: Decimal, longitude: Decimal | None, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        Localizacao.model_validate(
            {"id_usuario": 1, "cep": "01310100", "latitude": latitude, "longitude": longitude}
        )


def test_location_without_coordinates_is_accepted() -> None:
    local = Localizacao.model_validate(
        {"id_usuario": 1, "cep": "01310100", "latitude": None, "longitude": None}
    )
    assert local.latitude is None


def _log(**overrides: Any) -> dict[str, Any]:
    return {
        "id_admin": 1,
        "tabela_afetada": "usuarios",
        "id_registro": 10,
        "acao": "INSERT",
        "dado_anterior": None,
        "data_edicao": AGORA,
        **overrides,
    }


def test_log_insert_has_no_previous_data() -> None:
    assert AdminLogEdicao.model_validate(_log()).dado_anterior is None
    with pytest.raises(ValidationError, match="precisa ser nulo"):
        AdminLogEdicao.model_validate(_log(dado_anterior='{"nome": "Ana"}'))


def test_log_update_requires_json_object() -> None:
    anterior = json.dumps({"nome": "Ana", "status": "ATIVO"}, ensure_ascii=False)
    assert AdminLogEdicao.model_validate(_log(acao="UPDATE", dado_anterior=anterior))
    with pytest.raises(ValidationError, match="linha anterior"):
        AdminLogEdicao.model_validate(_log(acao="UPDATE"))
    with pytest.raises(ValidationError, match="JSON válido"):
        AdminLogEdicao.model_validate(_log(acao="DELETE", dado_anterior="nome=Ana"))
    with pytest.raises(ValidationError, match="objeto JSON"):
        AdminLogEdicao.model_validate(_log(acao="DELETE", dado_anterior="[1, 2]"))
