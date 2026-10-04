"""Geradores: quantidades, regras de negócio e determinismo, tudo em memória (sem banco)."""

import re
from collections import Counter
from datetime import UTC, datetime
from typing import Any, cast

import pytest
from pwdlib.hashers.argon2 import Argon2Hasher

from seed.config import EMAIL_DOMINIOS, FRACAO_SEM_DATA_NASCIMENTO, IDADE_MINIMA
from seed.contratos import (
    AcaoLog,
    Admin,
    AdminLogEdicao,
    DescarteFds,
    Estante,
    Historico,
    HistoricoProduto,
    Localizacao,
    Produto,
    ProdutoEstante,
    ProdutoUsuario,
    StatusConta,
    TipoHistorico,
    Usuario,
    UsuarioEmpresa,
)
from seed.dados import Dados, carregar_dados
from seed.generators import DadosGerados, gerar_tudo
from seed.modelos import load_order
from seed.validacao import cnpj_valido, idade_em

AGORA = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
SENHA = "senha-de-teste-ficticia"
SEMENTES = [1, 42, 2026]


@pytest.fixture(scope="module")
def dados() -> Dados:
    return carregar_dados()


@pytest.fixture(scope="module", params=SEMENTES, ids=lambda s: f"semente{s}")
def gerados(request: pytest.FixtureRequest, dados: Dados) -> DadosGerados:
    return gerar_tudo(
        dados.referencia, dados.catalogo.produtos, SENHA, semente=request.param, agora=AGORA
    )


def _t[T](gerados: DadosGerados, tabela: str, tipo: type[T]) -> list[T]:
    linhas = gerados.tabelas[tabela]
    assert all(isinstance(linha, tipo) for linha in linhas)
    return cast(list[T], linhas)


# ------------------------------------------------------------------ quantidades e chaves


def test_exactly_100_rows_per_table(gerados: DadosGerados, dados: Dados) -> None:
    contagens = gerados.contagens()
    assert contagens.pop("tipos_historicos") == len(dados.referencia.tipos_historicos) == 5
    assert set(contagens.values()) == {100}


def test_tables_follow_load_order(gerados: DadosGerados) -> None:
    assert list(gerados.tabelas) == load_order()


def test_foreign_keys_point_to_existing_rows(gerados: DadosGerados) -> None:
    tamanho = gerados.contagens()
    referencias: dict[str, dict[str, str]] = {
        "produtos": {"id_usuario_empresa": "usuarios_empresas"},
        "produtos_usuarios": {"id_usuario": "usuarios", "id_produto": "produtos"},
        "admin_log_edicoes": {"id_admin": "admins"},
        "localizacoes": {"id_usuario": "usuarios"},
        "estantes": {"id_usuario": "usuarios"},
        "historicos": {
            "id_estante": "estantes",
            "id_usuario": "usuarios",
            "id_tipo_historico": "tipos_historicos",
        },
        "produtos_estantes": {"id_estante": "estantes", "id_produto": "produtos"},
        "descartes_fds": {"id_produto": "produtos"},
        "historicos_produtos": {
            "id_produto": "produtos",
            "id_historico": "historicos",
            "id_usuario": "usuarios",
        },
    }
    for tabela, colunas in referencias.items():
        for linha in gerados.tabelas[tabela]:
            for coluna, pai in colunas.items():
                valor = getattr(linha, coluna)
                assert valor is None or 1 <= valor <= tamanho[pai], f"{tabela}.{coluna}"


def test_primary_and_unique_keys(gerados: DadosGerados) -> None:
    def sem_repeticao(tabela: str, *colunas: str) -> None:
        chaves = [tuple(getattr(linha, c) for c in colunas) for linha in gerados.tabelas[tabela]]
        assert len(chaves) == len(set(chaves)), f"{tabela} {colunas}"

    sem_repeticao("usuarios_empresas", "cnpj")
    sem_repeticao("usuarios_empresas", "email")
    sem_repeticao("admins", "email")
    sem_repeticao("usuarios", "email")
    sem_repeticao("tipos_historicos", "nome")
    sem_repeticao("produtos", "cas_number")
    sem_repeticao("produtos_usuarios", "id_usuario", "id_produto")
    sem_repeticao("localizacoes", "id_usuario")
    sem_repeticao("estantes", "id_usuario", "comodo")
    sem_repeticao("produtos_estantes", "id_estante", "id_produto")
    sem_repeticao("descartes_fds", "id_produto")
    sem_repeticao("historicos_produtos", "id_historico", "id_produto")


# ------------------------------------------------------------------ contas


def test_emails_are_synthetic_and_lowercase(gerados: DadosGerados) -> None:
    for tabela in ("usuarios", "admins", "usuarios_empresas"):
        for linha in gerados.tabelas[tabela]:
            email = cast(Any, linha).email
            assert email == email.lower()
            assert email.rsplit("@", 1)[1] in EMAIL_DOMINIOS


def test_cnpjs_are_valid_and_some_alphanumeric(gerados: DadosGerados) -> None:
    cnpjs = [e.cnpj for e in _t(gerados, "usuarios_empresas", UsuarioEmpresa)]
    assert all(cnpj_valido(c) for c in cnpjs)
    alfanumericos = [c for c in cnpjs if not c.isdigit()]
    assert 10 <= len(alfanumericos) <= 50


def test_user_photos(gerados: DadosGerados) -> None:
    padrao = re.compile(r"^https://randomuser\.me/api/portraits/(women|men)/(\d{1,2})\.jpg$")
    indices = []
    for usuario in _t(gerados, "usuarios", Usuario):
        assert usuario.url_foto is not None
        match = padrao.fullmatch(usuario.url_foto)
        assert match, usuario.url_foto
        indices.append(int(match.group(2)))
    assert len(set(indices)) == len(indices)
    assert all(0 <= i <= 99 for i in indices)


def test_company_photos(gerados: DadosGerados) -> None:
    for empresa in _t(gerados, "usuarios_empresas", UsuarioEmpresa):
        assert empresa.url_foto is not None
        assert empresa.url_foto.startswith("https://ui-avatars.com/api/?name=")
        assert empresa.url_foto.endswith("&size=256")
        assert " " not in empresa.url_foto


def test_minimum_age_and_missing_birth_dates(gerados: DadosGerados) -> None:
    usuarios = _t(gerados, "usuarios", Usuario)
    sem_data = [u for u in usuarios if u.data_nascimento is None]
    assert len(sem_data) == round(len(usuarios) * FRACAO_SEM_DATA_NASCIMENTO)
    for usuario in usuarios:
        if usuario.data_nascimento is not None:
            cadastro = usuario.data_cadastro.date()
            assert idade_em(usuario.data_nascimento, cadastro) >= IDADE_MINIMA


def test_signup_dates_are_not_after_load(gerados: DadosGerados) -> None:
    for tabela in ("usuarios", "admins", "usuarios_empresas"):
        for linha in gerados.tabelas[tabela]:
            assert cast(Any, linha).data_cadastro <= AGORA


def test_status_distribution(gerados: DadosGerados) -> None:
    status = Counter(u.status for u in _t(gerados, "usuarios", Usuario))
    assert status[StatusConta.ATIVO] >= 60
    assert sum(status.values()) == 100


def test_one_location_per_user_inside_city_range(gerados: DadosGerados, dados: Dados) -> None:
    localizacoes = _t(gerados, "localizacoes", Localizacao)
    assert sorted(loc.id_usuario for loc in localizacoes) == list(range(1, 101))
    faixas = [(c.cep_inicio, c.cep_fim) for c in dados.referencia.cidades]
    for local in localizacoes:
        assert any(inicio <= local.cep <= fim for inicio, fim in faixas)
    com_coordenadas = [loc for loc in localizacoes if loc.latitude is not None]
    assert len(com_coordenadas) >= 70


# ------------------------------------------------------------------ produtos e estantes


def test_every_product_has_exactly_one_disposal(gerados: DadosGerados) -> None:
    descartes = _t(gerados, "descartes_fds", DescarteFds)
    assert sorted(d.id_produto for d in descartes) == list(range(1, 101))


def test_products_come_from_catalog(gerados: DadosGerados, dados: Dados) -> None:
    catalogo = {e.cas_number: e for e in dados.catalogo.produtos}
    for produto in _t(gerados, "produtos", Produto):
        entrada = catalogo[produto.cas_number]
        assert produto.nome == entrada.nome
        assert produto.instrucao_de_uso == entrada.instrucao_de_uso  # nunca gerado


def test_owners_have_two_to_four_products(gerados: DadosGerados) -> None:
    por_dono = Counter(p.id_usuario for p in _t(gerados, "produtos_usuarios", ProdutoUsuario))
    assert all(2 <= n <= 4 for n in por_dono.values())
    assert len(por_dono) < 100  # há usuários sem produtos


def test_shelf_products_belong_to_shelf_owner(gerados: DadosGerados) -> None:
    estantes = _t(gerados, "estantes", Estante)
    posses = {
        (p.id_usuario, p.id_produto) for p in _t(gerados, "produtos_usuarios", ProdutoUsuario)
    }
    usuarios = _t(gerados, "usuarios", Usuario)
    for guardado in _t(gerados, "produtos_estantes", ProdutoEstante):
        dono = estantes[guardado.id_estante - 1].id_usuario
        assert (dono, guardado.id_produto) in posses
        assert usuarios[dono - 1].data_cadastro <= guardado.data_adicao <= AGORA


# ------------------------------------------------------------------ históricos


def _por_historico(gerados: DadosGerados) -> dict[int, list[HistoricoProduto]]:
    vinculos: dict[int, list[HistoricoProduto]] = {}
    for v in _t(gerados, "historicos_produtos", HistoricoProduto):
        vinculos.setdefault(v.id_historico, []).append(v)
    return vinculos


def test_history_shelf_belongs_to_history_user(gerados: DadosGerados) -> None:
    estantes = _t(gerados, "estantes", Estante)
    for historico in _t(gerados, "historicos", Historico):
        if historico.id_estante is not None:
            assert estantes[historico.id_estante - 1].id_usuario == historico.id_usuario


def test_history_products_belong_to_history_user(gerados: DadosGerados) -> None:
    historicos = _t(gerados, "historicos", Historico)
    posses = {
        (p.id_usuario, p.id_produto) for p in _t(gerados, "produtos_usuarios", ProdutoUsuario)
    }
    for vinculo in _t(gerados, "historicos_produtos", HistoricoProduto):
        assert vinculo.id_usuario == historicos[vinculo.id_historico - 1].id_usuario
        assert (vinculo.id_usuario, vinculo.id_produto) in posses


def test_rules_per_history_type(gerados: DadosGerados, dados: Dados) -> None:
    tipos = _t(gerados, "tipos_historicos", TipoHistorico)
    guardados = {
        (g.id_estante, g.id_produto): g.data_adicao
        for g in _t(gerados, "produtos_estantes", ProdutoEstante)
    }
    vinculos = _por_historico(gerados)
    for posicao, historico in enumerate(_t(gerados, "historicos", Historico)):
        regra = dados.referencia.regra(tipos[historico.id_tipo_historico - 1].nome)
        produtos = vinculos.get(posicao + 1, [])
        assert regra.produtos_min <= len(produtos) <= regra.produtos_max, regra.nome
        if regra.estante_obrigatoria:
            assert historico.id_estante is not None, regra.nome
            for vinculo in produtos:
                # ARMAZENAMENTO/VERIFICACAO: o produto está na estante desde antes.
                data_adicao = guardados[(historico.id_estante, vinculo.id_produto)]
                assert data_adicao <= historico.data_execucao


def test_mixtures_have_two_or_more_products(gerados: DadosGerados) -> None:
    tipos = _t(gerados, "tipos_historicos", TipoHistorico)
    vinculos = _por_historico(gerados)
    for posicao, historico in enumerate(_t(gerados, "historicos", Historico)):
        if tipos[historico.id_tipo_historico - 1].nome == "MISTURA":
            assert len(vinculos.get(posicao + 1, [])) >= 2


def test_history_dates(gerados: DadosGerados) -> None:
    usuarios = _t(gerados, "usuarios", Usuario)
    for historico in _t(gerados, "historicos", Historico):
        assert usuarios[historico.id_usuario - 1].data_cadastro <= historico.data_execucao <= AGORA


def test_some_users_have_no_history(gerados: DadosGerados) -> None:
    com_historico = {h.id_usuario for h in _t(gerados, "historicos", Historico)}
    assert len(com_historico) < 100


def test_descriptions_are_neutral(gerados: DadosGerados) -> None:
    proibidas = ("reag", "gás", "tóxic", "explo", "misture", "adicione", "aqueça")
    for historico in _t(gerados, "historicos", Historico):
        if historico.descricao_resultado is not None:
            texto = historico.descricao_resultado.lower()
            assert not any(p in texto for p in proibidas), texto


# ------------------------------------------------------------------ auditoria


def test_audit_logs_are_inserts_of_existing_records(gerados: DadosGerados, dados: Dados) -> None:
    admins = _t(gerados, "admins", Admin)
    tamanho = gerados.contagens()
    criacao = {
        "usuarios": [u.data_cadastro for u in _t(gerados, "usuarios", Usuario)],
        "usuarios_empresas": [
            e.data_cadastro for e in _t(gerados, "usuarios_empresas", UsuarioEmpresa)
        ],
    }
    logs = _t(gerados, "admin_log_edicoes", AdminLogEdicao)
    assert len({(log.tabela_afetada, log.id_registro) for log in logs}) == len(logs)
    for log in logs:
        assert log.acao is AcaoLog.INSERT
        assert log.dado_anterior is None
        assert log.tabela_afetada in dados.referencia.tabelas_auditaveis
        assert 1 <= log.id_registro <= tamanho[log.tabela_afetada]
        assert admins[log.id_admin - 1].data_cadastro <= log.data_edicao <= AGORA
        if log.tabela_afetada in criacao:
            assert log.data_edicao == criacao[log.tabela_afetada][log.id_registro - 1]


def test_audit_can_be_disabled(dados: Dados) -> None:
    gerados = gerar_tudo(
        dados.referencia, dados.catalogo.produtos, SENHA, semente=7, agora=AGORA, auditoria=False
    )
    assert gerados.tabelas["admin_log_edicoes"] == []


# ------------------------------------------------------------------ determinismo


def test_same_seed_same_data(dados: Dados) -> None:
    primeira = gerar_tudo(dados.referencia, dados.catalogo.produtos, SENHA, semente=42, agora=AGORA)
    segunda = gerar_tudo(dados.referencia, dados.catalogo.produtos, SENHA, semente=42, agora=AGORA)
    assert primeira.hash_conteudo() == segunda.hash_conteudo()


def test_different_seed_different_data(dados: Dados) -> None:
    a = gerar_tudo(dados.referencia, dados.catalogo.produtos, SENHA, semente=42, agora=AGORA)
    b = gerar_tudo(dados.referencia, dados.catalogo.produtos, SENHA, semente=43, agora=AGORA)
    assert a.hash_conteudo() != b.hash_conteudo()


def test_password_hash_is_shared_and_verifiable(gerados: DadosGerados) -> None:
    hashes = {u.senha_hash for u in _t(gerados, "usuarios", Usuario)}
    hashes |= {a.senha_hash for a in _t(gerados, "admins", Admin)}
    assert len(hashes) == 1
    assert Argon2Hasher().verify(SENHA, hashes.pop())


def test_fewer_catalog_entries_limit_products(dados: Dados) -> None:
    gerados = gerar_tudo(
        dados.referencia,
        dados.catalogo.produtos[:30],
        SENHA,
        semente=42,
        agora=AGORA,
    )
    assert gerados.contagens()["produtos"] == 30
    assert gerados.contagens()["descartes_fds"] == 30
