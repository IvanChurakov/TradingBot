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
        self.grid_levels = int(os.getenv("GRID_LEVELS", 5))
        self.grid_spacing = float(os.getenv("GRID_SPACING", 1.0))
        self.trade_interval = int(os.getenv("TRADE_INTERVAL", 60))  # in seconds

        # Risk Management
        self.max_balance_use = float(os.getenv("MAX_BALANCE_USE", 0.8))  # 80%
        self.min_order_size = float(os.getenv("MIN_ORDER_SIZE", 0.001))  # minimal size