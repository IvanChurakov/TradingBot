from bot.strategy import GridStrategy
from bot.trader import Trader
from bot.risk_management import RiskManager
from data.market_data import MarketData
from data.historical_data import HistoricalData
from configs.settings import Settings
from pybit.unified_trading import HTTP
import time

class GridBot:
    def __init__(self, test_mode=False):
        self.settings = Settings()

        self.http_session = HTTP(
            testnet=False,
            api_key=self.settings.api_key,
            api_secret=self.settings.api_secret,
        )

        self.market_data = MarketData(self.http_session)
        self.historical_data = HistoricalData(self.http_session)
        self.strategy = GridStrategy(self.settings)
        self.trader = Trader(self.http_session)
        self.risk_manager = RiskManager(self.settings)

        self.test_mode = test_mode
        self.active_orders = []
        self.trade_results = []  # Для зберігання результатів backtesting

    def run(self):
        if self.test_mode:
            self.run_backtest()
        else:
            self.run_real_time_bot()

    def run_backtest(self):
        print("Starting Backtest...")
        prices = self.historical_data.fetch_historical_data(
            symbol=self.settings.symbol,
            interval="15",
            days=30  # Місяць
        )

        for price_data in prices:
            price = price_data["close_price"]
            timestamp = price_data["timestamp"]

            # Емуляція стратегії
            decisions = self.strategy.update([price], self.active_orders)

            # Імітація виконання угоди
            for decision in decisions:
                self.process_decision(decision, timestamp=timestamp)

        # Виведемо результати
        total_profit = sum([trade["profit"] for trade in self.trade_results])
        print(f"Backtest complete! Total profit: {total_profit:.2f}")

    def run_real_time_bot(self):
        print("Starting Grid Bot...")

        while True:
            prices = self.market_data.get_current_price(self.settings.symbol)
            decisions = self.strategy.update(prices, self.active_orders)

            for decision in decisions:
                self.process_decision(decision)

            time.sleep(self.settings.trade_interval)

    def process_decision(self, decision, timestamp=None):
        if decision["action"] == "BUY":
            if self.test_mode:
                # Емітувати виконання ордеру в backtest
                self.trade_results.append({
                    "action": "BUY",
                    "price": decision["price"],
                    "timestamp": timestamp,
                    "profit": 0  # Обчислюється під час продажу
                })
            else:
                # Реальний режим
                if self.risk_manager.can_execute_trade(decision):
                    order = self.trader.place_order("BUY", decision)
                    self.active_orders.append(order)

        elif decision["action"] == "SELL":
            if self.test_mode:
                # Обчислити прибуток у режимі backtesting
                last_buy = next((trade for trade in self.trade_results if trade["action"] == "BUY" and trade["profit"] == 0), None)
                if last_buy:
                    profit = decision["price"] - last_buy["price"]
                    last_buy["profit"] = profit  # Фіксуємо прибуток для відповідного BUY
                    self.trade_results.append({
                        "action": "SELL",
                        "price": decision["price"],
                        "timestamp": timestamp,
                        "profit": profit
                    })
            else:
                if self.risk_manager.can_execute_trade(decision):
                    order = self.trader.place_order("SELL", decision)
                    self.active_orders.append(order)