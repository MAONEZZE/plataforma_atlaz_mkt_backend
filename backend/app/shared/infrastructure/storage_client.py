from supabase import Client

from app.core.config import settings


class SupabaseStorage:
    def __init__(self, client: Client) -> None:
        self._client = client
        self._bucket = settings.SUPABASE_BUCKET

    def upload(self, path: str, data: bytes, content_type: str) -> str:
        self._client.storage.from_(self._bucket).upload(path, data, {"content-type": content_type})
        return self._client.storage.from_(self._bucket).get_public_url(path)
