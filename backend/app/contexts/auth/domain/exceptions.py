from app.shared.domain.exceptions import DomainError


class TokenInvalido(DomainError):
    pass


class TokenExpirado(DomainError):
    pass


class ContaInativa(DomainError):
    pass


class CredenciaisInvalidas(DomainError):
    pass


class LogoutFalhou(DomainError):
    pass
