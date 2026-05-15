import re

from app.contexts.conteudo.domain.exceptions import DriveUrlInvalida

DRIVE_PATTERNS = [
    re.compile(r"/file/d/([a-zA-Z0-9_-]+)"),
    re.compile(r"[?&]id=([a-zA-Z0-9_-]+)"),
]


def parse_drive_file_id(url: str) -> str:
    for p in DRIVE_PATTERNS:
        m = p.search(url)
        if m:
            return m.group(1)
    raise DriveUrlInvalida(url)
