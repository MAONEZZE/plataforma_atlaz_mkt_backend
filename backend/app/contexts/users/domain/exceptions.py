from app.shared.domain.exceptions import DomainError


class UserNotFound(DomainError):
    pass


class InvalidPhoto(DomainError):
    pass
