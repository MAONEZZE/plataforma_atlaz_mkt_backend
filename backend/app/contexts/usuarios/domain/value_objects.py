import re
from dataclasses import dataclass
from typing import ClassVar

from app.shared.domain.exceptions import DomainError


@dataclass(frozen=True)
class LinkedinUrl:
    value: str

    def __post_init__(self) -> None:
        if self.value and "linkedin.com" not in self.value:
            raise DomainError("LinkedIn URL inválida. Deve conter 'linkedin.com'.")


@dataclass(frozen=True)
class InstagramUsername:
    value: str

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^[a-zA-Z0-9_.]{1,30}$")

    def __post_init__(self) -> None:
        if self.value and not self._PATTERN.match(self.value):
            raise DomainError(
                "Instagram username inválido. Use letras, números, _ ou . (máx. 30)."
            )


@dataclass(frozen=True)
class Telefone:
    value: str

    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^\+?\d{10,15}$")

    def __post_init__(self) -> None:
        if self.value and not self._PATTERN.match(self.value):
            raise DomainError("Telefone inválido. Use formato +XXXXXXXXXXX.")
