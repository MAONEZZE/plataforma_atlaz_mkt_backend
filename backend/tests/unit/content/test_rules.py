import pytest

from app.contexts.conteudo.domain.exceptions import DriveUrlInvalida
from app.contexts.conteudo.domain.rules import parse_drive_file_id


def test_parse_file_d_format() -> None:
    url = "https://drive.google.com/file/d/abc123XYZ/view"
    assert parse_drive_file_id(url) == "abc123XYZ"


def test_parse_query_id_format() -> None:
    url = "https://drive.google.com/open?id=abc123XYZ"
    assert parse_drive_file_id(url) == "abc123XYZ"


def test_parse_ampersand_id_format() -> None:
    url = "https://docs.google.com/presentation/d/some/edit?usp=sharing&id=abc123XYZ"
    assert parse_drive_file_id(url) == "abc123XYZ"


def test_parse_invalid_url_raises() -> None:
    with pytest.raises(DriveUrlInvalida):
        parse_drive_file_id("https://example.com/not-a-drive-url")


def test_parse_empty_string_raises() -> None:
    with pytest.raises(DriveUrlInvalida):
        parse_drive_file_id("")


def test_parse_file_id_with_hyphens_and_underscores() -> None:
    url = "https://drive.google.com/file/d/1a_B-Cd2/view"
    assert parse_drive_file_id(url) == "1a_B-Cd2"
