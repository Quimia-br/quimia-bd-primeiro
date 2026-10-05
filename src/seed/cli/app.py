"""Aplicação Typer, opção global ``--target`` e códigos de saída."""

from enum import IntEnum
from typing import Annotated

import typer
from rich.console import Console

from seed.config import Target


class ExitCode(IntEnum):
    """Códigos de saída da CLI."""

    OK = 0
    ERRO = 1
    USO = 2  # usado pelo próprio Typer/Click para opções inválidas
    CONFIGURACAO = 3
    CONEXAO = 4
    DADOS = 5
    SCHEMA = 6
    BLOQUEADO = 7
    REGRAS = 8


app = typer.Typer(
    help="Carga de dados (seed) do banco da Quimia.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.callback()
def _global_options(
    ctx: typer.Context,
    target: Annotated[
        Target,
        typer.Option(
            "--target",
            envvar="SEED_TARGET",
            case_sensitive=False,
            help="Banco de destino. O padrão é sempre test.",
        ),
    ] = Target.TEST,
) -> None:
    ctx.obj = target
