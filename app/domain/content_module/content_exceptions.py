from app.domain.shared.base_exceptions import DomainError


class TrackNotFound(DomainError):
    pass


class ModuleNotFound(DomainError):
    pass


class LessonNotFound(DomainError):
    pass


class CommentNotFound(DomainError):
    pass


class CommentNotOwnedByUser(DomainError):
    pass


class InvalidDriveUrl(DomainError):
    def __init__(self, url: str) -> None:
        super().__init__(f"URL do Google Drive inválida: {url}")
