# Merged from: shared/domain/exceptions.py + core/exceptions.py


class DomainError(Exception):
    pass


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status: int,
        details: dict[str, str] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status = status
        self.details = details
        super().__init__(message)
