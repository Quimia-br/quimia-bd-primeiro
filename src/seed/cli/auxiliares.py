"""Funções compartilhadas pelos comandos: conexão, mensagens, confirmações e geração."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import NoReturn

import typer
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import Connection
from sqlalchemy.exc import DBAPIError

from seed import dados
from seed.cli.app import ExitCode, console
from seed.config import ConfigError, Settings, Target, create_db_engine, get_settings
from seed.generators import DadosGerados, gerar_referencia, gerar_tudo
from seed.generators.historicos import HistoricoImpossivel
from seed.modelos import table_names


@contextmanager
def conexao(settings: Settings, *, transacao: bool = False) -> Iterator[Connection]:
    """Conexão com a engine do alvo; com ``transacao=True``, tudo ou nada."""
    engine = create_db_engine(settings)
    try:
        if transacao:
            with engine.begin() as conn:
                yield conn
        else:
            with engine.connect() as conn:
                yield conn
    finally:
        engine.dispose()


def gerar_dados(settings: Settings, semente: int, sinteticos: bool) -> DadosGerados:
    carregados = carregar_dados()
    if not sinteticos:
        return gerar_referencia(carregados.referencia, semente=semente)
    if settings.password_plain is None:
        falhar(
            f"Defina SEED_PASSWORD_PLAIN no {settings.target.env_file_name} "
            "(senha das contas sintéticas).",
            ExitCode.CONFIGURACAO,
        )
    entradas = carregados.catalogo.para_alvo(settings.target)
    try:
        return gerar_tudo(
            carregados.referencia,
            entradas,
            settings.password_plain.get_secret_value(),
            semente=semente,
            auditoria=settings.target is Target.TEST,
        )
    except (HistoricoImpossivel, ValueError) as exc:
        falhar(f"Não foi possível gerar os dados sem quebrar as regras: {exc}", ExitCode.DADOS)


def carregar_dados() -> dados.Dados:
    try:
        return dados.carregar_dados()
    except dados.DadosError as exc:
        falhar(f"Dados inválidos:\n{exc}", ExitCode.DADOS)


def imprimir_contagens(gerados: DadosGerados, titulo: str) -> None:
    table = Table(title=f"{titulo} (semente {gerados.semente})")
    table.add_column("Tabela")
    table.add_column("Linhas", justify="right")
    for nome, total in gerados.contagens().items():
        table.add_row(nome, str(total))
    console.print(table)


def confirmar_ou_bloquear(pergunta: str) -> None:
    if not typer.confirm(pergunta, default=False):
        falhar("Operação cancelada.", ExitCode.BLOQUEADO)


def confirmar_nome_do_banco(settings: Settings) -> None:
    console.print(
        Panel(
            f"Você vai gravar no banco PRINCIPAL ({settings.db_name}).",
            title="ATENÇÃO",
            style="bold red",
        )
    )
    digitado = typer.prompt("Digite o nome do banco para confirmar", default="", show_default=False)
    if digitado.strip() != settings.db_name:
        falhar("Nome do banco não confere; nada foi gravado.", ExitCode.BLOQUEADO)


def connection_hint(message: str) -> str:
    """Dica para o erro de conexão, a partir do texto do driver."""
    text = message.lower()
    if "certificate" in text or "ssl" in text:
        return (
            "Erro de SSL/certificado: confira se SEED_DB_SSLROOTCERT aponta para o CA "
            "deste serviço e se SEED_DB_SSLMODE é verify-ca."
        )
    if "password authentication failed" in text:
        return "Usuário ou senha recusados: confira SEED_DB_USER e SEED_DB_PASSWORD."
    if "does not exist" in text:
        return "Objeto inexistente: confira SEED_DB_NAME (normalmente defaultdb) e as tabelas."
    if "translate host name" in text or "name or service not known" in text:
        return "Host não encontrado: confira SEED_DB_HOST."
    return (
        "Confira a allowlist de IPs do serviço no Aiven, SEED_DB_HOST e SEED_DB_PORT "
        "(a porta do Aiven não é 5432)."
    )


def falhar_conexao(
    settings: Settings, exc: Exception, prefixo: str = "Falha ao conectar"
) -> NoReturn:
    cause = exc.orig if isinstance(exc, DBAPIError) and exc.orig is not None else exc
    message = settings.redact(str(cause)).strip()
    falhar(f"{prefixo}: {message}\n{connection_hint(message)}", ExitCode.CONEXAO)


def carregar_settings(ctx: typer.Context) -> Settings:
    target: Target = ctx.obj
    try:
        return get_settings(target)
    except ConfigError as exc:
        falhar(str(exc), ExitCode.CONFIGURACAO)


def imprimir_cabecalho(settings: Settings) -> None:
    summary = (
        f"Alvo: {settings.target.value}  |  Host: {settings.masked_host}  |  "
        f"Banco: {settings.db_name}  |  Schema: {settings.db_schema}  |  "
        f"Usuário: {settings.db_user}"
    )
    if settings.target is Target.MAIN:
        console.print(Panel(summary, title="ATENÇÃO: banco PRINCIPAL (main)", style="bold red"))
    else:
        console.print(Panel(summary, title="Banco de teste", style="green"))


def falhar(message: str, code: ExitCode) -> NoReturn:
    console.print(f"[red]{message}[/red]", highlight=False)
    raise typer.Exit(code)


def formatar_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def resumo_tabelas(missing: tuple[str, ...]) -> str:
    total = len(table_names())
    if not missing:
        return f"todas as {total} presentes"
    return f"{total - len(missing)} de {total} presentes"
