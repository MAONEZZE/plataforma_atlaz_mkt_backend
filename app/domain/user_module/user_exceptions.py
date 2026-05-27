from app.domain.shared.base_exceptions import DomainError


class UserNotFound(DomainError):
    pass


class InvalidPhoto(DomainError):
    pass


class EmailAlreadyRegistered(DomainError):
    pass


class SupabaseAdminError(DomainError):
    pass


class UserTriggerSyncFailed(DomainError):
    pass
