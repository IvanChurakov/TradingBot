import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        # Bybit API Keys
        self.api_key = os.getenv("API_KEY")
        self.api_secret = os.getenv("API_SECRET")

        # AWS Credentials
        self.aws_region = os.getenv("AWS_REGION")
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY")
        self.aws_secret_key = os.getenv("AWS_SECRET_KEY")

        # Telegram Credentials
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        # General Bot Settings
        self.symbol = os.getenv("SYMBOL", "BTCUSDT")
        self.grid_levels_count = int(os.getenv("GRID_LEVELS_COUNT", 20))
        self.volatility_threshold = float(os.getenv("VOLATILITY_THRESHOLD", 0.05))
        self.profit_target = float(os.getenv("PROFIT_TARGET", 0.02))
        self.btc_per_trade = float(os.getenv("BTC_PER_TRADE", 0.0000314))
        self.buy_percentage = float(os.getenv("BUY_PERCENTAGE", 0.005))
        self.min_transaction_amount = float(os.getenv("MIN_TRANSACTION_AMOUNT", 6))
        self.grid_historical_days = float(os.getenv("GRID_HISTORICAL_DAYS", 61))
        self.trading_interval = int(os.getenv("TRADING_INTERVAL", 60))
        self.qty_precision = int(os.getenv("QTY_PRECISION", 6))