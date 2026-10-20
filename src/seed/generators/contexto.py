"""Contexto compartilhado pelos geradores: semente, Faker, momento da carga e utilitários.

Determinismo: tudo o que é sorteado sai de ``ctx.rng`` ou de ``ctx.fake`` (os dois
semeados com a mesma semente), numa ordem fixa. Com a mesma semente e o mesmo
``agora``, os dados gerados são idênticos.

IDs provisórios: os geradores não conhecem os IDs reais (o banco os cria no insert).
Cada linha de uma tabela com identity tem o ID provisório ``posição + 1`` na lista da
sua tabela, e as chaves estrangeiras usam esses IDs. A carga troca pelos IDs reais
devolvidos pelo ``RETURNING``.
"""

import random
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from faker import Faker

from seed.config import EMAIL_DOMINIOS, FUSO_DE_GERACAO, PESOS_STATUS
from seed.contratos import StatusConta


@dataclass
class Contexto:
    """Estado da geração."""

    rng: random.Random
    fake: Faker
    agora: datetime
    zona: ZoneInfo

    @classmethod
    def criar(cls, seed: int, agora: datetime | None = None) -> Contexto:
        """Contexto semeado. ``agora`` precisa ter fuso; o padrão é o momento atual."""
        momento = agora or datetime.now(UTC)
        if momento.tzinfo is None:
            msg = "agora precisa ter fuso horário"
            raise ValueError(msg)
        fake = Faker("pt_BR")
        fake.seed_instance(seed)
        zona = ZoneInfo(FUSO_DE_GERACAO)
        # random.Random é intencional: dados reproduzíveis, não segredos.
        rng = random.Random(seed)  # noqa: S311
        return cls(rng, fake, momento.astimezone(zona).replace(microsecond=0), zona)

    def momento_entre(self, inicio: datetime, fim: datetime | None = None) -> datetime:
        """Momento sorteado entre ``inicio`` e ``fim`` (padrão: agora), no fuso de geração."""
        fim = fim or self.agora
        if fim < inicio:
            msg = "o fim do intervalo é anterior ao início"
            raise ValueError(msg)
        segundos = int((fim - inicio).total_seconds())
        return (inicio + timedelta(seconds=self.rng.randint(0, segundos))).astimezone(self.zona)

    def status(self) -> StatusConta:
        """Status sorteado com os pesos de ``config.PESOS_STATUS``."""
        nomes = list(PESOS_STATUS)
        return StatusConta(self.rng.choices(nomes, weights=list(PESOS_STATUS.values()))[0])

    def email(self, nome: str, indice: int, prefixo: str = "") -> str:
        """E-mail único e em minúsculas num domínio reservado para exemplos."""
        dominio = self.rng.choice(sorted(EMAIL_DOMINIOS))
        return f"{prefixo}{slug(nome)}.{indice}@{dominio}"


def slug(texto: str) -> str:
    """Texto sem acentos, em minúsculas, com pontos no lugar de espaços e símbolos."""
    ascii_ = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    partes = "".join(c if c.isalnum() else " " for c in ascii_.lower()).split()
    return ".".join(partes)[:60] or "conta"


def provisional_id(posicao: int) -> int:
    """ID provisório da linha na posição ``posicao`` (começando em 0) da sua tabela."""
    return posicao + 1
