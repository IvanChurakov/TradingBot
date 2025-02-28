from datetime import datetime
from bot.grid_bot import GridBot


if __name__ == "__main__":
    grid_bot = GridBot()

    from_date = datetime(2025, 1, 1, 0, 0, 0)
    to_date = datetime(2025, 2, 20, 17, 49, 0)

    grid_bot.run_backtest(from_date, to_date, use_real_data=False)