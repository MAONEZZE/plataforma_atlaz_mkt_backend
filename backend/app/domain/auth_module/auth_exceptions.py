from app.domain.shared.base_exceptions import DomainError


class InvalidToken(DomainError):
    pass


class ExpiredToken(DomainError):
    pass


class InactiveAccount(DomainError):
    pass


class InvalidCredentials(DomainError):
    pass


class LogoutFailed(DomainError):
    pass
