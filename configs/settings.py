import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        # API Keys
        self.api_key = os.getenv("API_KEY")
        self.api_secret = os.getenv("API_SECRET")

        # General Bot Settings
        self.symbol = os.getenv("SYMBOL", "BTCUSDT")
        self.grid_levels_count = int(os.getenv("GRID_LEVELS_COUNT", 30))
        self.volatility_threshold = float(os.getenv("VOLATILITY_THRESHOLD", 0.05))
        self.profit_target = float(os.getenv("PROFIT_TARGET", 0.02))
        self.btc_per_trade = float(os.getenv("BTC_PER_TRADE", 0.0000314))
        self.buy_percentage = float(os.getenv("BUY_PERCENTAGE", 0.005))
        self.min_transaction_amount = float(os.getenv("MIN_TRANSACTION_AMOUNT", 5))
        self.grid_spacing = float(os.getenv("GRID_SPACING", 1.0))
        self.trade_interval = int(os.getenv("TRADE_INTERVAL", 60))  # in seconds

        # Risk Management
        self.max_balance_use = float(os.getenv("MAX_BALANCE_USE", 0.8))  # 80%
        self.min_order_size = float(os.getenv("MIN_ORDER_SIZE", 0.001))  # minimal size