"""Comandos somente leitura: ``check``, ``validate``, ``verificar`` e ``stats``."""

import typer
from rich.table import Table
from sqlalchemy.exc import DBAPIError

from seed import verificacao
from seed.cli import auxiliares as aux
from seed.cli.app import ExitCode, app, console
from seed.config import ConfigError, Target
from seed.modelos import load_order
from seed.validacao import same_timezone


@app.command()
def check(ctx: typer.Context) -> None:
    """Conecta e mostra um diagnóstico do banco e a comparação com os modelos. Somente leitura."""
    settings = aux.carregar_settings(ctx)
    aux.imprimir_cabecalho(settings)
    try:
        info = verificacao.fetch_server_info(settings)
        with aux.conexao(settings) as conn:
            divergencias = verificacao.comparar_schema(conn, settings.db_schema)
    except ConfigError as exc:
        aux.falhar(str(exc), ExitCode.CONFIGURACAO)
    except (DBAPIError, OSError) as exc:
        aux.falhar_conexao(settings, exc)

    table = Table(title="Diagnóstico do banco", show_header=False)
    table.add_column("Item", style="bold")
    table.add_column("Valor")
    table.add_row("Banco", info.database)
    table.add_row("Usuário", info.user)
    table.add_row("Schema", info.current_schema or "(nenhum no search_path)")
    table.add_row("Postgres", info.server_version)
    table.add_row("Conexões", f"{info.open_connections} abertas de {info.max_connections}")
    table.add_row("Tamanho", aux.formatar_bytes(info.database_size_bytes))
    table.add_row("Fuso do servidor", info.timezone)
    table.add_row("Fuso do seed", settings.timezone)
    table.add_row("Tabelas esperadas", aux.resumo_tabelas(info.missing_tables))
    table.add_row(
        "Modelos × banco", "iguais" if not divergencias else f"{len(divergencias)} divergências"
    )
    console.print(table)

    if not same_timezone(info.timezone, settings.timezone):
        console.print(
            f"[yellow]Aviso: o fuso do servidor ({info.timezone}) é diferente de "
            f"SEED_TIMEZONE ({settings.timezone}). O seed run vai recusar a carga.[/yellow]"
        )
    if info.missing_tables:
        console.print(
            "[yellow]Aviso: tabelas ausentes ou sem permissão para o usuário: "
            f"{', '.join(info.missing_tables)}.[/yellow]"
        )
    if divergencias:
        console.print("[yellow]Divergências entre os modelos e o banco:[/yellow]")
        for item in divergencias:
            console.print(f"[yellow]  - {item}[/yellow]", highlight=False)
        console.print("[yellow]O seed run vai recusar a carga até isso ser resolvido.[/yellow]")


@app.command()
def validate(ctx: typer.Context) -> None:
    """Valida data/reference e data/catalog sem conectar ao banco."""
    target: Target = ctx.obj
    carregados = aux.carregar_dados()
    referencia, catalogo = carregados.referencia, carregados.catalogo
    revisados = len(catalogo.revisados)
    table = Table(title="Dados de referência e catálogo", show_header=False)
    table.add_column("Item", style="bold")
    table.add_column("Valor")
    table.add_row("Tipos de histórico", ", ".join(t.nome for t in referencia.tipos_historicos))
    table.add_row("Cômodos", str(len(referencia.comodos)))
    table.add_row("Cidades", str(len(referencia.cidades)))
    table.add_row("Tabelas auditáveis", ", ".join(referencia.tabelas_auditaveis))
    table.add_row("Produtos no catálogo", str(len(catalogo.produtos)))
    table.add_row("Revisados", str(revisados))
    table.add_row("Pendentes de revisão", str(len(catalogo.produtos) - revisados))
    console.print(table)
    console.print("[green]Todos os arquivos são válidos.[/green]")
    if target is Target.MAIN:
        console.print(
            f"[yellow]Alvo main: só as {revisados} entradas revisadas do catálogo "
            "podem ser carregadas.[/yellow]"
        )


@app.command()
def verificar(ctx: typer.Context) -> None:
    """Confere as regras de negócio no banco. Somente leitura."""
    settings = aux.carregar_settings(ctx)
    aux.imprimir_cabecalho(settings)
    referencia = aux.carregar_dados().referencia
    try:
        with aux.conexao(settings) as conn:
            resultados = verificacao.verificar_regras(conn, settings, referencia)
    except (DBAPIError, OSError) as exc:
        aux.falhar_conexao(settings, exc)

    table = Table(title="Regras de negócio")
    table.add_column("Regra")
    table.add_column("Resultado")
    table.add_column("Violações", justify="right")
    for r in resultados:
        situacao = "[green]aprovada[/green]" if r.aprovada else "[red]reprovada[/red]"
        table.add_row(r.nome, situacao, str(r.violacoes))
    console.print(table)
    reprovadas = [r for r in resultados if not r.aprovada]
    if reprovadas:
        aux.falhar(f"{len(reprovadas)} regra(s) reprovada(s).", ExitCode.REGRAS)
    console.print("[green]Todas as regras aprovadas.[/green]")


@app.command()
def stats(ctx: typer.Context) -> None:
    """Mostra quantas linhas cada tabela tem. Somente leitura."""
    settings = aux.carregar_settings(ctx)
    aux.imprimir_cabecalho(settings)
    try:
        with aux.conexao(settings) as conn:
            totais = verificacao.contagens(conn)
    except (DBAPIError, OSError) as exc:
        aux.falhar_conexao(settings, exc)
    table = Table(title="Linhas por tabela")
    table.add_column("Tabela")
    table.add_column("Linhas", justify="right")
    for nome in load_order():
        table.add_row(nome, str(totais.get(nome, 0)))
    console.print(table)
