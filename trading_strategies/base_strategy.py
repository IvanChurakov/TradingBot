from abc import ABC, abstractmethod

class BaseTradingStrategy(ABC):
    @abstractmethod
    def make_decision(self, current_price, timestamp):
        pass