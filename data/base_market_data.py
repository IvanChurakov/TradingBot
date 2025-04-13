from abc import ABC, abstractmethod
from typing import List, Dict, Union


class BaseMarketData(ABC):
    @abstractmethod
    def get_min_order_amt(self, symbol: str) -> float:
        pass

    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        pass

    @abstractmethod
    def fetch_data_for_period(self, symbol: str, start_datetime: int, end_datetime: int, interval: str) -> List[Dict[str, Union[int, float]]]:
        pass