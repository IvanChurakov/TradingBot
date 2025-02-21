from bot.strategy import GridStrategy
from bot.trader import Trader
from bot.risk_management import RiskManager
from data.market_data import MarketData
from data.historical_data import HistoricalData
from configs.settings import Settings
from pybit.unified_trading import HTTP
import time
from queue import Queue

class GridBot:
    def __init__(self, test_mode=False, data_queue=None):
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
        self.trade_results = []
        self.data_queue = data_queue
        self.price_data = []

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
            days=30
        )

        self.price_data = prices
        #for price_data in prices:
        #    price = price_data["close_price"]
        #    timestamp = price_data["timestamp"]

            #decisions = self.strategy.update([price], self.active_orders)

            #for decision in decisions:
            #    self.process_decision(decision, timestamp=timestamp)

        self.send_updates_to_ui()

        #total_profit = sum([trade["profit"] for trade in self.trade_results])
        #print(f"Backtest complete! Total profit: {total_profit:.2f}")

    def run_real_time_bot(self):
        print("Starting Grid Bot...")

        while True:
            prices = self.market_data.get_current_price(self.settings.symbol)
            decisions = self.strategy.update(prices, self.active_orders)

            for decision in decisions:
                self.process_decision(decision)

            self.send_updates_to_ui()

            time.sleep(self.settings.trade_interval)

    def process_decision(self, decision, timestamp=None):
        if decision["action"] == "BUY":
            if self.test_mode:
                self.trade_results.append({
                    "action": "BUY",
                    "price": decision["price"],
                    "timestamp": timestamp,
                    "profit": 0
                })
            else:
                if self.risk_manager.can_execute_trade(decision):
                    order = self.trader.place_order("BUY", decision)
                    self.active_orders.append(order)

        elif decision["action"] == "SELL":
            if self.test_mode:
                last_buy = next((trade for trade in self.trade_results if trade["action"] == "BUY" and trade["profit"] == 0), None)
                if last_buy:
                    profit = decision["price"] - last_buy["price"]
                    last_buy["profit"] = profit
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

    def send_updates_to_ui(self):
        if self.data_queue:
            max_price_data = 500
            price_data_limited = self.price_data[-max_price_data:]

            self.data_queue.put({
                "price_data": price_data_limited,
                "grid_levels": self.strategy.get_grid_levels(),
                "active_orders": self.active_orders,
                "trade_results": self.trade_results,
            })