from app.shared.domain.exceptions import DomainError


class TrilhaNaoEncontrada(DomainError):
    pass


class ModuloNaoEncontrado(DomainError):
    pass


class AulaNaoEncontrada(DomainError):
    pass


class ComentarioNaoEncontrado(DomainError):
    pass


class ComentarioNaoPertenceAoUsuario(DomainError):
    pass


class DriveUrlInvalida(DomainError):
    def __init__(self, url: str) -> None:
        super().__init__(f"URL do Google Drive inválida: {url}")
