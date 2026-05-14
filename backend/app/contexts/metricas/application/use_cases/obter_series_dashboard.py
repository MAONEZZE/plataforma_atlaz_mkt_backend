from app.contexts.metricas.domain.repositories import MetricaRepository


class ObterSeriesDashboard:
    def __init__(self, repo: MetricaRepository) -> None:
        self._repo = repo

    async def execute(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise NotImplementedError
