from dataclasses import dataclass

@dataclass
class SpotTradingDecision:
    action: str
    price: float
    amount: float
    orderLinkId: str