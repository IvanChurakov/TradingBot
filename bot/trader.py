class Trader:
    def __init__(self, http_session):
        self.http_session = http_session

    def get_balance(self):
        print("Fetching balance information...")

        response = self.http_session.get_wallet_balance(category="spot")

        if response.get("retCode") == 0:
            balances = response["result"]["balances"]

            # Форматуємо вивід балансу (якщо потрібно)
            for balance in balances:
                asset = balance["coin"]
                total = float(balance["total"])
                free = float(balance["free"])
                locked = float(balance["locked"])
                print(f"Asset: {asset}, Total: {total}, Free: {free}, Locked: {locked}")

            return balances  # Повертаємо отримані баланси як список словників
        else:
            print(f"Error fetching balance: {response['retMsg']}")
            return None

    def place_order(self, symbol, side, quantity, price):
        print(f"Placing {'BUY' if side == 'BUY' else 'SELL'} order for {symbol}...")

        order_data = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",  # Використовуємо лімітний ордер
            "qty": quantity,
            "price": price,
            "timeInForce": "GTC",  # Good till Cancelled
        }

        response = self.http_session.place_order(order_data)

        if response.get("retCode") == 0:
            print(f"Order placed successfully: {response['result']}")
            return response["result"]
        else:
            print(f"Error placing order: {response['retMsg']}")
            return None