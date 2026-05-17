class EntidadNoEncontrada(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConflictoUnicidad(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidacionNegocio(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SaldoInsuficiente(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class EliminacionBloqueada(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NoAutenticado(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class PermisoInsuficiente(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
