class KiwiError(Exception):
    pass


class AuthenticationError(KiwiError):
    pass


class NotFoundError(KiwiError):
    pass


class APIError(KiwiError):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")
