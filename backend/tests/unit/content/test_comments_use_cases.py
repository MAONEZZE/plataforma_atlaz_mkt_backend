from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.contexts.content.application.use_cases.comments.delete import DeleteComment
from app.contexts.content.application.use_cases.comments.create import CreateComment
from app.contexts.content.application.use_cases.comments.edit import EditComment
from app.contexts.content.application.use_cases.comments.list import ListComments
from app.contexts.content.domain.entities import Aula, Comentario, CommentRead
from app.contexts.content.domain.exceptions import (
    LessonNotFound,
    CommentNotFound,
    ComentarioNaoPertenceAoUsuario,
)
from app.shared.application.dtos import PagedResponse


# ── Fake repos ─────────────────────────────────────────────────────────────────

class FakeAulaRepo:
    def __init__(self, aula: Lesson | None = None) -> None:
        self._aula = aula

    async def get_by_id(self, aula_id: UUID) -> Lesson | None:
        return self._aula if self._aula and self._aula.id == aula_id else None


class FakeComentarioRepo:
    def __init__(self, comentarios: list[Comment] | None = None) -> None:
        self._comentarios: list[Comment] = comentarios or []
        self._apagados: list[UUID] = []

    async def list_by_lesson(
        self, aula_id: UUID, page: int, page_size: int
    ) -> tuple[list[CommentRead], int]:
        items = [c for c in self._comentarios if c.aula_id == aula_id]
        total = len(items)
        offset = (page - 1) * page_size
        page_items = items[offset : offset + page_size]
        leituras = [
            CommentRead(
                id=c.id,
                aula_id=c.aula_id,
                usuario_id=c.usuario_id,
                texto=None if c.apagado_em else c.texto,
                criado_em=c.criado_em,
                editado_em=c.editado_em,
                apagado_em=c.apagado_em,
                autor_nome="Autor",
                autor_foto_url=None,
            )
            for c in page_items
        ]
        return leituras, total

    async def get_by_id(self, comentario_id: UUID) -> Comment | None:
        return next((c for c in self._comentarios if c.id == comentario_id), None)

    async def create(self, comentario: Comment) -> Comment:
        self._comentarios.append(comentario)
        return comentario

    async def update(self, comentario: Comment) -> Comment:
        self._comentarios = [comentario if c.id == comentario.id else c for c in self._comentarios]
        return comentario

    async def delete_comment(self, comentario_id: UUID) -> None:
        self._apagados.append(comentario_id)


def _make_aula() -> Lesson:
    return Lesson(
        id=uuid4(), modulo_id=uuid4(), titulo="Aula", descricao=None,
        drive_file_id="x", duracao_minutos=None, ordem=0, criado_em=datetime.now(tz=UTC)
    )


def _make_comentario(usuario_id: UUID, aula_id: UUID, texto: str = "Texto") -> Comment:
    return Comment(
        id=uuid4(),
        aula_id=aula_id,
        usuario_id=usuario_id,
        texto=texto,
        criado_em=datetime.now(tz=UTC),
        editado_em=None,
        apagado_em=None,
    )


# ── CreateComment ────────────────────────────────────────────────────────────

async def test_criar_comentario_ok() -> None:
    aula = _make_aula()
    comentario_repo = FakeComentarioRepo()
    use_case = CreateComment(FakeAulaRepo(aula), comentario_repo)
    c = await use_case.execute(aula.id, uuid4(), "Ótima aula!")
    assert c.texto == "Ótima aula!"
    assert len(comentario_repo._comentarios) == 1


async def test_criar_comentario_aula_nao_encontrada_raises() -> None:
    use_case = CreateComment(FakeAulaRepo(None), FakeComentarioRepo())
    with pytest.raises(LessonNotFound):
        await use_case.execute(uuid4(), uuid4(), "texto")


# ── EditComment ───────────────────────────────────────────────────────────

async def test_editar_comentario_proprio() -> None:
    usuario_id = uuid4()
    aula_id = uuid4()
    comentario = _make_comentario(usuario_id, aula_id)
    repo = FakeComentarioRepo([comentario])
    use_case = EditComment(repo)
    updated = await use_case.execute(comentario.id, usuario_id, False, "Novo texto")
    assert updated.texto == "Novo texto"
    assert updated.editado_em is not None


async def test_editar_comentario_outro_usuario_raises() -> None:
    outro_id = uuid4()
    comentario = _make_comentario(uuid4(), uuid4())
    repo = FakeComentarioRepo([comentario])
    use_case = EditComment(repo)
    with pytest.raises(ComentarioNaoPertenceAoUsuario):
        await use_case.execute(comentario.id, outro_id, False, "hack")


async def test_editar_comentario_admin_pode_editar_qualquer() -> None:
    comentario = _make_comentario(uuid4(), uuid4())
    repo = FakeComentarioRepo([comentario])
    use_case = EditComment(repo)
    updated = await use_case.execute(comentario.id, uuid4(), True, "Admin edit")
    assert updated.texto == "Admin edit"


async def test_editar_comentario_nao_encontrado_raises() -> None:
    use_case = EditComment(FakeComentarioRepo())
    with pytest.raises(CommentNotFound):
        await use_case.execute(uuid4(), uuid4(), False, "texto")


# ── DeleteComment ───────────────────────────────────────────────────────────

async def test_apagar_comentario_proprio() -> None:
    usuario_id = uuid4()
    comentario = _make_comentario(usuario_id, uuid4())
    repo = FakeComentarioRepo([comentario])
    use_case = DeleteComment(repo)
    await use_case.execute(comentario.id, usuario_id, False)
    assert comentario.id in repo._apagados


async def test_apagar_comentario_outro_usuario_raises() -> None:
    comentario = _make_comentario(uuid4(), uuid4())
    repo = FakeComentarioRepo([comentario])
    use_case = DeleteComment(repo)
    with pytest.raises(ComentarioNaoPertenceAoUsuario):
        await use_case.execute(comentario.id, uuid4(), False)


async def test_apagar_comentario_admin_pode_apagar_qualquer() -> None:
    comentario = _make_comentario(uuid4(), uuid4())
    repo = FakeComentarioRepo([comentario])
    use_case = DeleteComment(repo)
    await use_case.execute(comentario.id, uuid4(), True)
    assert comentario.id in repo._apagados


async def test_apagar_comentario_nao_encontrado_raises() -> None:
    use_case = DeleteComment(FakeComentarioRepo())
    with pytest.raises(CommentNotFound):
        await use_case.execute(uuid4(), uuid4(), False)


# ── ListComments ──────────────────────────────────────────────────────────

async def test_listar_comentarios_is_proprio_flag() -> None:
    current_user = uuid4()
    aula_id = uuid4()
    proprio = _make_comentario(current_user, aula_id)
    alheio = _make_comentario(uuid4(), aula_id)
    repo = FakeComentarioRepo([proprio, alheio])
    use_case = ListComments(repo)
    result: PagedResponse = await use_case.execute(aula_id, 1, 20, current_user)
    by_id = {c.id: c for c in result.items}
    assert by_id[proprio.id].is_proprio is True
    assert by_id[alheio.id].is_proprio is False


async def test_listar_comentarios_apagado_texto_null() -> None:
    current_user = uuid4()
    aula_id = uuid4()
    apagado = Comment(
        id=uuid4(), aula_id=aula_id, usuario_id=uuid4(), texto="secreto",
        criado_em=datetime.now(tz=UTC), editado_em=None, apagado_em=datetime.now(tz=UTC),
    )
    repo = FakeComentarioRepo([apagado])
    use_case = ListComments(repo)
    result = await use_case.execute(aula_id, 1, 20, current_user)
    assert result.items[0].texto is None


async def test_listar_comentarios_paginacao() -> None:
    current_user = uuid4()
    aula_id = uuid4()
    comentarios = [_make_comentario(uuid4(), aula_id) for _ in range(5)]
    repo = FakeComentarioRepo(comentarios)
    use_case = ListComments(repo)
    result = await use_case.execute(aula_id, 1, 3, current_user)
    assert result.total == 5
    assert len(result.items) == 3
    assert result.page == 1
    assert result.page_size == 3
