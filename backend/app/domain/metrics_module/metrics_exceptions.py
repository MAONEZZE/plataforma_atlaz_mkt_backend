class MetricNotFound(Exception):
    pass


class DuplicateMetric(Exception):
    pass


class MetricOutOfWindow(Exception):
    pass


class FutureWeekNotAllowed(Exception):
    pass


class MetricNotOwnedByUser(Exception):
    pass
