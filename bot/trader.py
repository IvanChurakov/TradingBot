from unicodedata import category


class Trader:
    def __init__(self, http_session):
        self.http_session = http_session

    def get_balance(self, coin=None, account_type="SPOT"):
        print("Fetching balance information...")

        response = self.http_session.get_wallet_balance(category="spot")

        if response.get("retCode") == 0:
            balance_list = response["result"].get("list", [])
            if not balance_list:
                print("No balance data available.")
                return None

            account_data = next((item for item in balance_list if item.get("accountType") == account_type), None)
            if not account_data:
                print(f"No account found with type {account_type}.")
                return None

            coins = account_data.get("coin", [])

            if coin:
                for item in coins:
                    if item["coin"] == coin:
                        return float(item.get("free", 0))  # Повертаємо лише кількість доступних монет
                return 0.0  # Якщо монета не знайдена, повертаємо 0

            # Якщо параметр coin не передано, формуємо список доступних монет
            available_balances = {item["coin"]: float(item.get("free", 0)) for item in coins}
            return available_balances
        else:
            print(f"Error fetching balance: {response['retMsg']}")
            return None

    def is_order_closed(self, order_link_id):
        print(f"Checking if order with orderLinkId: {order_link_id} is closed...")

        # Викликаємо API для отримання відкритих ордерів
        response = self.http_session.get_open_orders(
            category="spot",
            orderLinkId=order_link_id
        )

        if response.get("retCode") == 0:
            open_orders = response["result"].get("list", [])
            if not open_orders:
                print("No open orders found.")
                return True
            else:
                return False
        else:
            print(f"Error fetching open orders: {response['retMsg']}")
            return None

    def place_order(self, symbol, decision):
        print(f"Placing {decision["action"]} order for {symbol} with orderLinkId {decision["orderLinkId"]}...")

        response = self.http_session.place_order(
            category="spot",
            symbol=symbol,
            side=decision["action"],
            orderType="Limit",
            qty=decision["amount"],
            price=decision["price"],
            timeInForce="GTC",
            orderLinkId=decision["orderLinkId"],
        )

        if response.get("retCode") == 0:
            print(f"Order placed successfully: {response['result']}")
            return response["result"]
        else:
            print(f"Error placing order: {response['retMsg']}")
            return None