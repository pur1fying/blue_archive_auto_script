class PluginError(ValueError):
    """Stable public error; messages must not include source paths or secrets."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise PluginError(code, message)
