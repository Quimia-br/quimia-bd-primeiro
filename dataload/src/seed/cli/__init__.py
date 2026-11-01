"""Linha de comando do seed (Typer).

Comandos: ``check``, ``validate``, ``run``, ``reset``, ``verificar`` e ``stats``.
Opção global ``--target test|main`` (padrão ``test``).

Módulos: ``app`` (Typer, ``--target``, códigos de saída), ``consulta`` (comandos
somente leitura), ``escrita`` (``run`` e ``reset``) e ``auxiliares``.

Travas do alvo ``main`` (garantidas no código e testadas sem banco):

1. qualquer escrita pede para digitar o nome do banco;
2. ``reset`` é bloqueado;
3. dados sintéticos só com ``--allow-synthetic`` e uma segunda confirmação; sem a
   opção, o ``main`` recebe só os tipos de histórico (os produtos do catálogo
   precisam de empresas, que são sintéticas);
4. ``admin_log_edicoes`` nunca recebe dados no ``main``;
5. avisos em vermelho.
"""

from seed.cli import consulta, escrita  # noqa: F401  (registram os comandos no app)
from seed.cli.app import ExitCode, app, console
from seed.cli.auxiliares import connection_hint

__all__ = ["ExitCode", "app", "connection_hint", "console", "main"]


def main() -> None:
    """Ponto de entrada do comando ``seed``."""
    app()
