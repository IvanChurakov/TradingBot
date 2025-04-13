from typing import List

from models.coin_balance import CoinBalance


class PortfolioBalance:
    def __init__(self, total_equity: float, total_available_balance: float, details: List[CoinBalance]):
        self.total_equity = total_equity
        self.total_available_balance = total_available_balance
        self.details = details

    def generate_balance_string(self) -> str:
        details_string = ""

        for coin_balance in self.details:
            details_string += (
                f"🔸 {coin_balance.coin}:\n"
                f"   💰 Wallet Balance: {coin_balance.wallet_balance:.6f} {coin_balance.coin}\n"
                f"   🔒 Locked Balance: {coin_balance.locked_balance:.6f} {coin_balance.coin}\n"
                f"   🔓 Available Balance: {coin_balance.available_balance:.6f} {coin_balance.coin}\n"
                f"   📈 Equity: {coin_balance.equity:.6f} {coin_balance.coin}\n"
                f"   💵 USD Value: {coin_balance.usd_value:.2f} USD\n"
            )

        return (
            f"💹 *Portfolio Balance*:\n"
            f"💼 Total Equity: {self.total_equity:.2f} USD\n"
            f"💵 Total Available Balance: {self.total_available_balance:.2f} USD\n\n"
            f"🪙 *Detailed Coin Balances*:\n{details_string}"
        )