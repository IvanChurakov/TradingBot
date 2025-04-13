from dataclasses import dataclass
from typing import Optional

from models.order import Order


class SpotTradingDecision:
    def __init__(self, action: str, order: Order, buy_order_link_id: Optional[str] = None):
        self.action = action
        self.order = order
        self.buy_order_link_id = buy_order_link_id