from app.shared.domain.exceptions import DomainError


class UsuarioNaoEncontrado(DomainError):
    pass


class FotoInvalida(DomainError):
    pass
