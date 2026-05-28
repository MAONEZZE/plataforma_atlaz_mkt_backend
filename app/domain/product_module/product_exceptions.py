from app.domain.shared.base_exceptions import DomainError


class ProductNotFound(DomainError):
    pass


class ProductInUse(DomainError):
    pass
