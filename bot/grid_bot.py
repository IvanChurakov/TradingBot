import json

from bot.grid_strategy import GridStrategy
from bot.trading_strategy import TradingStrategy
from data.market_data import MarketData
from configs.settings import Settings
from pybit.unified_trading import HTTP

class GridBot:
    def __init__(self):
        self.settings = Settings()

        self.http_session = HTTP(
            testnet=False,
            api_key=self.settings.api_key,
            api_secret=self.settings.api_secret,
        )

        self.market_data = MarketData(self.http_session)

        self.grid_strategy = GridStrategy()
        self.trading_strategy = TradingStrategy()

    def run_real_time_bot(self):
        print("Starting Grid Bot...")
        pass

    def run_backtest(self, from_datetime, to_datetime, use_real_data=False):
        print("Starting Backtest...")

        # Конвертуємо дати у мілісекунди
        start = int(from_datetime.timestamp() * 1000)
        end = int(to_datetime.timestamp() * 1000)

        # Звантажуємо історичні дані
        historical_price_data, backtest_price_data = self.fetch_historical_data(start, end, use_real_data)
        if historical_price_data is None or backtest_price_data is None:
            print("Failed to fetch data for the backtest. Exiting...")
            return

        print("Starting backtest simulation...")

        # Побудова грідів на основі історичних даних перед бектестом
        historical_prices = [item["close_price"] for item in historical_price_data]
        self.trading_strategy.grid_levels = self.grid_strategy.calculate_grid_levels_with_percentile(
            historical_prices, self.settings.grid_levels_count
        )

        # Запуск бектесту
        one_day_ms = 24 * 60 * 60 * 1000
        grid_recalculation_interval_days = 1
        recalculation_interval_ms = grid_recalculation_interval_days * one_day_ms
        next_grid_recalculation_time = start  # Час першого перерахунку грідів

        for point in backtest_price_data:
            timestamp = point["timestamp"]
            close_price = point["close_price"]

            # Перевіряємо, чи настав час для перерахунку грідів
            if timestamp >= next_grid_recalculation_time:
                print(f"Recalculating grid levels at {timestamp}...")

                # Дані за останній період (наприклад, 30 днів) для перерахунку
                start_time_for_calculation = timestamp - (self.settings.grid_historical_days * one_day_ms)
                relevant_prices = [
                    p["close_price"]
                    for p in historical_price_data + backtest_price_data
                    if start_time_for_calculation <= p["timestamp"] < timestamp
                ]

                if not relevant_prices:
                    print(f"No sufficient data for recalculation at {timestamp}")
                else:
                    self.trading_strategy.grid_levels = self.grid_strategy.calculate_grid_levels_with_percentile(
                        relevant_prices, self.settings.grid_levels_count
                    )

                next_grid_recalculation_time += recalculation_interval_ms

            # Обробляємо поточну ціну
            self.trading_strategy.process_price(close_price, timestamp=timestamp)

        # Підрахунок прибутку
        total_profit = sum(
            trade["profit"] for trade in self.trading_strategy.trade_results if "profit" in trade
        )
        print(f"Backtest finished successfully.\nTotal Profit: {total_profit:.2f} USDT")

        # Баланс портфеля
        portfolio_balance = self.trading_strategy.get_portfolio_balance(
            backtest_price_data[-1]["close_price"]
        )

    def fetch_historical_data(self, from_timestamp, to_timestamp, use_real_data):
        if use_real_data:
            print(f"Fetching real price data...")
            # Ретриваємо реальні дані для історичного періоду та основного тестового періоду
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
            print(f"Loading historical data from file...")
            try:
                # Читаємо дані з файлу
                with open("data/historical_data/btc_historical_data_sorted.json", "r") as file:
                    all_historical_data = json.load(file)
            except FileNotFoundError:
                print("Error: Historical data file not found.")
                return None, None
            except json.JSONDecodeError:
                print("Error: Failed to decode JSON data.")
                return None, None

            # Фільтр даних із JSON-файлу
            historical_price_data = [
                p for p in all_historical_data
                if from_timestamp - (self.settings.grid_historical_days * 24 * 60 * 60 * 1000) <= p["timestamp"] < from_timestamp
            ]

            backtest_price_data = [
                p for p in all_historical_data
                if from_timestamp <= p["timestamp"] <= to_timestamp
            ]

        # Перевіряємо наявність даних
        if not historical_price_data:
            print("No historical data found for the grid calculation.")
            return None, None
        if not backtest_price_data:
            print("No data found for the backtest period.")
            return None, None

        return historical_price_data, backtest_price_data