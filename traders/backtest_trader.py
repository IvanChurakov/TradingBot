from models.order import Order
from models.order_placement_result import OrderActionResult
from models.portfolio_balance import PortfolioBalance
from traders.base_trader import BaseTrader

class BacktestTrader(BaseTrader):
    def __init__(self, initial_balance=1000.0):
        self.balance = {"USDT": initial_balance}
        self.orders = []
        self.closed_orders = []

    def get_available_coin_balance(self, coin: str, account_type: str = "UNIFIED") -> float:
        return float(self.balance.get(coin, 0.0))

    def is_order_closed(self, order_link_id: str) -> bool:
        pass

    def place_order(self, symbol: str, decision: Order) -> OrderActionResult:
        if decision.action == "Buy":
            self.balance["USDT"] -= decision.amount * decision.price

            return OrderActionResult(success=True, result=f"Buy Order for {symbol} placed successfully.")

        elif decision.action == "Sell":
            self.balance["USDT"] += decision.amount * decision.price

            return OrderActionResult(success=True, result=f"Sell Order for {symbol} placed successfully.")

        return OrderActionResult(success=False, error_message="Invalid order action.")

    def get_portfolio_balance(self, account_type: str = "UNIFIED") -> PortfolioBalance:
        pass

    def cancel_order(self, order_link_id: str) -> OrderActionResult:
        pass