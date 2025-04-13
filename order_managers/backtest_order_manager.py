from typing import Optional, List, Union
from models.order import Order
from order_managers.base_order_manager import BaseOrderManager


class BacktestOrderManager(BaseOrderManager):
    def __init__(self):
        self.orders: List[Order] = []  # Список для зберігання об'єктів Order

    def add_order(self, order: Order):
        order.allow_to_sell = True
        self.orders.append(order)

    def remove_order(self, order_link_id: str):
        self.orders = [order for order in self.orders if order.order_link_id != order_link_id]

    def update_order(self, order_link_id: str, **fields):
        order = self.get_order(order_link_id)
        if order:
            for key, value in fields.items():
                if hasattr(order, key):
                    setattr(order, key, value)

    def get_orders(self) -> List[Order]:
        for order in self.orders:
            order.amount = float(order.amount)
            order.price = float(order.price)
        return self.orders

    def get_order(self, order_link_id: str) -> Optional[Order]:
        for order in self.orders:
            if order.order_link_id == order_link_id:
                order.amount = float(order.amount)
                order.price = float(order.price)
                return order
        return None

    def update_positions(self, trader):
        for order in self.orders:
            if not order.allow_to_sell:
                is_closed = trader.is_order_closed(order.order_link_id)
                if is_closed:
                    order.allow_to_sell = True