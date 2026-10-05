"""Leitura e validação dos dados de ``data/reference`` (YAML) e ``data/catalog`` (JSON).

Nada aqui conecta ao banco. Os erros dizem o arquivo e o caminho do campo com problema
(por exemplo, ``produtos.json: produtos[12].cas_number``) e, em erro de sintaxe do YAML,
a linha.
"""

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any, Final, Self

import yaml
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationError,
    model_validator,
)

from seed import validacao
from seed.config import DATA_DIR, Target
from seed.contratos import Codigo
from seed.modelos import table_names

PENDENTE_REVISAO: Final = "pendente de revisão"
PENDENTE_CONFERENCIA: Final = "pendente de conferência"


class DadosError(Exception):
    """Arquivo de dados ausente ou inválido. A mensagem diz o arquivo e o campo."""


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


Cep = Annotated[str, AfterValidator(validacao.validar_cep)]
TextoCatalogo = Annotated[str, Field(min_length=1)]


# ---------------------------------------------------------------------------
# data/reference
# ---------------------------------------------------------------------------


class RegraTipoHistorico(_Modelo):
    """Tipo de histórico e a regra de produtos e estante (``tipos_historicos.yaml``)."""

    nome: Codigo
    produtos_min: Annotated[int, Field(ge=0)]
    produtos_max: Annotated[int, Field(ge=0)]
    estante_obrigatoria: bool

    @model_validator(mode="after")
    def _limits(self) -> Self:
        if self.produtos_max < self.produtos_min:
            msg = "produtos_max precisa ser maior ou igual a produtos_min"
            raise ValueError(msg)
        return self


class Cidade(_Modelo):
    """Cidade com faixa de CEP e coordenadas do centro (``cidades.yaml``)."""

    nome: Annotated[str, Field(min_length=1)]
    uf: Annotated[str, Field(pattern=r"^[A-Z]{2}$")]
    cep_inicio: Cep
    cep_fim: Cep
    latitude: Decimal
    longitude: Decimal

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.cep_fim < self.cep_inicio:
            msg = "cep_fim precisa ser maior ou igual a cep_inicio"
            raise ValueError(msg)
        if not validacao.coordenadas_no_brasil(self.latitude, self.longitude):
            msg = "as coordenadas da cidade precisam estar dentro do Brasil"
            raise ValueError(msg)
        return self


def _unique(values: list[str], what: str) -> None:
    repeated = sorted({v for v in values if values.count(v) > 1})
    if repeated:
        msg = f"{what} repetidos: {', '.join(repeated)}"
        raise ValueError(msg)


class Referencia(_Modelo):
    """Todos os dados de referência, já validados."""

    tipos_historicos: Annotated[list[RegraTipoHistorico], Field(min_length=1)]
    comodos: Annotated[list[Codigo], Field(min_length=1)]
    cidades: Annotated[list[Cidade], Field(min_length=1)]
    raio_graus: Annotated[Decimal, Field(gt=0, le=Decimal("0.5"))]
    tabelas_auditaveis: Annotated[list[str], Field(min_length=1)]

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        _unique([t.nome for t in self.tipos_historicos], "tipos de histórico")
        _unique(list(self.comodos), "cômodos")
        _unique([f"{c.nome}/{c.uf}" for c in self.cidades], "cidades")
        desconhecidas = sorted(set(self.tabelas_auditaveis) - table_names())
        if desconhecidas:
            msg = f"tabelas auditáveis que não existem nos modelos: {', '.join(desconhecidas)}"
            raise ValueError(msg)
        for cidade in self.cidades:
            borda = [
                (cidade.latitude + dl, cidade.longitude + dg)
                for dl in (-self.raio_graus, self.raio_graus)
                for dg in (-self.raio_graus, self.raio_graus)
            ]
            if not all(validacao.coordenadas_no_brasil(lat, lon) for lat, lon in borda):
                msg = f"o raio de {cidade.nome} sai do Brasil; reduza raio_graus"
                raise ValueError(msg)
        return self

    def regra(self, nome_tipo: str) -> RegraTipoHistorico:
        """Regra de um tipo de histórico pelo nome."""
        for tipo in self.tipos_historicos:
            if tipo.nome == nome_tipo:
                return tipo
        msg = f"tipo de histórico desconhecido: {nome_tipo}"
        raise KeyError(msg)


# ---------------------------------------------------------------------------
# data/catalog
# ---------------------------------------------------------------------------


class EntradaCatalogo(_Modelo):
    """Um produto do catálogo: campos de ``produtos`` e ``descartes_fds`` mais a origem.

    A empresa dona do produto não fica no catálogo: é sorteada pelos geradores.
    """

    substancia: Annotated[str, Field(min_length=1)]
    cas_number: Annotated[str, AfterValidator(validacao.validar_cas)]
    nome: Annotated[str, Field(min_length=1, max_length=150)]
    marca: Annotated[str, Field(min_length=1, max_length=150)]
    instrucao_de_uso: TextoCatalogo
    dosagem_tecnica: TextoCatalogo
    metodo_descarte_produto: TextoCatalogo | None
    metodo_descarte_embalagem: TextoCatalogo | None
    restricao_descarte: TextoCatalogo | None
    precaucao_ambiental: TextoCatalogo | None
    fonte: Annotated[str, Field(min_length=1)]
    data_consulta: date | None
    revisado: bool

    @model_validator(mode="after")
    def _review(self) -> Self:
        if not self.revisado:
            return self
        if self.fonte == PENDENTE_CONFERENCIA or self.data_consulta is None:
            msg = "entrada revisada precisa de fonte conferida e data_consulta"
            raise ValueError(msg)
        pendentes = [
            campo
            for campo in (
                "instrucao_de_uso",
                "dosagem_tecnica",
                "metodo_descarte_produto",
                "metodo_descarte_embalagem",
                "restricao_descarte",
                "precaucao_ambiental",
            )
            if getattr(self, campo) == PENDENTE_REVISAO
        ]
        if pendentes:
            msg = f"entrada revisada ainda tem campos pendentes: {', '.join(pendentes)}"
            raise ValueError(msg)
        return self


class Catalogo(_Modelo):
    """Catálogo completo (``produtos.json``)."""

    aviso: Annotated[str, Field(alias="_aviso")] = ""
    produtos: Annotated[list[EntradaCatalogo], Field(min_length=1)]

    @model_validator(mode="after")
    def _unique_keys(self) -> Self:
        # cas_number é UNIQUE em produtos: é a chave natural de cada entrada.
        _unique([p.cas_number for p in self.produtos], "CAS")
        _unique([p.nome for p in self.produtos], "nomes de produto")
        return self

    @property
    def revisados(self) -> list[EntradaCatalogo]:
        return [p for p in self.produtos if p.revisado]

    def para_alvo(self, target: Target) -> list[EntradaCatalogo]:
        """Entradas permitidas no alvo: no ``main``, só as revisadas."""
        return self.revisados if target is Target.MAIN else list(self.produtos)


# ---------------------------------------------------------------------------
# Carga dos arquivos
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Dados:
    """Referência e catálogo carregados e validados."""

    referencia: Referencia
    catalogo: Catalogo


def carregar_referencia(pasta: Path | None = None) -> Referencia:
    """Lê os YAML de ``data/reference`` e valida o conjunto."""
    pasta = pasta or DATA_DIR / "reference"
    tipos = _yaml(pasta / "tipos_historicos.yaml")
    cidades = _yaml(pasta / "cidades.yaml")
    bruto = {
        "tipos_historicos": tipos.get("tipos"),
        "comodos": _yaml(pasta / "comodos.yaml").get("comodos"),
        "cidades": cidades.get("cidades"),
        "raio_graus": cidades.get("raio_graus"),
        "tabelas_auditaveis": _yaml(pasta / "auditoria.yaml").get("tabelas"),
    }
    return _validate(TypeAdapter(Referencia), bruto, pasta.name)


def carregar_catalogo(pasta: Path | None = None) -> Catalogo:
    """Lê ``data/catalog/produtos.json`` e valida cada entrada."""
    arquivo = (pasta or DATA_DIR / "catalog") / "produtos.json"
    try:
        bruto = json.loads(_read(arquivo))
    except json.JSONDecodeError as exc:
        msg = f"{arquivo.name}: JSON inválido na linha {exc.lineno}, coluna {exc.colno}: {exc.msg}"
        raise DadosError(msg) from None
    return _validate(TypeAdapter(Catalogo), bruto, arquivo.name)


def carregar_dados(pasta: Path | None = None) -> Dados:
    """Carrega ``data/reference`` e ``data/catalog``."""
    raiz = pasta or DATA_DIR
    return Dados(carregar_referencia(raiz / "reference"), carregar_catalogo(raiz / "catalog"))


def _read(arquivo: Path) -> str:
    try:
        return arquivo.read_text(encoding="utf-8")
    except FileNotFoundError:
        msg = f"arquivo não encontrado: {arquivo}"
        raise DadosError(msg) from None


def _yaml(arquivo: Path) -> dict[str, Any]:
    try:
        conteudo = yaml.safe_load(_read(arquivo))
    except yaml.MarkedYAMLError as exc:
        linha = exc.problem_mark.line + 1 if exc.problem_mark else "?"
        msg = f"{arquivo.name}: YAML inválido na linha {linha}: {exc.problem}"
        raise DadosError(msg) from None
    if not isinstance(conteudo, dict):
        msg = f"{arquivo.name}: o arquivo precisa ter chaves no primeiro nível"
        raise DadosError(msg)
    return conteudo


def _validate[T](adapter: TypeAdapter[T], bruto: object, origem: str) -> T:
    try:
        return adapter.validate_python(bruto)
    except ValidationError as exc:
        linhas = [f"{origem}: dados inválidos"]
        for erro in exc.errors(include_url=False):
            linhas.append(f"  - {_path(erro['loc'])}: {erro['msg']}")
        raise DadosError("\n".join(linhas)) from None


def _path(loc: tuple[int | str, ...]) -> str:
    caminho = ""
    for parte in loc:
        caminho += f"[{parte}]" if isinstance(parte, int) else f".{parte}"
    return caminho.lstrip(".") or "(raiz)"
