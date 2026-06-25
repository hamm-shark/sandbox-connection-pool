class ClientCallError(Exception):
    message = "Client call failed"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)


class PaymentError(ClientCallError):
    """Имитация ошибки платежного сервиса."""

    message: str = "Payment service is unavailable"


class DomesticServiceError(ClientCallError):
    """Имитация ошибки работы сервиса."""

    message: str = "Domestic service is unavailable"
