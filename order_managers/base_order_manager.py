from abc import ABC, abstractmethod
from typing import List, Optional
from models.order import Order

class BaseOrderManager(ABC):
    @abstractmethod
    def add_order(self, order: Order) -> None:
        pass

    @abstractmethod
    def remove_order(self, order_link_id: str) -> None:
        pass

    @abstractmethod
    def update_order(self, order_link_id: str, **fields) -> None:
        pass

    @abstractmethod
    def get_orders(self) -> List[Order]:
        pass

    @abstractmethod
    def get_order(self, order_link_id: str) -> Optional[Order]:
        pass

    @abstractmethod
    def update_positions(self, trader) -> None:
        pass