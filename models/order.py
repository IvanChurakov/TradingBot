from decimal import Decimal
from typing import Optional


class Order:
    def __init__(
            self,
            order_link_id: str,
            amount: float,
            price: float,
            allow_to_sell: bool = False,
            action: str = "",
            buy_order_link_id: Optional[str] = None
    ):
        self.order_link_id = order_link_id
        self.amount = amount
        self.price = price
        self.allow_to_sell = allow_to_sell
        self.action = action
        self.buy_order_link_id = buy_order_link_id

    def to_dict(self) -> dict:
        return {
            "orderLinkId": self.order_link_id,
            "amount": Decimal(self.amount),
            "price": Decimal(self.price),
            "allowToSell": self.allow_to_sell
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            order_link_id=data["orderLinkId"],
            amount=float(data["amount"]),
            price=float(data["price"]),
            allow_to_sell=data.get("allowToSell", False)
        )