from decimal import Decimal
from typing import Union, Optional


class Order:
    def __init__(
            self,
            order_link_id: str,
            amount: Union[float, Decimal],
            price: Union[float, Decimal],
            allow_to_sell: bool = False,
            action: str = "",
            buy_order_link_id: Optional[str] = None
    ):
        self.order_link_id = order_link_id
        self.amount = Decimal(str(amount)) if isinstance(amount, float) else amount
        self.price = Decimal(str(price)) if isinstance(price, float) else price
        self.allow_to_sell = allow_to_sell
        self.action = action
        self.buy_order_link_id = buy_order_link_id

    def to_dict(self) -> dict:
        return {
            "orderLinkId": self.order_link_id,
            "amount": self.amount,
            "price": self.price,
            "allowToSell": self.allow_to_sell
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            order_link_id=data["orderLinkId"],
            amount=float(data["amount"]) if isinstance(data["amount"], Decimal) else data["amount"],
            price=float(data["price"]) if isinstance(data["price"], Decimal) else data["price"],
            allow_to_sell=data.get("allowToSell", False)
        )