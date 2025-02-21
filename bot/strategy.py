def _calculate_grid_levels():
    min_price = 20000
    max_price = 26000
    step = 1000

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


class GridStrategy:
    def __init__(self, settings):
        self.settings = settings
        self.grid_levels = _calculate_grid_levels()

    def update(self, prices, active_orders):
        decisions = []
        for price in prices:
            if price < self.grid_levels["lower"]:
                decisions.append({"action": "BUY", "price": price})
            elif price > self.grid_levels["upper"]:
                decisions.append({"action": "SELL", "price": price})
        return decisions

    def get_grid_levels(self):
        return self.grid_levels