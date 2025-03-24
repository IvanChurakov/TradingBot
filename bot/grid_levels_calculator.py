import numpy as np

from models.grid_levels import GridLevels
from utils.logging_utils import setup_logger


logger = setup_logger(log_dir="logs", days_to_keep=30)


class GridLevelsCalculator:
    @staticmethod
    def calculate_grid_levels_with_percentile(historical_prices, grid_levels_count):
        logger.info("Calculating grid levels using percentiles...")
        if not historical_prices or len(historical_prices) < 2:
            logger.error("Insufficient historical data to calculate grid levels.")
            raise ValueError("Insufficient historical data to calculate grid levels")

        min_price = np.percentile(historical_prices, 5)
        max_price = np.percentile(historical_prices, 95)

        levels = np.linspace(min_price, max_price, grid_levels_count).tolist()

        logger.info(
            f"Percentile grid calculated: min={min_price:.2f}, max={max_price:.2f}, levels={len(levels)}"
        )

        return GridLevels(levels=levels, min=float(min_price), max=float(max_price))

    @staticmethod
    def calculate_grid_levels_with_standard_deviation(historical_prices, grid_levels_count, k=2):
        logger.info("Calculating grid levels using standard deviation...")
        if not historical_prices or len(historical_prices) < 2:
            logger.error("Insufficient historical data to calculate grid levels.")
            raise ValueError("Insufficient historical data to calculate grid levels")

        mean_price = np.mean(historical_prices)
        std_dev_price = np.std(historical_prices)

        min_price = mean_price - k * std_dev_price
        max_price = mean_price + k * std_dev_price

        levels = np.linspace(min_price, max_price, grid_levels_count).tolist()

        logger.info(
            f"Standard deviation grid calculated: mean={mean_price:.2f}, std_dev={std_dev_price:.2f}, "
            f"min={min_price:.2f}, max={max_price:.2f}, levels={len(levels)}"
        )

        return GridLevels(levels=levels, min=min_price, max=max_price)

    @staticmethod
    def calculate_grid_levels_bollinger(historical_prices, grid_levels_count, n_points=20, k=2):
        logger.info("Calculating grid levels using Bollinger Bands...")
        if len(historical_prices) < n_points:
            logger.error("Insufficient data points for Bollinger Bands calculation.")
            raise ValueError("Insufficient data points for Bollinger Bands calculation.")

        recent_prices = historical_prices[-n_points:]

        moving_average = np.mean(recent_prices)
        std_dev = np.std(recent_prices)

        lower_band = moving_average - k * std_dev
        upper_band = moving_average + k * std_dev

        levels = np.linspace(lower_band, upper_band, grid_levels_count).tolist()

        logger.info(
            f"Bollinger Bands grid calculated: moving_average={moving_average:.2f}, std_dev={std_dev:.2f}, "
            f"lower_band={lower_band:.2f}, upper_band={upper_band:.2f}, levels={len(levels)}"
        )

        return GridLevels(levels=levels, min=float(lower_band), max=float(upper_band))