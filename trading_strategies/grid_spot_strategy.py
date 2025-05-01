import secrets
import string
from typing import Optional

from configs.settings import Settings
from models.grid_levels import GridLevels
from models.grid_thresholds import GridThresholds
from models.order import Order
from trading_strategies.base_strategy import BaseTradingStrategy
from utils.logging_utils import setup_logger
from decimal import Decimal, ROUND_DOWN


logger = setup_logger(log_dir="logs", days_to_keep=30)


class GridSpotStrategy(BaseTradingStrategy):
    def __init__(self, order_manager):
        self.settings = Settings()
        self.grid_levels = GridLevels(levels=[], min=0, max=0)
        self.balance = 0
        #TODO: maybe store in somewhere
        self.trade_results = []

        self.order_manager = order_manager
        logger.info("GridSpotStrategy initialized.")

    def make_decision(self, current_price: float, timestamp: int) -> Optional[Order]:
        if not self.__is_price_within_grid(current_price):
            return None

        thresholds = self.__calculate_grid_thresholds(current_price)

        if self.__should_buy(current_price, thresholds):
            return self.__execute_buy(current_price, thresholds.amount_to_spend)

        if self.__should_sell(current_price, thresholds):
            return self.__execute_sell(current_price, timestamp)

        return None

    def log_grid_levels_and_zone(self, current_price: float) -> None:
        if not self.__is_price_within_grid(current_price):
            logger.info(f"Current price {current_price:.2f} is outside the grid range.")
            return

        thresholds = self.__calculate_grid_thresholds(current_price)
        lower = thresholds.lower_grid
        upper = thresholds.upper_grid

        if lower is not None:
            logger.info(f"Nearest lower grid: {lower}")
        else:
            logger.info("No lower grid found.")

        if upper is not None:
            logger.info(f"Nearest upper grid: {upper}")
        else:
            logger.info("No upper grid found.")

        if lower is not None and lower <= current_price < thresholds.lower_buy_threshold:
            logger.info(f"Zone: BUY zone (between {lower} and {thresholds.lower_buy_threshold:.2f})")
        elif upper is not None and upper >= current_price > thresholds.upper_sell_threshold:
            logger.info(f"Zone: SELL zone (between {upper} and {thresholds.upper_sell_threshold:.2f})")
        else:
            logger.info("Zone: No-action zone")

    def __is_price_within_grid(self, current_price) -> bool:
        if current_price < self.grid_levels.min or current_price > self.grid_levels.max:
            logger.info(f"Current price {current_price:.2f} is out of grid range. No action taken.")
            return False
        return True

    def __calculate_grid_thresholds(self, current_price) -> GridThresholds:
        lower_grid = max((level for level in self.grid_levels.levels if level <= current_price), default=None)
        upper_grid = min((level for level in self.grid_levels.levels if level >= current_price), default=None)

        grid_distance = upper_grid - lower_grid if lower_grid is not None and upper_grid is not None else 0
        lower_buy_threshold = lower_grid + grid_distance * 0.30 if lower_grid is not None else None
        upper_sell_threshold = upper_grid - grid_distance * 0.30 if upper_grid is not None else None

        calculated_amount_to_spend = self.balance * self.settings.buy_percentage
        amount_to_spend = max(calculated_amount_to_spend, self.settings.min_transaction_amount)

        return GridThresholds(
            lower_grid=lower_grid,
            upper_grid=upper_grid,
            lower_buy_threshold=lower_buy_threshold,
            upper_sell_threshold=upper_sell_threshold,
            amount_to_spend=amount_to_spend
        )

    def __should_buy(self, current_price, thresholds: GridThresholds) -> bool:
        if thresholds.lower_grid is not None and thresholds.lower_grid <= current_price < thresholds.lower_buy_threshold \
                and self.balance >= thresholds.amount_to_spend:
            return True
        return False

    def __should_sell(self, current_price, thresholds: GridThresholds) -> bool:
        if thresholds.upper_grid is not None and thresholds.upper_grid >= current_price > thresholds.upper_sell_threshold:
            return True
        return False

    def __execute_buy(self, current_price: float, amount_to_spend: float) -> Optional[Order]:
        bought_amount = amount_to_spend / current_price
        rounded_bought_amount = self.__round_to_precision(bought_amount)

        if rounded_bought_amount == 0:
            logger.info(f"Buy skipped. Rounded bought amount is 0. Current price: {current_price:.2f}, "
                        f"Amount to spend: {amount_to_spend:.2f}, Rounded Amount: {rounded_bought_amount:.6f}")
            return None

        if rounded_bought_amount * current_price > self.balance:
            logger.info("Buy skipped. Not enough money.")
            return None

        order_link_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        logger.info(f"Buy decision made @ {current_price:.7f}, Amount: {rounded_bought_amount:.6f}")

        return Order(
            order_link_id=order_link_id,
            amount=rounded_bought_amount,
            price=current_price,
            allow_to_sell=False,
            action="Buy"
        )

    def __execute_sell(self, current_price: float, timestamp: int) -> Optional[Order]:
        sorted_orders = sorted(self.order_manager.get_orders(), key=lambda order: order.price)

        active_order = next(
            (order for order in sorted_orders if (current_price - order.price) * order.amount > 0.12 and order.allow_to_sell),
            None
        )

        if active_order:
            profit = (current_price - active_order.price) * active_order.amount
            sale_amount = active_order.amount * current_price
            order_link_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))

            self.balance += sale_amount

            self.trade_results.append({
                "action": "Sell",
                "buy_price": active_order.price,
                "sell_price": current_price,
                "amount": active_order.amount,
                "profit": profit,
                "timestamp": timestamp,
            })

            logger.info(
                f"Sell executed @ {current_price:.7f}, Profit: {profit:.2f}, Sold Amount: {sale_amount:.2f}, Updated Balance: {self.balance:.2f}"
            )

            return Order(
                order_link_id=order_link_id,
                amount=active_order.amount,
                price=current_price,
                allow_to_sell=False,
                action="Sell",
                buy_order_link_id=active_order.order_link_id
            )

        logger.info("No valid order found for selling.")
        return None

    def __round_to_precision(self, value):
        decimal_value = Decimal(value)
        rounded_value = decimal_value.quantize(Decimal(f'1e-{self.settings.qty_precision}'), rounding=ROUND_DOWN)
        return float(rounded_value)