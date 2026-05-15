"""Unit tests for scripts/criar_usuario.py.

Tests:
- Password validation (_validar_senha_forte)
- CLI: weak password rejected before calling Supabase Admin API
- CLI: valid input calls Supabase Admin API with correct data
- CLI: trigger message printed after create
"""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from scripts.criar_usuario import _validar_senha_forte, app

runner = CliRunner()

# ── _validar_senha_forte ──────────────────────────────────────────────────────


def test_valid_strong_password() -> None:
    assert _validar_senha_forte("Senha@123") is True


def test_valid_minimal_strong_password() -> None:
    assert _validar_senha_forte("Abcde123") is True


def test_weak_too_short() -> None:
    assert _validar_senha_forte("Ab1") is False


def test_weak_no_uppercase() -> None:
    assert _validar_senha_forte("senha1234") is False


def test_weak_no_digit() -> None:
    assert _validar_senha_forte("SenhaForte") is False


def test_weak_empty() -> None:
    assert _validar_senha_forte("") is False


def test_weak_exactly_7_chars() -> None:
    assert _validar_senha_forte("Abc1234") is False


def test_strong_exactly_8_chars() -> None:
    assert _validar_senha_forte("Abc12345") is True


# ── CLI: weak password exits before calling Supabase ─────────────────────────


def test_weak_password_exits_without_calling_supabase() -> None:
    with patch("scripts.criar_usuario.create_client") as mock_create:
        result = runner.invoke(
            app,
            ["--nome", "Maria", "--email", "maria@test.com", "--senha", "fraco", "--role", "cliente"],
        )
        assert result.exit_code != 0
        mock_create.assert_not_called()


def test_weak_password_prints_error_message() -> None:
    with patch("scripts.criar_usuario.create_client"):
        result = runner.invoke(
            app,
            ["--nome", "X", "--email", "x@x.com", "--senha", "abc", "--role", "cliente"],
        )
        assert "senha" in result.output.lower() or "erro" in result.output.lower()
        assert result.exit_code != 0


# ── CLI: invalid role rejected ────────────────────────────────────────────────


def test_invalid_role_rejected() -> None:
    with patch("scripts.criar_usuario.create_client") as mock_create:
        result = runner.invoke(
            app,
            ["--nome", "X", "--email", "x@x.com", "--senha", "Forte@123", "--role", "superuser"],
        )
        assert result.exit_code != 0
        mock_create.assert_not_called()


# ── CLI: valid input calls Supabase Admin API ─────────────────────────────────


def test_valid_input_calls_supabase_create_user() -> None:
    mock_user = MagicMock()
    mock_user.id = "uuid-1234"

    mock_response = MagicMock()
    mock_response.user = mock_user

    mock_supabase = MagicMock()
    mock_supabase.auth.admin.create_user.return_value = mock_response

    with patch("scripts.criar_usuario.create_client", return_value=mock_supabase):
        result = runner.invoke(
            app,
            [
                "--nome", "Maria Silva",
                "--email", "maria@test.com",
                "--senha", "Senha@123",
                "--role", "cliente",
            ],
        )
        assert result.exit_code == 0
        mock_supabase.auth.admin.create_user.assert_called_once()
        call_args = mock_supabase.auth.admin.create_user.call_args[0][0]
        assert call_args["email"] == "maria@test.com"
        assert call_args["password"] == "Senha@123"
        assert call_args["email_confirm"] is True
        assert call_args["user_metadata"]["nome"] == "Maria Silva"
        assert call_args["user_metadata"]["role"] == "cliente"


def test_trigger_message_printed_after_create() -> None:
    """After successful create, CLI must inform that the trigger created public.usuario."""
    mock_user = MagicMock()
    mock_user.id = "uuid-5678"

    mock_response = MagicMock()
    mock_response.user = mock_user

    mock_supabase = MagicMock()
    mock_supabase.auth.admin.create_user.return_value = mock_response

    with patch("scripts.criar_usuario.create_client", return_value=mock_supabase):
        result = runner.invoke(
            app,
            ["--nome", "Ana", "--email", "ana@test.com", "--senha", "Ana@12345", "--role", "admin"],
        )
        assert result.exit_code == 0
        assert "uuid-5678" in result.output
        assert "trigger" in result.output.lower() or "public.usuario" in result.output.lower()


def test_admin_role_accepted() -> None:
    mock_user = MagicMock()
    mock_user.id = "admin-uuid"

    mock_response = MagicMock()
    mock_response.user = mock_user

    mock_supabase = MagicMock()
    mock_supabase.auth.admin.create_user.return_value = mock_response

    with patch("scripts.criar_usuario.create_client", return_value=mock_supabase):
        result = runner.invoke(
            app,
            ["--nome", "Admin", "--email", "admin@test.com", "--senha", "Admin@123", "--role", "admin"],
        )
        assert result.exit_code == 0
        call_args = mock_supabase.auth.admin.create_user.call_args[0][0]
        assert call_args["user_metadata"]["role"] == "admin"


# ── CLI: telefone flag updates DB ─────────────────────────────────────────────


def test_telefone_param_triggers_db_update() -> None:
    mock_user = MagicMock()
    mock_user.id = "uuid-tel"

    mock_response = MagicMock()
    mock_response.user = mock_user

    mock_supabase = MagicMock()
    mock_supabase.auth.admin.create_user.return_value = mock_response

    mock_engine = MagicMock()

    # create_engine is imported inside the function, so patch the original source
    with (
        patch("scripts.criar_usuario.create_client", return_value=mock_supabase),
        patch("sqlalchemy.create_engine", return_value=mock_engine),
    ):
        result = runner.invoke(
            app,
            [
                "--nome", "Tel User",
                "--email", "tel@test.com",
                "--senha", "Tel@12345",
                "--role", "cliente",
                "--telefone", "+5511999999999",
            ],
        )
        assert result.exit_code == 0
        assert "telefone" in result.output.lower() or "+5511999999999" in result.output


# ── CLI: Supabase error handled gracefully ────────────────────────────────────


def test_supabase_error_exits_with_nonzero() -> None:
    mock_supabase = MagicMock()
    mock_supabase.auth.admin.create_user.side_effect = Exception("API error")

    with patch("scripts.criar_usuario.create_client", return_value=mock_supabase):
        result = runner.invoke(
            app,
            ["--nome", "X", "--email", "x@x.com", "--senha", "Forte@123", "--role", "cliente"],
        )
        assert result.exit_code != 0
