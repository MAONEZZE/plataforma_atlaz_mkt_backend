from app.domain.shared.base_exceptions import DomainError


class UserNotFound(DomainError):
    pass


class InvalidPhoto(DomainError):
    pass
