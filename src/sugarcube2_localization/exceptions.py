class _BaseException(Exception):
    def __init__(self, message: str = "Some random exception occured"):
        self._message = message

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return self.message

    @property
    def message(self):
        return self._message


class GameRootNotExistException(_BaseException):
    def __init__(self):
        super().__init__(message="Game root is blank or not correct!")


__all__ = [
    "GameRootNotExistException",
]