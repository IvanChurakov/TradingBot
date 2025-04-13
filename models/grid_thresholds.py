from dataclasses import dataclass

#TODO: remove dataclass
@dataclass
class GridThresholds:
    lower_grid: float
    upper_grid: float
    lower_buy_threshold: float
    upper_sell_threshold: float
    amount_to_spend: float