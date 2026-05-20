from uuid import UUID

from supabase import Client

from app.api.config.settings import settings


class SupabaseStorageGateway:
    def __init__(self, client: Client) -> None:
        self._client = client
        self._bucket = settings.SUPABASE_BUCKET

    def upload(
        self,
        user_id: UUID,
        data: bytes,
        content_type: str,
        extension: str,
    ) -> str:
        path = f"{user_id}.{extension}"
        self._client.storage.from_(self._bucket).upload(
            path,
            data,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        return self._client.storage.from_(self._bucket).get_public_url(path)
