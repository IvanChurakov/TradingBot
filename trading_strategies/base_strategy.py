from abc import ABC, abstractmethod

class BaseTradingStrategy(ABC):
    def __init__(self, settings, market_data):
        self.settings = settings
        self.market_data = market_data

    @abstractmethod
    def make_decision(self, current_price, timestamp):
        pass