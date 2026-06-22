from dataclasses import dataclass

from src.infra.postgres.transaction_manager import TransactionManager


@dataclass(slots=True)
class BaseController:
    """
    A controller class that delegates work to services, manages roles, and aggregates the response.
    """

    tr_manager: TransactionManager
