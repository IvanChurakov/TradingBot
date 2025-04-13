class CoinBalance:
    def __init__(self, coin: str, equity: float, wallet_balance: float, locked_balance: float, available_balance: float, usd_value: float):
        self.coin = coin
        self.equity = equity
        self.wallet_balance = wallet_balance
        self.locked_balance = locked_balance
        self.available_balance = available_balance
        self.usd_value = usd_value