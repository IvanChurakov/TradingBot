import numpy as np


class GridStrategy:
    def __init__(self, settings):
        self.settings = settings

    def calculate_grid_levels_with_percentile(self, historical_prices, grid_levels_count):
        if not historical_prices or len(historical_prices) < 2:
            raise ValueError("Insufficient historical data to calculate grid levels")

        min_price = np.percentile(historical_prices, 5)
        max_price = np.percentile(historical_prices, 95)

        step = (max_price - min_price) / (grid_levels_count - 1)

        levels = []
        price = min_price
        while price <= max_price:
            levels.append(price)
            price += step

        return {
            "levels": levels,
            "min": min_price,
            "max": max_price
        }

    def calculate_grid_levels_with_standard_deviation(self, historical_prices, grid_levels_count, k=2):
        if not historical_prices or len(historical_prices) < 2:
            raise ValueError("Insufficient historical data to calculate grid levels")

        mean_price = np.mean(historical_prices)
        std_dev_price = np.std(historical_prices)

        min_price = mean_price - k * std_dev_price
        max_price = mean_price + k * std_dev_price

        step = (max_price - min_price) / (grid_levels_count - 1)

        levels = []
        price = min_price
        while price <= max_price:
            levels.append(price)
            price += step

        return {
            "levels": levels,
            "min": min_price,
            "max": max_price
        }

    def calculate_grid_levels_bollinger(self, historical_prices, grid_levels_count, n_points=20, k=2):
        if len(historical_prices) < n_points:
            raise ValueError("Insufficient data points for Bollinger Bands calculation.")

        recent_prices = historical_prices[-n_points:]

        moving_average = np.mean(recent_prices)
        std_dev = np.std(recent_prices)

        lower_band = moving_average - k * std_dev
        upper_band = moving_average + k * std_dev

        step = (upper_band - lower_band) / (grid_levels_count - 1)

        levels = []
        price = lower_band
        while price <= upper_band:
            levels.append(price)
            price += step

        return {
            "levels": levels,
            "min": lower_band,
            "max": upper_band
        }