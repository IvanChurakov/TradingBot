import json
import time
from datetime import datetime

from api_managers.bybit_api_manager import BybitAPIManager
from bot.grid_levels_calculator import GridLevelsCalculator
from configs.settings import Settings
from data.bybit_market_data import BybitMarketData
from order_managers.backtest_order_manager import BacktestOrderManager
from order_managers.dynamodb_order_manager import DynamoDBOrderManager
from traders.backtest_trader import BacktestTrader
from traders.bybit_trader import BybitTrader
from trading_strategies.grid_spot_strategy import GridSpotStrategy
from utils.datetime_utils import format_timestamp
from utils.logging_utils import setup_logger
from utils.telegram_utils import send_telegram_notification


logger = setup_logger(log_dir="logs", days_to_keep=30)


class GridBot:
    def __init__(self):
        self.settings = Settings()

        logger.info("HTTP session initialized with API keys.")

        self.api_manager = BybitAPIManager(self.settings.api_key, self.settings.api_secret)
        self.market_data = BybitMarketData(self.api_manager)
        self.trader = BybitTrader(self.api_manager)
        self.grid_levels_calculator = GridLevelsCalculator()
        self.order_manager = DynamoDBOrderManager()
        self.grid_spot_strategy = GridSpotStrategy(self.order_manager)
        logger.info("GridBot modules initialized successfully.")

    def run_real_time_bot(self):
        logger.info("Starting Grid Bot...")
        send_telegram_notification("Starting Grid Bot...")

        grid_recalculation_interval_days = 1
        recalculation_interval_ms = grid_recalculation_interval_days * 24 * 60 * 60 * 1000
        next_grid_recalculation_time = int(time.time() * 1000)

        while True:
            try:
                current_datetime_timestamp = int(time.time() * 1000)

                if current_datetime_timestamp >= next_grid_recalculation_time:
                    self.refresh_data(current_datetime_timestamp)
                    next_grid_recalculation_time += recalculation_interval_ms

                self.grid_spot_strategy.order_manager.update_positions(self.trader)

                self.grid_spot_strategy.balance = self.trader.get_available_coin_balance("USDT")

                close_price = self.market_data.get_current_price(self.settings.symbol)

                order = self.grid_spot_strategy.make_decision(close_price, timestamp=current_datetime_timestamp)
                if order:
                    logger.info(f"Decision made: {order}")

                    order_placement_result = self.trader.place_order(self.settings.symbol, order)
                    if order_placement_result and order_placement_result.success:
                        if order.action == "Buy":
                            self.order_manager.add_order(order)
                            logger.info(f"Buy order recorded in state manager: {order.order_link_id}")

                        if order.action == "Sell":
                            self.order_manager.remove_order(order.buy_order_link_id)
                            logger.info(f"Sell order removed from state manager: {order.buy_order_link_id}")

                        action = order.action
                        portfolio_balance = self.trader.get_portfolio_balance()

                        message = None

                        if action == "Buy":
                            message = (
                                f"📈 *Grid Bot {action} Alert*\n\n"
                                f"🔹 *Symbol*: {self.settings.symbol}\n"
                                f"💵 *Buy Price*: {order.price:.2f}\n"
                                f"💰 *Bought Amount*: {order.amount:.6f}\n"
                                f"🔗 *Order Link ID*: {order.order_link_id}\n\n"
                                f"{portfolio_balance.generate_balance_string()}"
                            )
                        elif action == "Sell":
                            last_trade = self.grid_spot_strategy.trade_results[-1]

                            message = (
                                f"📉 *Grid Bot {action} Alert*\n\n"
                                f"🔹 *Symbol*: {self.settings.symbol}\n"
                                f"💵 *Buy Price*: {last_trade['buy_price']:.2f}\n"
                                f"💵 *Sell Price*: {order.price:.2f}\n"
                                f"💰 *Sold Amount*: {order.amount:.6f}\n"
                                f"💸 *Profit*: {last_trade['profit']:.2f} USDT\n\n"
                                f"{portfolio_balance.generate_balance_string()}"
                            )

                        if message:
                            send_telegram_notification(message)

                time.sleep(self.settings.trading_interval)

            except Exception as e:
                logger.error(f"Error occurred in the bot loop: {e}", exc_info=True)

                error_message = f"🚨 An error occurred in the bot loop: {e}"
                send_telegram_notification(error_message)

                break

    def run_backtest(self, from_timestamp, to_timestamp, use_real_data=False):
        self.trader = BacktestTrader(initial_balance=300)
        self.order_manager = BacktestOrderManager()
        self.grid_spot_strategy = GridSpotStrategy(self.order_manager)

        logger.info("Starting Grid Bot Backtest...")

        grid_recalculation_interval_days = 1
        recalculation_interval_ms = grid_recalculation_interval_days * 24 * 60 * 60 * 1000

        backtest_price_data = self.fetch_historical_data(from_timestamp, to_timestamp, use_real_data)
        if not backtest_price_data:
            logger.warning("Insufficient data for backtest. Terminating backtest.")
            return

        test_price_data = [
            price_data for price_data in backtest_price_data
            if from_timestamp <= price_data["timestamp"] <= to_timestamp
        ]

        next_grid_recalculation_time = from_timestamp

        for price_data in test_price_data:
            current_datetime_timestamp = price_data["timestamp"]
            close_price = float(price_data["price"])

            if current_datetime_timestamp >= next_grid_recalculation_time:
                filtered_historical_prices = [
                    item["price"] for item in backtest_price_data
                    if current_datetime_timestamp - (self.settings.grid_historical_days * 24 * 60 * 60 * 1000) <= item["timestamp"] < current_datetime_timestamp
                ]

                if len(filtered_historical_prices) == 0:
                    current_datetime_human_readable = datetime.fromtimestamp(
                        current_datetime_timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    logger.warning(
                        f"No historical prices available for calculation. Current time: {current_datetime_human_readable}")
                else:
                    self.grid_spot_strategy.grid_levels = self.grid_levels_calculator.calculate_grid_levels_with_percentile(
                        filtered_historical_prices, self.settings.grid_levels_count
                    )

                next_grid_recalculation_time += recalculation_interval_ms

            self.grid_spot_strategy.balance = self.trader.get_available_coin_balance("USDT")

            order = self.grid_spot_strategy.make_decision(close_price, timestamp=current_datetime_timestamp)
            if order:
                logger.info(f"Decision made: {order}")

                order_placement_result = self.trader.place_order(self.settings.symbol, order)
                if order_placement_result and order_placement_result.success:
                    if order.action == "Buy":
                        self.order_manager.add_order(order)
                        logger.info(f"Buy order recorded in state manager: {order.order_link_id}")

                    if order.action == "Sell":
                        self.order_manager.remove_order(order.buy_order_link_id)
                        logger.info(f"Sell order removed from state manager: {order.buy_order_link_id}")

        results = self.grid_spot_strategy.trade_results
        total_profit = sum(trade["profit"] for trade in results if "profit" in trade)

        logger.info(f"Backtest finished. Total Profit: {total_profit:.2f} USDT")

    def refresh_data(self, current_datetime_timestamp):
        logger.info(f"Recalculating grid levels at {format_timestamp(current_datetime_timestamp)}...")

        start_time_for_calculation = current_datetime_timestamp - (
            self.settings.grid_historical_days * 24 * 60 * 60 * 1000
        )

        historical_price_data = self.market_data.fetch_data_for_period(
            self.settings.symbol,
            start_time_for_calculation,
            current_datetime_timestamp,
            "1"
        )

        historical_prices = [item["close_price"] for item in historical_price_data]

        if not historical_prices:
            logger.warning(f"No sufficient data for recalculation at {format_timestamp(current_datetime_timestamp)}")
        else:
            self.grid_spot_strategy.grid_levels = self.grid_levels_calculator.calculate_grid_levels_with_percentile(
                historical_prices, self.settings.grid_levels_count
            )

        self.grid_spot_strategy.min_order_amount = self.market_data.get_min_order_amt(self.settings.symbol)

    def fetch_historical_data(self, from_timestamp, to_timestamp, use_real_data):
        historical_duration_ms = self.settings.grid_historical_days * 24 * 60 * 60 * 1000

        if use_real_data:
            logger.info("Fetching real price data...")

            backtest_price_data = self.market_data.fetch_data_for_period(
                symbol=self.settings.symbol,
                start_datetime=from_timestamp - historical_duration_ms,
                end_datetime=to_timestamp,
                interval="1",
            )
        else:
            logger.info("Loading historical data from file...")
            try:
                with open("historical/btc_historical_data_sorted.json", "r") as file:
                    all_historical_data = json.load(file)
            except FileNotFoundError:
                logger.error("Error: Historical data file not found.")
                return None
            except json.JSONDecodeError:
                logger.error("Error: Failed to decode JSON data.")
                return None

            backtest_price_data = [
                p for p in all_historical_data
                if from_timestamp - historical_duration_ms <= p["timestamp"] <= to_timestamp
            ]

        if not backtest_price_data:
            logger.warning("No data found for the requested backtest period, including historical range.")
            return None

        return backtest_price_data