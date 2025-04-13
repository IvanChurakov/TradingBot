from datetime import datetime
from bot.grid_bot import GridBot

from_datetime = datetime.strptime("2023-01-01", "%Y-%m-%d")
to_datetime = datetime.strptime("2025-04-12", "%Y-%m-%d")

from_timestamp = int(from_datetime.timestamp() * 1000)
to_timestamp = int(to_datetime.timestamp() * 1000)

grid_bot = GridBot()

grid_bot.run_backtest(from_timestamp, to_timestamp, use_real_data=False)