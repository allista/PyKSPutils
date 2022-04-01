class ExceptionChain(Exception):
    def __init__(self, message: str, cause: Exception = None) -> None:
        super().__init__(message)
        self.cause = cause

    def __str__(self):
        short = f"{super().__str__()}"
        if self.cause:
            return f"{short}: {self.cause}"
        return short
