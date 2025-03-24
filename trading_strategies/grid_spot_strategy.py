import secrets
import string
from configs.settings import Settings
from models.grid_levels import GridLevels
from models.grid_thresholds import GridThresholds
from models.spot_trading_decision import SpotTradingDecision
from trading_strategies.base_strategy import BaseTradingStrategy
from utils.logging_utils import setup_logger
from decimal import Decimal, ROUND_DOWN


logger = setup_logger(log_dir="logs", days_to_keep=30)

class GridSpotStrategy(BaseTradingStrategy):
    def __init__(self, state_manager):
        self.settings = Settings()
        self.grid_levels = GridLevels(levels=[], min=0, max=0)
        self.balance = 0
        #TODO: maybe store in somewhere
        self.trade_results = []

        self.state_manager = state_manager
        logger.info("GridSpotStrategy initialized.")

    def make_decision(self, current_price, timestamp):
        if not self.is_price_within_grid(current_price):
            return None

        thresholds = self.calculate_grid_thresholds(current_price)
        logger.info(f"Thresholds calculated: {thresholds}")

        if self.should_buy(current_price, thresholds):
            return self.execute_buy(
                current_price,
                thresholds.lower_grid,
                thresholds.lower_buy_threshold,
                thresholds.amount_to_spend
            )

        if self.should_sell(current_price, thresholds):
            return self.execute_sell(
                current_price,
                thresholds.upper_grid,
                thresholds.upper_sell_threshold
            )

        return None

    def is_price_within_grid(self, current_price):
        if current_price < self.grid_levels.min or current_price > self.grid_levels.max:
            logger.info(f"Current price {current_price:.2f} is out of grid range. No action taken.")
            return False
        return True

    def calculate_grid_thresholds(self, current_price):
        lower_grid = max((level for level in self.grid_levels.levels if level <= current_price), default=None)
        upper_grid = min((level for level in self.grid_levels.levels if level >= current_price), default=None)

        grid_distance = upper_grid - lower_grid if lower_grid is not None and upper_grid is not None else 0
        lower_buy_threshold = lower_grid + grid_distance * 0.49 if lower_grid is not None else None
        upper_sell_threshold = upper_grid - grid_distance * 0.49 if upper_grid is not None else None

        calculated_amount_to_spend = self.balance * self.settings.buy_percentage
        amount_to_spend = max(calculated_amount_to_spend, self.settings.min_transaction_amount)

        return GridThresholds(
            lower_grid=lower_grid,
            upper_grid=upper_grid,
            lower_buy_threshold=lower_buy_threshold,
            upper_sell_threshold=upper_sell_threshold,
            amount_to_spend=amount_to_spend
        )

    def should_buy(self, current_price, thresholds: GridThresholds):
        if thresholds.lower_grid is not None and thresholds.lower_grid <= current_price < thresholds.lower_buy_threshold \
                and self.balance >= thresholds.amount_to_spend:
            return True
        return False

    def should_sell(self, current_price, thresholds: GridThresholds):
        if thresholds.upper_grid is not None and thresholds.upper_grid >= current_price > thresholds.upper_sell_threshold:
            return True
        return False

    def execute_buy(self, current_price, lower_grid, lower_buy_threshold, amount_to_spend):
        bought_amount = amount_to_spend / current_price
        rounded_bought_amount = self.round_to_precision(bought_amount)

        if rounded_bought_amount == 0:
            logger.info(f"Buy skipped. Rounded bought amount is 0. Current price: {current_price:.2f}, "
                        f"Amount to spend: {amount_to_spend:.2f}, Rounded Amount: {rounded_bought_amount:.6f}")
            return None

        if rounded_bought_amount * current_price > self.balance:
            logger.info("Buy skipped. Not enough money.")
            return None

        order_link_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        logger.info(f"Buy decision made @ {current_price:.7f}, Amount: {rounded_bought_amount:.6f}")
        return SpotTradingDecision(
            action="Buy",
            price=current_price,
            amount=rounded_bought_amount,
            orderLinkId=order_link_id
        )

    def execute_sell(self, current_price, upper_grid, upper_sell_threshold):
        active_orders = self.state_manager.get_orders()
        sorted_orders = sorted(active_orders, key=lambda order: order["price"])

        active_order = next(
            (order for order in sorted_orders if current_price > order["price"] and order["allowToSell"]),
            None
        )

        if active_order:
            profit = (current_price - active_order["price"]) * active_order["amount"]
            logger.info(f"Sell decision made @ {current_price:.7f}, Profit: {profit:.2f}")
            return SpotTradingDecision(
                action="Sell",
                price=current_price,
                amount=active_order["amount"],
                orderLinkId=active_order["orderLinkId"]
            )

        return None

    #TODO: move to trader class
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