"""Comparação de nomes de fuso horário."""

from typing import Final

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
