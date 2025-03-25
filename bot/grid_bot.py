import json
import time

from bot.api_manager import APIManager
from bot.grid_levels_calculator import GridLevelsCalculator
from bot.state_manager import StateManager
from bot.trader import Trader
from data.market_data import MarketData
from configs.settings import Settings
from trading_strategies.grid_spot_strategy import GridSpotStrategy
from utils.datetime_utils import format_timestamp
from utils.logging_utils import setup_logger
from utils.telegram_utils import send_telegram_notification


logger = setup_logger(log_dir="logs", days_to_keep=30)


class GridBot:
    def __init__(self):
        self.settings = Settings()

        logger.info("HTTP session initialized with API keys.")

        self.api_manager = APIManager(self.settings.api_key, self.settings.api_secret)
        self.market_data = MarketData(self.api_manager)
        self.trader = Trader(self.api_manager)
        self.grid_Levels_calculator = GridLevelsCalculator()
        self.state_manager = StateManager()
        self.grid_spot_strategy = GridSpotStrategy(self.state_manager)
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

                self.update_positions()

                self.grid_spot_strategy.balance = self.trader.get_balance("USDT")

                close_price = self.market_data.get_current_price(self.settings.symbol)

                decision = self.grid_spot_strategy.make_decision(close_price, timestamp=current_datetime_timestamp)
                if decision:
                    logger.info(f"Decision made: {decision}")

                    order_placement_result = self.trader.place_order(self.settings.symbol, decision)
                    if order_placement_result and order_placement_result.success:
                        if decision.action == "Buy":
                            self.state_manager.add_order(
                                decision.orderLinkId,
                                decision.amount,
                                decision.price
                            )
                            logger.info(f"Buy order recorded in state manager: {decision.orderLinkId}")

                        if decision.action == "Sell":
                            self.state_manager.remove_order(decision.orderLinkId)
                            logger.info(f"Sell order removed from state manager: {decision.orderLinkId}")

                        action = decision.action
                        balance_info = self.grid_spot_strategy.get_portfolio_balance(close_price)

                        balance_details = (
                            f"💹 *Portfolio Balance*:\n"
                            f"🔸 *USDT Balance*: {balance_info['usdt_balance']:.2f} USDT\n"
                            f"🔹 *BTC Value (at current price)*: {balance_info['positions_usdt_value']:.2f} USDT\n"
                            f"🔸 *BTC Bought Value*: {balance_info['btc_bought_value']:.2f} USDT\n"
                            f"🔹 *Total BTC*: {balance_info['total_btc']:.6f} BTC\n"
                            f"💼 *Total Portfolio Value*: {balance_info['total_balance']:.2f} USDT\n"
                        )

                        message = None

                        if action == "Buy":
                            message = (
                                f"📈 *Grid Bot {action} Alert*\n\n"
                                f"🔹 *Symbol*: {self.settings.symbol}\n"
                                f"💵 *Buy Price*: {decision.price:.2f}\n"
                                f"💰 *Bought Amount*: {decision.amount:.6f}\n"
                                f"🔗 *Order Link ID*: {decision.orderLinkId}\n\n"
                                f"{balance_details}"
                            )
                        elif action == "Sell":
                            last_trade = self.grid_spot_strategy.trade_results[-1]

                            message = (
                                f"📉 *Grid Bot {action} Alert*\n\n"
                                f"🔹 *Symbol*: {self.settings.symbol}\n"
                                f"💵 *Buy Price*: {last_trade['buy_price']:.2f}\n"
                                f"💵 *Sell Price*: {decision.price:.2f}\n"
                                f"💰 *Sold Amount*: {decision.amount:.6f}\n"
                                f"💸 *Profit*: {last_trade['profit']:.2f} USDT\n\n"
                                f"{balance_details}"
                            )

                        if message:
                            send_telegram_notification(message)

                time.sleep(self.settings.trading_interval)

            except Exception as e:
                logger.error(f"Error occurred in the bot loop: {e}", exc_info=True)

                error_message = f"🚨 An error occurred in the bot loop: {e}"
                send_telegram_notification(error_message)

                break

    def run_backtest(self, from_datetime, to_datetime, use_real_data=False):
        logger.info("Starting Backtest...")

        start = int(from_datetime.timestamp() * 1000)
        end = int(to_datetime.timestamp() * 1000)

        historical_price_data, backtest_price_data = self.fetch_historical_data(start, end, use_real_data)
        if historical_price_data is None or backtest_price_data is None:
            logger.error("Failed to fetch data for the backtest. Exiting...")
            return

        logger.info("Starting backtest simulation...")

        historical_prices = [item["close_price"] for item in historical_price_data]
        self.grid_spot_strategy.grid_levels = self.grid_Levels_calculator.calculate_grid_levels_with_percentile(
            historical_prices, self.settings.grid_levels_count
        )

        one_day_ms = 24 * 60 * 60 * 1000
        grid_recalculation_interval_days = 1
        recalculation_interval_ms = grid_recalculation_interval_days * one_day_ms
        next_grid_recalculation_time = start

        for point in backtest_price_data:
            timestamp = point["timestamp"]
            close_price = point["close_price"]

            if timestamp >= next_grid_recalculation_time:
                logger.info(f"Recalculating grid levels at {format_timestamp(timestamp)}...")

                start_time_for_calculation = timestamp - (self.settings.grid_historical_days * one_day_ms)
                relevant_prices = [
                    p["close_price"]
                    for p in historical_price_data + backtest_price_data
                    if start_time_for_calculation <= p["timestamp"] < timestamp
                ]

                if not relevant_prices:
                    logger.warning(f"No sufficient data for recalculation at {timestamp}")
                else:
                    self.grid_spot_strategy.grid_levels = self.grid_Levels_calculator.calculate_grid_levels_with_percentile(
                        relevant_prices, self.settings.grid_levels_count
                    )

                logger.info(f"Retrieving min order amount at {format_timestamp(timestamp)}...")

                if use_real_data:
                    self.grid_spot_strategy.min_order_amount = self.market_data.get_min_order_amt(self.settings.symbol)
                else:
                    self.grid_spot_strategy.min_order_amount = self.settings.min_transaction_amount

                next_grid_recalculation_time += recalculation_interval_ms

            decision = self.grid_spot_strategy.process_price(close_price, timestamp=timestamp)

        total_profit = sum(
            trade["profit"] for trade in self.grid_spot_strategy.trade_results if "profit" in trade
        )
        logger.info(f"Backtest finished successfully. Total Profit: {total_profit:.2f} USDT")

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
            self.grid_spot_strategy.grid_levels = self.grid_Levels_calculator.calculate_grid_levels_with_percentile(
                historical_prices, self.settings.grid_levels_count
            )

        self.grid_spot_strategy.min_order_amount = self.market_data.get_min_order_amt(self.settings.symbol)

    #TODO:Move to stateManager class
    def update_positions(self):
        active_orders = self.grid_spot_strategy.state_manager.get_orders()

        for position in active_orders:
            if not position["allowToSell"]:
                order_link_id = position["orderLinkId"]

                order_placement_result = self.trader.is_order_closed(order_link_id)
                if order_placement_result and order_placement_result == True:
                    logger.info(f"OrderLinkId {order_link_id} is closed. Marking as 'allowToSell'.")
                    self.grid_spot_strategy.state_manager.update_order(order_link_id, allowToSell=True)

    def fetch_historical_data(self, from_timestamp, to_timestamp, use_real_data):
        if use_real_data:
            logger.info("Fetching real price data...")
            historical_price_data = self.market_data.fetch_data_for_period(
                symbol=self.settings.symbol,
                start_datetime=from_timestamp - (self.settings.grid_historical_days * 24 * 60 * 60 * 1000),
                end_datetime=from_timestamp,
                interval="1",
            )

            backtest_price_data = self.market_data.fetch_data_for_period(
                symbol=self.settings.symbol,
                start_datetime=from_timestamp,
                end_datetime=to_timestamp,
                interval="1",
            )
        else:
            logger.info("Loading historical data from file...")
            try:
                with open("data/historical_data/btc_historical_data_sorted.json", "r") as file:
                    all_historical_data = json.load(file)
            except FileNotFoundError:
                logger.error("Error: Historical data file not found.")
                return None, None
            except json.JSONDecodeError:
                logger.error("Error: Failed to decode JSON data.")
                return None, None

            historical_price_data = [
                p for p in all_historical_data
                if from_timestamp - (self.settings.grid_historical_days * 24 * 60 * 60 * 1000) <= p["timestamp"] < from_timestamp
            ]

            backtest_price_data = [
                p for p in all_historical_data
                if from_timestamp <= p["timestamp"] <= to_timestamp
            ]

        if not historical_price_data:
            logger.warning("No historical data found for the grid calculation.")
            return None, None
        if not backtest_price_data:
            logger.warning("No data found for the backtest period.")
            return None, None

        return historical_price_data, backtest_price_data