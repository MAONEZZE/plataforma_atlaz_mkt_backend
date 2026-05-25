from unittest.mock import MagicMock
from uuid import uuid4

from app.api.config.dependencies.auth_deps import get_validate_token_use_case
from app.api.controllers.auth_module.auth_dto.auth_dto import AuthenticatedUserDTO
from app.services.auth_module.validate_token_service import ValidateToken


def test_authenticated_user_dto_fields() -> None:
    uid = uuid4()
    dto = AuthenticatedUserDTO(id=uid, email="x@x.com", role="admin")
    assert dto.id == uid
    assert dto.email == "x@x.com"
    assert dto.role == "admin"


def test_get_validate_token_use_case_returns_use_case() -> None:
    mock_session = MagicMock()
    uc = get_validate_token_use_case(session=mock_session)
    assert isinstance(uc, ValidateToken)


async def test_logout_no_block() -> None:
    """Logout.execute must use asyncio.to_thread so sync sign_out doesn't block event loop (Fix #4)."""
    import asyncio
    from unittest.mock import patch

    from app.services.auth_module.logout_service import Logout

    gateway = MagicMock()
    gateway.sign_out = MagicMock(return_value=None)
    uc = Logout(gateway)

    with patch("asyncio.to_thread", wraps=asyncio.to_thread) as mock_to_thread:
        await uc.execute("some-token")
        mock_to_thread.assert_called_once_with(gateway.sign_out, "some-token")
