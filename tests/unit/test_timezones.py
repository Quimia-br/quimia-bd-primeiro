import pytest

from seed.validacao import same_timezone


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        ("UTC", "UTC", True),
        ("UTC", "Etc/UTC", True),
        ("utc", "GMT", True),
        ("America/Sao_Paulo", "america/sao_paulo", True),
        ("America/Sao_Paulo", "UTC", False),
        ("America/Sao_Paulo", "America/Bahia", False),
    ],
)
def test_same_timezone(first: str, second: str, expected: bool) -> None:
    assert same_timezone(first, second) is expected
