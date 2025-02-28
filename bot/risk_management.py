class RiskManager:
    def __init__(self, settings):
        self.settings = settings

    def can_execute_trade(self, historical_prices):
        if not historical_prices or len(historical_prices) < 2:
            print("Not enough data to make decision.")
            return False

        # Calculate the average price over the historical price range
        average_price = sum(historical_prices) / len(historical_prices)

        # Calculate the standard deviation to determine price volatility
        standard_deviation = (sum((price - average_price) ** 2 for price in historical_prices) / len(
            historical_prices)) ** 0.5
        print(f"Calculated Standard Deviation: {standard_deviation}")

        if standard_deviation < self.settings.volatility_threshold:
            print("Market is in a low volatility state, considered consolidated/sideways.")
            # Low volatility, so it might be consolidating (in a range / sideways)
            return True

        # Calculate the slope of the trendline (using linear regression)
        n = len(historical_prices)
        sum_x = sum(range(n))
        sum_y = sum(historical_prices)
        sum_xy = sum(x * y for x, y in enumerate(historical_prices))
        sum_x_squared = sum(x ** 2 for x in range(n))

        # To avoid division by zero
        if (n * sum_x_squared - sum_x ** 2) == 0:
            print("Division by zero in slope calculation. Cannot determine trend.")
            return False

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x ** 2)
        print(f"Calculated Slope of Trendline: {slope}")

        # If slope is negative, the price is falling
        if slope < 0:
            print("Negative trend detected, price is falling.")
            return False

        print("Positive trend detected, conditions are favorable for trading.")
        return True