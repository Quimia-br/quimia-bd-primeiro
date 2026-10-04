"""Isolamento dos testes unitários.

Todo teste unitário roda sem variáveis ``SEED_*`` do ambiente real, numa pasta
temporária (então nunca lê o ``.env.test`` nem o ``.env`` do projeto) e com o
cache de ``get_settings`` limpo. Nenhum teste unitário conecta a banco.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from seed.config import get_settings


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    for name in list(os.environ):
        if name.upper().startswith("SEED_"):
            monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
