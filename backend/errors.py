class AppError(Exception):
    """An expected application failure that can be returned safely to clients."""

    def __init__(self, message: str, *, code: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class ConfigurationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, code="configuration_error", status_code=503)


class PlanningError(AppError):
    def __init__(self, message: str):
        super().__init__(message, code="planning_error", status_code=502)


class SearchError(AppError):
    def __init__(self, message: str):
        super().__init__(message, code="search_error", status_code=502)


class DocumentGenerationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, code="document_generation_error", status_code=500)
