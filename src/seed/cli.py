"""Linha de comando do seed (Typer)."""

from enum import IntEnum
from typing import Annotated, NoReturn

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy.exc import DBAPIError

from seed.config import ConfigError, Settings, Target, get_settings
from seed.db import diagnostics
from seed.db.table_names import EXPECTED_TABLES
from seed.domain.timezones import same_timezone


class ExitCode(IntEnum):
    """Códigos de saída da CLI."""

    OK = 0
    ERRO = 1
    USO = 2  # usado pelo próprio Typer/Click para opções inválidas
    CONFIGURACAO = 3
    CONEXAO = 4


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


@app.command()
def check(ctx: typer.Context) -> None:
    """Conecta e mostra um diagnóstico do banco. Somente leitura."""
    settings = _load_settings(ctx)
    _print_target_header(settings)
    try:
        info = diagnostics.fetch_server_info(settings)
    except ConfigError as exc:
        _fail(str(exc), ExitCode.CONFIGURACAO)
    except (DBAPIError, OSError) as exc:
        cause = exc.orig if isinstance(exc, DBAPIError) and exc.orig is not None else exc
        message = settings.redact(str(cause)).strip()
        _fail(f"Falha ao conectar: {message}\n{connection_hint(message)}", ExitCode.CONEXAO)

    table = Table(title="Diagnóstico do banco", show_header=False)
    table.add_column("Item", style="bold")
    table.add_column("Valor")
    table.add_row("Banco", info.database)
    table.add_row("Usuário", info.user)
    table.add_row("Schema", info.current_schema or "(nenhum no search_path)")
    table.add_row("Postgres", info.server_version)
    table.add_row("Conexões", f"{info.open_connections} abertas de {info.max_connections}")
    table.add_row("Tamanho", _format_bytes(info.database_size_bytes))
    table.add_row("Fuso do servidor", info.timezone)
    table.add_row("Fuso do seed", settings.timezone)
    table.add_row("Revisão Alembic", info.alembic_revision or "(sem alembic_version)")
    table.add_row("Tabelas esperadas", _tables_summary(info.missing_tables))
    console.print(table)

    if not same_timezone(info.timezone, settings.timezone):
        console.print(
            f"[yellow]Aviso: o fuso do servidor ({info.timezone}) é diferente de "
            f"SEED_TIMEZONE ({settings.timezone}). O seed run vai recusar a carga "
            "(ADR 0010).[/yellow]"
        )
    if info.missing_tables:
        console.print(
            "[yellow]Aviso: tabelas ausentes ou sem permissão para o usuário: "
            f"{', '.join(info.missing_tables)}.[/yellow]"
        )
    if info.alembic_revision is None:
        console.print(
            "[yellow]Aviso: o banco ainda não tem revisão do Alembic "
            "(o stamp da baseline vem na Fase 3).[/yellow]"
        )


def main() -> None:
    """Ponto de entrada do comando ``seed``."""
    app()


def connection_hint(message: str) -> str:
    """Dica para o erro de conexão, a partir do texto do driver."""
    text = message.lower()
    if "certificate" in text or "ssl" in text:
        return (
            "Erro de SSL/certificado: confira se SEED_DB_SSLROOTCERT aponta para o CA "
            "deste serviço e se SEED_DB_SSLMODE é verify-ca (ADR 0017)."
        )
    if "password authentication failed" in text:
        return "Usuário ou senha recusados: confira SEED_DB_USER e SEED_DB_PASSWORD."
    if "does not exist" in text:
        return "Banco inexistente: confira SEED_DB_NAME (normalmente defaultdb)."
    if "translate host name" in text or "name or service not known" in text:
        return "Host não encontrado: confira SEED_DB_HOST."
    return (
        "Confira a allowlist de IPs do serviço no Aiven, SEED_DB_HOST e SEED_DB_PORT "
        "(a porta do Aiven não é 5432)."
    )


def _load_settings(ctx: typer.Context) -> Settings:
    target: Target = ctx.obj
    try:
        return get_settings(target)
    except ConfigError as exc:
        _fail(str(exc), ExitCode.CONFIGURACAO)


def _print_target_header(settings: Settings) -> None:
    summary = (
        f"Alvo: {settings.target.value}  |  Host: {settings.masked_host}  |  "
        f"Banco: {settings.db_name}  |  Schema: {settings.db_schema}  |  "
        f"Usuário: {settings.db_user}"
    )
    if settings.target is Target.MAIN:
        console.print(Panel(summary, title="ATENÇÃO: banco PRINCIPAL (main)", style="bold red"))
    else:
        console.print(Panel(summary, title="Banco de teste", style="green"))


def _fail(message: str, code: ExitCode) -> NoReturn:
    console.print(f"[red]{message}[/red]", highlight=False)
    raise typer.Exit(code)


def _format_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def _tables_summary(missing: tuple[str, ...]) -> str:
    total = len(EXPECTED_TABLES)
    if not missing:
        return f"todas as {total} presentes"
    return f"{total - len(missing)} de {total} presentes"
