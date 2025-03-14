import json
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bot.grid_strategy import GridStrategy
from bot.trader import Trader
from bot.trading_strategy import TradingStrategy
from data.market_data import MarketData
from configs.settings import Settings
from pybit.unified_trading import HTTP
from utils.datetime_utils import format_timestamp
from utils.logging_utils import setup_logger
from utils.telegram_utils import send_telegram_notification


logger = setup_logger(log_dir="logs", days_to_keep=30)


class GridBot:
    def __init__(self):
        self.settings = Settings()

        self.http_session = self.create_http_session()
        logger.info("HTTP session initialized with API keys.")

        self.market_data = MarketData(self.http_session)
        self.trader = Trader(self.http_session)
        self.grid_strategy = GridStrategy()
        self.trading_strategy = TradingStrategy()
        logger.info("GridBot modules initialized successfully.")

    def create_http_session(self):
        return HTTP(
            testnet=False,
            api_key=self.settings.api_key,
            api_secret=self.settings.api_secret,
            timeout=30
        )

    def safe_api_call(self, api_func, *args, **kwargs):
        max_retries = 3
        retry_interval = 5

        for attempt in range(max_retries):
            try:
                send_telegram_notification("safe api call")
                return api_func(*args, **kwargs)

            except requests.exceptions.ReadTimeout as e:
                logger.warning(f"Read timeout occurred: {e}. Attempt {attempt + 1}/{max_retries}")

                if attempt < max_retries - 1:
                    time.sleep(retry_interval)
                    self.http_session = self.create_http_session()
                else:
                    logger.error(f"Read timeout after {max_retries} retries. Giving up...")
                    send_telegram_notification(f"⚠ API call failed due to timeout after {max_retries} retries.")
                    raise e

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection reset by peer: {e}. Attempt {attempt + 1}/{max_retries}")

                if attempt < max_retries - 1:
                    time.sleep(retry_interval)
                    self.http_session = self.create_http_session()
                else:
                    logger.error(f"Connection reset by peer after {max_retries} retries. Giving up...")
                    send_telegram_notification(
                        f"⚠ API call failed due to connection issues after {max_retries} retries.")
                    raise e

            except Exception as e:
                logger.error(f"Unexpected error occurred: {e}. Attempt {attempt + 1}/{max_retries}", exc_info=True)

                if attempt < max_retries - 1:
                    time.sleep(retry_interval)
                    self.http_session = self.create_http_session()
                else:
                    logger.error(f"Unexpected error after {max_retries} retries. Giving up...")
                    send_telegram_notification(f"⚠ Unexpected API call error: {e}")
                    raise e

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

                self.trading_strategy.balance = self.safe_api_call(self.trader.get_balance, "USDT")
                logger.info(f"Balance updated: {self.trading_strategy.balance:.2f} USDT")

                close_price = self.safe_api_call(self.market_data.get_current_price, self.settings.symbol)
                logger.info(f"Current Price: {close_price:.2f}")

                decision = self.trading_strategy.process_price(close_price, timestamp=current_datetime_timestamp)
                if decision:
                    logger.info(f"Decision made: {decision}")
                    self.safe_api_call(self.trader.place_order, self.settings.symbol, decision)

                    action = decision['action']
                    balance_info = self.trading_strategy.get_portfolio_balance(close_price)

                    balance_details = (
                        f"💹 **Portfolio Balance**:\n"
                        f"🔸 **USDT Balance**: {balance_info['usdt_balance']:.2f} USDT\n"
                        f"🔹 **BTC Value (at current price)**: {balance_info['positions_usdt_value']:.2f} USDT\n"
                        f"🔸 **BTC Bought Value**: {balance_info['btc_bought_value']:.2f} USDT\n"
                        f"🔹 **Total BTC**: {balance_info['total_btc']:.6f} BTC\n"
                        f"💼 **Total Portfolio Value**: {balance_info['total_balance']:.2f} USDT\n"
                    )

                    message = None

                    if action == "Buy":
                        message = (
                            f"📈 **Grid Bot {action} Alert**\n\n"
                            f"🔹 **Symbol**: {self.settings.symbol}\n"
                            f"💵 **Buy Price**: {decision['price']:.2f}\n"
                            f"💰 **Bought Amount**: {decision['amount']:.6f}\n"
                            f"🔗 **Order Link ID**: {decision['orderLinkId']}\n\n"
                            f"{balance_details}"
                        )
                    elif action == "Sell":
                        last_trade = self.trading_strategy.trade_results[-1]
                        profit = last_trade['profit']

                        message = (
                            f"📉 **Grid Bot {action} Alert**\n\n"
                            f"🔹 **Symbol**: {self.settings.symbol}\n"
                            f"💵 **Sell Price**: {decision['price']:.2f}\n"
                            f"💰 **Sold Amount**: {decision['amount']:.6f}\n"
                            f"💸 **Profit**: {profit:.2f} USDT\n\n"
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

    def refresh_data(self, current_datetime_timestamp):
        logger.info(f"Recalculating grid levels at {format_timestamp(current_datetime_timestamp)}...")

        start_time_for_calculation = current_datetime_timestamp - (
            self.settings.grid_historical_days * 24 * 60 * 60 * 1000
        )

        historical_price_data = self.safe_api_call(
            self.market_data.fetch_data_for_period,
            self.settings.symbol, start_time_for_calculation, current_datetime_timestamp, "1"
        )

        historical_prices = [item["close_price"] for item in historical_price_data]

        if not historical_prices:
            logger.warning(f"No sufficient data for recalculation at {format_timestamp(current_datetime_timestamp)}")
        else:
            self.trading_strategy.grid_levels = self.grid_strategy.calculate_grid_levels_with_percentile(
                historical_prices, self.settings.grid_levels_count
            )
            logger.info(f"Grid recalculated successfully with {len(self.trading_strategy.grid_levels['levels'])} levels.")

        logger.info(f"Retrieving min order amount at {format_timestamp(current_datetime_timestamp)}...")
        self.trading_strategy.min_order_amount = self.safe_api_call(self.market_data.get_min_order_amt, self.settings.symbol)

    def update_positions(self):
        active_orders = self.trading_strategy.state_manager.get_orders()

        for position in active_orders:
            if not position["allowToSell"]:
                order_link_id = position["orderLinkId"]
                logger.info(f"Checking order with orderLinkId: {order_link_id}...")

                if self.trader.is_order_closed(order_link_id):
                    logger.info(f"OrderLinkId {order_link_id} is closed. Marking as 'allowToSell'.")
                    self.trading_strategy.state_manager.update_order(order_link_id, allowToSell=True)
                else:
                    logger.info(f"Order with orderLinkId: {order_link_id} is still open.")

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
        self.trading_strategy.grid_levels = self.grid_strategy.calculate_grid_levels_with_percentile(
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
                    self.trading_strategy.grid_levels = self.grid_strategy.calculate_grid_levels_with_percentile(
                        relevant_prices, self.settings.grid_levels_count
                    )

                logger.info(f"Retrieving min order amount at {format_timestamp(timestamp)}...")

                if use_real_data:
                    self.trading_strategy.min_order_amount = self.market_data.get_min_order_amt(self.settings.symbol)
                else:
                    self.trading_strategy.min_order_amount = self.settings.min_transaction_amount

                next_grid_recalculation_time += recalculation_interval_ms

            decision = self.trading_strategy.process_price(close_price, timestamp=timestamp)

        total_profit = sum(
            trade["profit"] for trade in self.trading_strategy.trade_results if "profit" in trade
        )
        logger.info(f"Backtest finished successfully. Total Profit: {total_profit:.2f} USDT")

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