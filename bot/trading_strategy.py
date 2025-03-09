from bot.state_manager import StateManager
import secrets
import string
from configs.settings import Settings
from utils.logging_utils import setup_logger
from decimal import Decimal, ROUND_DOWN


logger = setup_logger(log_dir="logs", days_to_keep=30)

class TradingStrategy:
    def __init__(self):
        self.settings = Settings()
        self.grid_levels = {"levels": [], "min": None, "max": None}
        self.qty_precision = 6
        self.balance = 200
        self.trade_results = []

        self.state_manager = StateManager()
        logger.info("TradingStrategy initialized.")

    def process_price(self, current_price, timestamp):
        if current_price < min(self.grid_levels["levels"]) or current_price > max(self.grid_levels["levels"]):
            logger.info(f"Current price {current_price:.7f} is out of grid range. No action taken.")
            return None

        lower_grid = max((level for level in self.grid_levels["levels"] if level <= current_price), default=None)
        upper_grid = min((level for level in self.grid_levels["levels"] if level >= current_price), default=None)

        grid_distance = upper_grid - lower_grid
        lower_buy_threshold = lower_grid + grid_distance * 0.49
        upper_sell_threshold = upper_grid - grid_distance * 0.49

        calculated_amount_to_spend = self.balance * self.settings.buy_percentage
        amount_to_spend = max(calculated_amount_to_spend, self.settings.min_transaction_amount)

        if lower_grid <= current_price < lower_buy_threshold and self.balance >= amount_to_spend:
            bought_amount = amount_to_spend / current_price

            rounded_bought_amount = self.round_to_precision(bought_amount)

            if rounded_bought_amount == 0:
                logger.info(f"Buy skipped. Rounded bought amount is 0. Current price: {current_price:.2f}, "
                            f"Amount to spend: {amount_to_spend:.2f}, Rounded Amount: {rounded_bought_amount:.6f}")
                return None

            order_link_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))

            self.state_manager.add_order(order_link_id, rounded_bought_amount, current_price)
            self.balance -= amount_to_spend

            logger.info(f"Buy executed @ {current_price:.7f}, Amount: {rounded_bought_amount:.6f}, "
                        f"Remaining Balance: {self.balance:.2f}")
            return {
                "action": "Buy",
                "price": current_price,
                "amount": rounded_bought_amount,
                "orderLinkId": order_link_id
            }

        if upper_grid >= current_price > upper_sell_threshold:
            active_orders = self.state_manager.get_orders()

            active_order = next((order for order in active_orders if current_price > order["price"] and order["allowToSell"]), None)
            if active_order is not None:
                self.state_manager.remove_order(active_order["orderLinkId"])
                profit = (current_price - active_order["price"]) * active_order["amount"]
                sale_amount = active_order["amount"] * current_price
                order_link_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))

                self.balance += sale_amount

                self.trade_results.append({
                    "action": "Sell",
                    "buy_price": active_order["price"],
                    "sell_price": current_price,
                    "amount": active_order["amount"],
                    "profit": profit,
                    "timestamp": timestamp,
                })

                logger.info(f"SELL executed @ {current_price:.7f}, Profit: {profit:.2f}, "
                            f"Sold Amount: {sale_amount:.2f}, Updated Balance: {self.balance:.2f}")

                return {
                    "action": "Sell",
                    "price": current_price,
                    "amount": active_order['amount'],
                    "orderLinkId": order_link_id
                }

        return None

    def get_portfolio_balance(self, current_price):
        active_orders = self.state_manager.get_orders()

        usdt_balance = self.balance
        positions_usdt_value = sum(order["amount"] * current_price for order in active_orders)

        total_balance = usdt_balance + positions_usdt_value
        total_btc = sum(order["amount"] for order in active_orders)
        btc_bought_value = sum(order["amount"] * order["price"] for order in active_orders)

        result = {
            "usdt_balance": usdt_balance,
            "positions_usdt_value": positions_usdt_value,
            "btc_bought_value": btc_bought_value,
            "total_btc": total_btc,
            "total_balance": total_balance
        }

        logger.info(f"Portfolio Balance: "
                    f"USDT Balance = {usdt_balance:.2f}, "
                    f"BTC Value (current price) = {positions_usdt_value:.2f}, "
                    f"BTC Bought Value = {btc_bought_value:.2f}, "
                    f"Total BTC = {total_btc:.6f}, "
                    f"Total = {total_balance:.2f}")
        return result

    def round_to_precision(self, value):
        decimal_value = Decimal(value)
        rounded_value = decimal_value.quantize(Decimal(f'1e-{self.settings.qty_precision}'), rounding=ROUND_DOWN)
        return float(rounded_value)