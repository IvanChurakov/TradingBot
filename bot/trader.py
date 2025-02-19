class Trader:
    def __init__(self, http_session):
        self.http_session = http_session

    def place_order(self, action, decision):
        side = "Buy" if action == "BUY" else "Sell"
        price = decision["price"]
        quantity = decision["quantity"]

        print(f"Placing {side} order for {quantity} at {price}")

        # Placeholder: Place a real order via HTTP API
        response = self.http_session.place_active_order(
            category="spot",
            symbol=decision["symbol"],
            qty=quantity,
            side=side,
            orderType="Limit",
            price=price,
            timeInForce="GoodTillCancel"
        )

        if response.get("retCode") == 0:
            print(f"Order placed successfully: {response['result']}")
            return response["result"]
        else:
            print(f"Error placing order: {response['retMsg']}")
            return None