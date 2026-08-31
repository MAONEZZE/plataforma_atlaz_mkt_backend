import asyncio
from functools import partial
from uuid import UUID

from supabase import Client

from app.api.config.settings import settings


class SupabaseEventImageGateway:
    def __init__(self, client: Client) -> None:
        self._client = client
        self._bucket = settings.SUPABASE_BUCKET

    async def upload(
        self,
        event_id: UUID,
        data: bytes,
        content_type: str,
        extension: str,
    ) -> str:
        path = f"pictures/events/{event_id}.{extension}"
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            partial(
                self._client.storage.from_(self._bucket).upload,
                path,
                data,
                file_options={"content-type": content_type, "upsert": "true"},
            ),
        )
        return self._client.storage.from_(self._bucket).get_public_url(path)
