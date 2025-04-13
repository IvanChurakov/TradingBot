from abc import ABC, abstractmethod
from models.order import Order
from models.order_placement_result import OrderPlacementResult
from models.portfolio_balance import PortfolioBalance


class BaseTrader(ABC):
    @abstractmethod
    def get_available_coin_balance(self, coin: str, account_type: str = "UNIFIED") -> float:
        pass

    @abstractmethod
    def is_order_closed(self, order_link_id: str) -> bool:
        pass

    @abstractmethod
    def place_order(self, symbol: str, decision: Order) -> OrderPlacementResult:
        pass

    @abstractmethod
    def get_portfolio_balance(self, account_type: str = "UNIFIED") -> PortfolioBalance:
        pass