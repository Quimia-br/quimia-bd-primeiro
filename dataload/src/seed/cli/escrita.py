"""Comandos que gravam no banco: ``run`` e ``reset``."""

import time
from typing import Annotated

import typer
from rich.table import Table
from sqlalchemy.exc import DBAPIError

from seed import carga, verificacao
from seed.cli import auxiliares as aux
from seed.cli.app import ExitCode, app, console
from seed.config import SEMENTE_PADRAO, ConfigError, Target
from seed.modelos import load_order, table_names
from seed.validacao import same_timezone


@app.command()
def run(
    ctx: typer.Context,
    seed: Annotated[int, typer.Option("--seed", help="Semente da geração.")] = SEMENTE_PADRAO,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Gera e valida tudo, sem conectar nem gravar.")
    ] = False,
    allow_synthetic: Annotated[
        bool,
        typer.Option("--allow-synthetic", help="Permite dados sintéticos no alvo main."),
    ] = False,
    ignorar_fuso: Annotated[
        bool,
        typer.Option(
            "--ignorar-fuso",
            help="Carrega mesmo com o fuso do servidor diferente de SEED_TIMEZONE.",
        ),
    ] = False,
) -> None:
    """Gera os dados e carrega no banco numa única transação."""
    settings = aux.carregar_settings(ctx)
    aux.imprimir_cabecalho(settings)
    principal = settings.target is Target.MAIN
    sinteticos = not principal or allow_synthetic

    if principal and allow_synthetic and not dry_run:
        console.print(
            "[bold red]Você pediu dados SINTÉTICOS no banco PRINCIPAL "
            "(exceto admin_log_edicoes).[/bold red]"
        )
        aux.confirmar_ou_bloquear("Confirma a carga de dados sintéticos no main?")

    gerados = aux.gerar_dados(settings, seed, sinteticos)
    aux.imprimir_contagens(gerados, titulo="Dados gerados")
    if dry_run:
        console.print("[green]Dry-run: tudo gerado e validado; nada foi gravado.[/green]")
        return

    if principal:
        aux.confirmar_nome_do_banco(settings)

    inicio = time.perf_counter()
    try:
        info = verificacao.fetch_server_info(settings)
        if not same_timezone(info.timezone, settings.timezone) and not ignorar_fuso:
            aux.falhar(
                f"O fuso do servidor ({info.timezone}) é diferente de SEED_TIMEZONE "
                f"({settings.timezone}). Ajuste SEED_TIMEZONE ou use --ignorar-fuso.",
                ExitCode.BLOQUEADO,
            )
        with aux.conexao(settings, transacao=True) as conn:
            divergencias = verificacao.comparar_schema(conn, settings.db_schema)
            if divergencias:
                aux.falhar(
                    "Os modelos não batem com o banco (veja seed check):\n  - "
                    + "\n  - ".join(divergencias),
                    ExitCode.SCHEMA,
                )
            problemas = carga.problemas_do_destino(conn, gerados, settings.target)
            if problemas:
                aux.falhar(
                    "O destino não está pronto:\n  - " + "\n  - ".join(problemas),
                    ExitCode.BLOQUEADO,
                )
            inseridas = carga.carregar(conn, gerados, settings.zone)
    except ConfigError as exc:
        aux.falhar(str(exc), ExitCode.CONFIGURACAO)
    except carga.CargaError as exc:
        aux.falhar(f"Carga interrompida, nada foi gravado: {exc}", ExitCode.ERRO)
    except (DBAPIError, OSError) as exc:
        aux.falhar_conexao(settings, exc, prefixo="Carga interrompida, nada foi gravado")

    segundos = time.perf_counter() - inicio
    table = Table(title="Carga concluída")
    table.add_column("Tabela")
    table.add_column("Linhas", justify="right")
    for nome in load_order():
        table.add_row(nome, str(inseridas.get(nome, 0)))
    console.print(table)
    console.print(
        f"Semente {gerados.semente} | alvo {settings.target.value} | "
        f"{sum(inseridas.values())} linhas | {segundos:.1f} s"
    )


@app.command()
def reset(
    ctx: typer.Context,
    yes: Annotated[bool, typer.Option("--yes", help="Não pede confirmação.")] = False,
) -> None:
    """Esvazia as 13 tabelas e reinicia as identities. Só no alvo test."""
    settings = aux.carregar_settings(ctx)
    aux.imprimir_cabecalho(settings)
    if settings.target is not Target.TEST:
        aux.falhar("reset é proibido no banco principal.", ExitCode.BLOQUEADO)
    if not yes:
        aux.confirmar_ou_bloquear(
            f"Apagar TODOS os dados das {len(table_names())} tabelas do banco de teste?"
        )
    try:
        with aux.conexao(settings, transacao=True) as conn:
            nomes = carga.esvaziar(conn, settings.target)
    except (DBAPIError, OSError) as exc:
        aux.falhar_conexao(settings, exc)
    console.print(f"[green]{len(nomes)} tabelas esvaziadas.[/green]")
