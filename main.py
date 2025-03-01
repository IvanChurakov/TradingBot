from datetime import datetime
from bot.grid_bot import GridBot


if __name__ == "__main__":
    grid_bot = GridBot()

    from_date = datetime(2023, 1, 1, 0, 0, 0)
    to_date = datetime(2024, 12, 31, 23, 59, 59)

    grid_bot.run_backtest(from_date, to_date, use_real_data=True)