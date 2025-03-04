import json
import os
from pathlib import Path
from utils.logging_utils import setup_logger


logger = setup_logger(log_dir="logs", days_to_keep=30)


class StateManager:
    def __init__(self, orders_file=None):
        if orders_file is None:
            if os.name == "nt":
                base_dir = Path(__file__).parent.parent
                data_dir = base_dir / "data" / "orders"
                data_dir.mkdir(parents=True, exist_ok=True)
                self.orders_file = os.path.join(data_dir, "orders.json")
            else:
                self.orders_file = "/home/ubuntu/orders.json"
        else:
            self.orders_file = orders_file

        self.orders = []
        self.load_orders()

    def load_orders(self):
        if os.path.exists(self.orders_file):
            logger.info(f"Loading orders from {self.orders_file}")
            with open(self.orders_file, "r") as file:
                self.orders = json.load(file)
        else:
            logger.warning(f"No orders file found at {self.orders_file}. Creating a new one.")
            self.save_orders()

    def save_orders(self):
        try:
            with open(self.orders_file, "w") as file:
                json.dump(self.orders, file, indent=4)
            logger.info(f"Orders saved to {self.orders_file}")
        except Exception as e:
            logger.error(f"Failed to save orders to {self.orders_file}: {e}", exc_info=True)

    def add_order(self, order_link_id, amount, price):
        new_order = {
            "orderLinkId": order_link_id,
            "amount": amount,
            "price": price,
            "allowToSell": False
        }
        self.orders.append(new_order)
        self.save_orders()
        logger.info(f"Order added: {new_order}")

    def remove_order(self, order_link_id):
        initial_len = len(self.orders)
        self.orders = [
            order for order in self.orders if order["orderLinkId"] != order_link_id
        ]
        if len(self.orders) < initial_len:
            self.save_orders()
            logger.info(f"Order with ID {order_link_id} removed.")
        else:
            logger.warning(f"No order found with ID {order_link_id} to remove.")

    def update_order(self, order_link_id, **fields):
        order_found = False
        for order in self.orders:
            if order["orderLinkId"] == order_link_id:
                for key, value in fields.items():
                    if key in order:
                        order[key] = value
                order_found = True
                break

        if order_found:
            self.save_orders()
            logger.info(f"Order with ID {order_link_id} updated with fields: {fields}.")
        else:
            logger.warning(f"Order with ID {order_link_id} not found for update.")

    def get_orders(self):
        logger.info(f"Fetching all orders. Total orders: {len(self.orders)}")
        return self.orders

    def get_order(self, order_link_id):
        for order in self.orders:
            if order["orderLinkId"] == order_link_id:
                logger.info(f"Order with ID {order_link_id} found.")
                return order
        logger.warning(f"Order with ID {order_link_id} not found.")
        return None