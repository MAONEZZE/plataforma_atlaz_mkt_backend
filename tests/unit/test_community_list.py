import json
from uuid import uuid4

from app.api.controllers.community_module.community_dto.community_dto import (
    CommunityMemberSchema,
    ListCommunityResponse,
    ListCommunityResultDTO,
)
from app.domain.community_module.community_model import CommunityMember
from app.services.community_module.community_service.list_community import ListCommunity


class _FakeRepo:
    def __init__(self, members: list[CommunityMember], total: int) -> None:
        self._members = members
        self._total = total
        self.called_with: tuple[int, int] | None = None

    async def list_active(self, page: int, page_size: int) -> tuple[list[CommunityMember], int]:
        self.called_with = (page, page_size)
        return self._members, self._total


def _make_member(
    name: str = "Ana",
    photo_url: str | None = None,
    linkedin_url: str | None = None,
    instagram_username: str | None = None,
) -> CommunityMember:
    return CommunityMember(
        id=uuid4(),
        name=name,
        photo_url=photo_url,
        linkedin_url=linkedin_url,
        instagram_username=instagram_username,
    )


async def test_use_case_returns_correct_shape() -> None:
    member = _make_member(name="João", photo_url="https://x.com/photo.jpg")
    repo = _FakeRepo([member], total=1)
    result = await ListCommunity(repo).execute(page=1, page_size=24)

    assert isinstance(result, ListCommunityResultDTO)
    assert result.page == 1
    assert result.page_size == 24
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].name == "João"
    assert result.items[0].photo_url == "https://x.com/photo.jpg"


async def test_use_case_passes_pagination_to_repo() -> None:
    repo = _FakeRepo([], total=0)
    await ListCommunity(repo).execute(page=3, page_size=10)
    assert repo.called_with == (3, 10)


async def test_use_case_optional_fields_can_be_none() -> None:
    member = _make_member(name="Maria")
    repo = _FakeRepo([member], total=1)
    result = await ListCommunity(repo).execute(page=1, page_size=24)

    item = result.items[0]
    assert item.linkedin_url is None
    assert item.instagram_username is None
    assert item.photo_url is None


async def test_use_case_empty_result() -> None:
    repo = _FakeRepo([], total=0)
    result = await ListCommunity(repo).execute(page=1, page_size=24)

    assert result.items == []
    assert result.total == 0


async def test_use_case_maps_all_fields() -> None:
    uid = uuid4()
    member = CommunityMember(
        id=uid,
        name="Carlos",
        photo_url="https://photo.com",
        linkedin_url="https://linkedin.com/in/carlos",
        instagram_username="carlos.ig",
    )
    repo = _FakeRepo([member], total=1)
    result = await ListCommunity(repo).execute(page=1, page_size=24)

    dto = result.items[0]
    assert dto.id == uid
    assert dto.name == "Carlos"
    assert dto.photo_url == "https://photo.com"
    assert dto.linkedin_url == "https://linkedin.com/in/carlos"
    assert dto.instagram_username == "carlos.ig"


def test_response_schema_fields() -> None:
    schema = CommunityMemberSchema(
        id=uuid4(),
        name="Test",
        photo_url=None,
        linkedin_url=None,
        instagram_username=None,
    )
    data = json.loads(schema.model_dump_json())
    assert "name" in data
    assert "telefone" not in data


def test_list_response_schema_fields() -> None:
    response = ListCommunityResponse(
        items=[
            CommunityMemberSchema(
                id=uuid4(),
                name="Test",
                photo_url=None,
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
        assert "name" in item
        assert "telefone" not in item


async def test_use_case_multiple_items_order_preserved() -> None:
    members = [_make_member(name=n) for n in ["Ana", "Bia", "Carlos"]]
    repo = _FakeRepo(members, total=3)
    result = await ListCommunity(repo).execute(page=1, page_size=24)

    names = [item.name for item in result.items]
    assert names == ["Ana", "Bia", "Carlos"]
