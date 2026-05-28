from app.domain.shared.base_exceptions import DomainError


class StageNotFound(DomainError):
    pass


class StageAlreadyAttached(DomainError):
    pass
