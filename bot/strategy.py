class GridStrategy:
    def __init__(self, settings):
        self.settings = settings
        self.grid_levels = self._calculate_grid_levels()

    def update(self, prices, active_orders):
        decisions = []
        for price in prices:
            if price < self.grid_levels["lower"]:
                decisions.append({"action": "BUY", "price": price})
            elif price > self.grid_levels["upper"]:
                decisions.append({"action": "SELL", "price": price})
        return decisions

    def _calculate_grid_levels(self):
        # Calculate grid levels
        lower_level = 100  # Add logic based on settings
        upper_level = 110
        return {"lower": lower_level, "upper": upper_level}