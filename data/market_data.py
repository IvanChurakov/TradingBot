class MarketData:
    def __init__(self, http_session):
        self.http_session = http_session

    def get_current_price(self, symbol):
        # Використовуємо HTTP-сесію для отримання поточних цін
        response = self.http_session.get_ticker(category="spot", symbol=symbol)

        if response.get("retCode") == 0:
            return float(response["result"]["lastPrice"])
        else:
            print(f"Error fetching market price: {response['retMsg']}")
            return None