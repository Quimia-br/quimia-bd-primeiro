"""Leitura e validação de data/reference e data/catalog (sem banco)."""

import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from seed import dados
from seed.cli import ExitCode, app
from seed.config import DATA_DIR, Target
from seed.contratos import DescarteFds, Estante, Produto, TipoHistorico
from seed.dados import DadosError, carregar_catalogo, carregar_dados, carregar_referencia
from seed.validacao import cas_valido, cep_valido


@pytest.fixture
def data_copy(tmp_path: Path) -> Path:
    """Cópia da pasta data/ para os testes poderem estragar os arquivos."""
    destino = tmp_path / "data"
    shutil.copytree(DATA_DIR, destino)
    return destino


def _edit_catalog(data_copy: Path, change: Any) -> None:
    arquivo = data_copy / "catalog" / "produtos.json"
    doc = json.loads(arquivo.read_text(encoding="utf-8"))
    change(doc)
    arquivo.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


# ------------------------------------------------------------------ arquivos reais


def test_real_reference_data() -> None:
    referencia = carregar_referencia()

    assert [t.nome for t in referencia.tipos_historicos] == [
        "USO",
        "DESCARTE",
        "ARMAZENAMENTO",
        "VERIFICACAO",
        "MISTURA",
    ]
    assert referencia.regra("MISTURA").produtos_min == 2
    assert referencia.regra("ARMAZENAMENTO").estante_obrigatoria is True
    assert len(referencia.comodos) == 8
    assert "DESCONHECIDO" not in referencia.comodos
    assert len(referencia.cidades) >= 10
    for nome in referencia.comodos:
        Estante.model_validate({"id_usuario": 1, "comodo": nome})
    for tipo in referencia.tipos_historicos:
        TipoHistorico.model_validate({"nome": tipo.nome})


def test_real_catalog_has_100_distinct_valid_cas() -> None:
    catalogo = carregar_catalogo()

    assert len(catalogo.produtos) == 100
    cas = [p.cas_number for p in catalogo.produtos]
    assert len(set(cas)) == 100
    assert all(cas_valido(c) for c in cas)


def test_real_catalog_is_pending_review() -> None:
    catalogo = carregar_catalogo()

    assert catalogo.revisados == []
    assert catalogo.para_alvo(Target.MAIN) == []
    assert len(catalogo.para_alvo(Target.TEST)) == 100
    for produto in catalogo.produtos:
        assert produto.fonte == dados.PENDENTE_CONFERENCIA
        assert produto.data_consulta is None
        # Nenhum texto de uso, dosagem ou descarte foi inventado.
        assert produto.instrucao_de_uso == dados.PENDENTE_REVISAO
        assert produto.dosagem_tecnica == dados.PENDENTE_REVISAO
        assert produto.metodo_descarte_produto == dados.PENDENTE_REVISAO
        assert produto.precaucao_ambiental == dados.PENDENTE_REVISAO


def test_catalog_entries_fit_the_table_contracts() -> None:
    for produto in carregar_catalogo().produtos:
        Produto.model_validate(
            {
                "id_usuario_empresa": 1,
                **produto.model_dump(
                    include={"cas_number", "nome", "marca", "instrucao_de_uso", "dosagem_tecnica"}
                ),
            }
        )
        DescarteFds.model_validate(
            {
                "id_produto": 1,
                **produto.model_dump(
                    include={
                        "metodo_descarte_produto",
                        "metodo_descarte_embalagem",
                        "restricao_descarte",
                        "precaucao_ambiental",
                    }
                ),
            }
        )


def test_city_ceps_are_valid() -> None:
    for cidade in carregar_referencia().cidades:
        assert cep_valido(cidade.cep_inicio) and cep_valido(cidade.cep_fim)


# ------------------------------------------------------------------ erros


def test_invalid_cas_points_to_file_and_field(data_copy: Path) -> None:
    _edit_catalog(data_copy, lambda doc: doc["produtos"][3].update(cas_number="64-17-4"))

    with pytest.raises(DadosError) as info:
        carregar_dados(data_copy)

    assert "produtos.json" in str(info.value)
    assert "produtos[3].cas_number" in str(info.value)
    assert "CAS inválido" in str(info.value)


def test_duplicated_cas_is_rejected(data_copy: Path) -> None:
    def duplicate(doc: dict[str, Any]) -> None:
        doc["produtos"][1]["cas_number"] = doc["produtos"][0]["cas_number"]

    _edit_catalog(data_copy, duplicate)

    with pytest.raises(DadosError, match="CAS repetidos"):
        carregar_catalogo(data_copy / "catalog")


def test_reviewed_entry_cannot_keep_pending_texts(data_copy: Path) -> None:
    def review(doc: dict[str, Any]) -> None:
        doc["produtos"][0].update(revisado=True, fonte="FDS consultada", data_consulta="2026-10-01")

    _edit_catalog(data_copy, review)

    with pytest.raises(DadosError, match="campos pendentes"):
        carregar_catalogo(data_copy / "catalog")


def test_reviewed_entry_needs_source(data_copy: Path) -> None:
    _edit_catalog(data_copy, lambda doc: doc["produtos"][0].update(revisado=True))

    with pytest.raises(DadosError, match="fonte conferida"):
        carregar_catalogo(data_copy / "catalog")


def test_main_only_gets_reviewed_entries(data_copy: Path) -> None:
    def review(doc: dict[str, Any]) -> None:
        doc["produtos"][0].update(
            revisado=True,
            fonte="FDS do fabricante, consultada",
            data_consulta="2026-10-01",
            instrucao_de_uso="texto conferido",
            dosagem_tecnica="texto conferido",
            metodo_descarte_produto="texto conferido",
            metodo_descarte_embalagem="texto conferido",
            restricao_descarte="texto conferido",
            precaucao_ambiental="texto conferido",
        )

    _edit_catalog(data_copy, review)
    catalogo = carregar_catalogo(data_copy / "catalog")

    assert [p.cas_number for p in catalogo.para_alvo(Target.MAIN)] == [
        catalogo.produtos[0].cas_number
    ]


def test_unquoted_cep_in_yaml_is_rejected(data_copy: Path) -> None:
    arquivo = data_copy / "reference" / "cidades.yaml"
    texto = arquivo.read_text(encoding="utf-8")
    arquivo.write_text(texto.replace('cep_inicio: "01000000"', "cep_inicio: 01000000"), "utf-8")

    with pytest.raises(DadosError, match=r"cidades\[0\]\.cep_inicio"):
        carregar_referencia(data_copy / "reference")


def test_yaml_syntax_error_shows_line(data_copy: Path) -> None:
    arquivo = data_copy / "reference" / "comodos.yaml"
    arquivo.write_text('comodos:\n  - "COZINHA"\n  - "SALA\n', encoding="utf-8")

    with pytest.raises(DadosError, match=r"comodos\.yaml: YAML inválido na linha"):
        carregar_referencia(data_copy / "reference")


def test_history_rule_limits(data_copy: Path) -> None:
    arquivo = data_copy / "reference" / "tipos_historicos.yaml"
    texto = arquivo.read_text(encoding="utf-8")
    arquivo.write_text(texto.replace("produtos_max: 4", "produtos_max: 1"), encoding="utf-8")

    with pytest.raises(DadosError, match="produtos_max"):
        carregar_referencia(data_copy / "reference")


def test_unknown_audited_table(data_copy: Path) -> None:
    arquivo = data_copy / "reference" / "auditoria.yaml"
    arquivo.write_text('tabelas:\n  - "usuarios"\n  - "clientes"\n', encoding="utf-8")

    with pytest.raises(DadosError, match="clientes"):
        carregar_referencia(data_copy / "reference")


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(DadosError, match="arquivo não encontrado"):
        carregar_referencia(tmp_path)


# ------------------------------------------------------------------ CLI


def test_cli_validate_ok() -> None:
    result = CliRunner().invoke(app, ["validate"], env={"FORCE_COLOR": "", "NO_COLOR": "1"})

    assert result.exit_code == ExitCode.OK
    assert "Todos os arquivos são válidos" in result.output
    assert "100" in result.output


def test_cli_validate_reports_errors(data_copy: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _edit_catalog(data_copy, lambda doc: doc["produtos"][0].update(cas_number="1-1-1"))
    monkeypatch.setattr(dados, "DATA_DIR", data_copy)

    result = CliRunner().invoke(app, ["validate"])

    assert result.exit_code == ExitCode.DADOS
    assert "CAS inválido" in result.output
