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
            "amount": Decimal(str(self.amount)),
            "price": Decimal(str(self.price)),
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

    def __str__(self) -> str:
        return (
            f"Order("
            f"orderLinkId = {self.order_link_id}, "
            f"amount={self.amount}, "
            f"price={self.price}, "
            f"allowToSell={self.allow_to_sell}, "
            f"action={self.action}, "
            f"buy_order_link_id={self.buy_order_link_id}"
            f")"
        )