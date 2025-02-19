class HistoricalData:
    def __init__(self, http_session):
        self.http_session = http_session

    def fetch_historical_data(self, symbol, interval="15", days=30):
        end_time = int(datetime.datetime.now().timestamp() * 1000)
        start_time = end_time - (days * 24 * 60 * 60 * 1000)

        historical_prices = []
        while start_time < end_time:
            response = self.http_session.get_kline(
                category="spot",
                symbol=symbol,
                interval=interval,
                start=start_time,
                end=min(start_time + 1000 * 15 * 60 * 1000, end_time),  # 1000 записів максимум
                limit=1000
            )

            if response.get("retCode") == 0:
                kline_data = response.get("result", {}).get("list", [])
                for entry in kline_data:
                    timestamp = int(entry[0])
                    close_price = float(entry[4])
                    historical_prices.append({"timestamp": timestamp, "close_price": close_price})

                # Оновимо початок для наступного запиту
                start_time = kline_data[-1][0] + (15 * 60 * 1000)  # Починає з наступного запису
            else:
                print(f"Error fetching historical data: {response.get('retMsg')}")
                break

        return historical_prices