from unittest.mock import MagicMock
from uuid import uuid4

from app.api.config.dependencies.auth_deps import get_validate_token_use_case
from app.api.controllers.auth_module.auth_dto.auth_dto import AuthenticatedUserDTO
from app.services.auth_module.auth_service.validate_token_service import ValidateToken


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
