import json
from uuid import uuid4

from app.contexts.community.application.dtos import ListCommunityResultDTO
from app.contexts.community.application.use_cases.list_community import ListarComunidade
from app.contexts.community.domain.entities import CommunityMember
from app.contexts.community.presentation.schemas import (
    ListarComunidadeResponse,
    CommunityMemberSchema,
)


class _FakeRepo:
    def __init__(self, membros: list[CommunityMember], total: int) -> None:
        self._membros = membros
        self._total = total
        self.called_with: tuple[int, int] | None = None

    async def list_active(self, page: int, page_size: int) -> tuple[list[CommunityMember], int]:
        self.called_with = (page, page_size)
        return self._membros, self._total


def _make_membro(
    nome: str = "Ana",
    foto_url: str | None = None,
    linkedin_url: str | None = None,
    instagram_username: str | None = None,
) -> CommunityMember:
    return CommunityMember(
        id=uuid4(),
        nome=nome,
        foto_url=foto_url,
        linkedin_url=linkedin_url,
        instagram_username=instagram_username,
    )


async def test_use_case_returns_correct_shape() -> None:
    membro = _make_membro(nome="João", foto_url="https://x.com/foto.jpg")
    repo = _FakeRepo([membro], total=1)
    result = await ListarComunidade(repo).execute(page=1, page_size=24)

    assert isinstance(result, ListCommunityResultDTO)
    assert result.page == 1
    assert result.page_size == 24
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].nome == "João"
    assert result.items[0].foto_url == "https://x.com/foto.jpg"


async def test_use_case_passes_pagination_to_repo() -> None:
    repo = _FakeRepo([], total=0)
    await ListarComunidade(repo).execute(page=3, page_size=10)
    assert repo.called_with == (3, 10)


async def test_use_case_optional_fields_can_be_none() -> None:
    membro = _make_membro(nome="Maria")
    repo = _FakeRepo([membro], total=1)
    result = await ListarComunidade(repo).execute(page=1, page_size=24)

    item = result.items[0]
    assert item.linkedin_url is None
    assert item.instagram_username is None
    assert item.foto_url is None


async def test_use_case_empty_result() -> None:
    repo = _FakeRepo([], total=0)
    result = await ListarComunidade(repo).execute(page=1, page_size=24)

    assert result.items == []
    assert result.total == 0


async def test_use_case_maps_all_fields() -> None:
    uid = uuid4()
    membro = CommunityMember(
        id=uid,
        nome="Carlos",
        foto_url="https://foto.com",
        linkedin_url="https://linkedin.com/in/carlos",
        instagram_username="carlos.ig",
    )
    repo = _FakeRepo([membro], total=1)
    result = await ListarComunidade(repo).execute(page=1, page_size=24)

    dto = result.items[0]
    assert dto.id == uid
    assert dto.nome == "Carlos"
    assert dto.foto_url == "https://foto.com"
    assert dto.linkedin_url == "https://linkedin.com/in/carlos"
    assert dto.instagram_username == "carlos.ig"


def test_response_schema_never_contains_telefone() -> None:
    schema = CommunityMemberSchema(
        id=uuid4(),
        nome="Test",
        foto_url=None,
        linkedin_url=None,
        instagram_username=None,
    )
    data = json.loads(schema.model_dump_json())
    assert "telefone" not in data


def test_list_response_schema_never_contains_telefone() -> None:
    response = ListarComunidadeResponse(
        items=[
            CommunityMemberSchema(
                id=uuid4(),
                nome="Test",
                foto_url=None,
                linkedin_url=None,
                instagram_username=None,
            )
        ],
        page=1,
        page_size=24,
        total=1,
    )
    data = json.loads(response.model_dump_json())
    for item in data["items"]:
        assert "telefone" not in item


async def test_use_case_multiple_items_order_preserved() -> None:
    membros = [_make_membro(nome=n) for n in ["Ana", "Bia", "Carlos"]]
    repo = _FakeRepo(membros, total=3)
    result = await ListarComunidade(repo).execute(page=1, page_size=24)

    nomes = [item.nome for item in result.items]
    assert nomes == ["Ana", "Bia", "Carlos"]
