"""O ``.env.example`` precisa continuar carregável e sem variáveis desconhecidas."""

import shutil
from pathlib import Path

from dotenv import dotenv_values

from seed.config import Settings, Target, load_settings

ENV_EXAMPLE = Path(__file__).resolve().parents[2] / ".env.example"


def test_env_example_variables_are_known_fields() -> None:
    names = dotenv_values(ENV_EXAMPLE).keys()
    fields = {f"SEED_{field.upper()}" for field in Settings.model_fields}

    assert names, ".env.example está vazio"
    assert set(names) <= fields, f"variáveis desconhecidas: {set(names) - fields}"


def test_env_example_loads_as_test_target(tmp_path: Path, ca_file: Path) -> None:
    shutil.copy(ENV_EXAMPLE, tmp_path / Target.TEST.env_file_name)

    settings = load_settings(Target.TEST)

    assert settings.db_sslrootcert == Path("certs/ca-test.pem")
    assert settings.db_sslmode == "verify-ca"
    assert settings.timezone == "UTC"
