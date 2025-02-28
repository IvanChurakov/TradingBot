import datetime


class MarketData:
    def __init__(self, http_session):
        self.http_session = http_session

    def get_current_price(self, symbol):
        response = self.http_session.get_ticker(category="spot", symbol=symbol)

        if response.get("retCode") == 0:
            return float(response["result"]["lastPrice"])
        else:
            print(f"Error fetching market price: {response['retMsg']}")
            return None

    def fetch_data_for_period(self, symbol, start_datetime, end_datetime, interval="15"):
        try:
            historical_prices = []
            interval_milliseconds = self._to_milliseconds_from_minutes(interval)
            max_duration = 200 * interval_milliseconds

            print(f"start datetime: {self._format_timestamp(start_datetime)}")
            print(f"start datetime: {self._format_timestamp(end_datetime)}")

            while start_datetime < end_datetime:
                current_end_time = min(start_datetime + max_duration, end_datetime)

                print(f"Fetching historical data from {self._format_timestamp(start_datetime)} to {self._format_timestamp(current_end_time)}")

                response = self.http_session.get_kline(
                    category="spot",
                    symbol=symbol,
                    interval=interval,
                    start=start_datetime,
                    end=current_end_time
                )

                if response.get("retCode") == 0:
                    kline_data = response.get("result", {}).get("list", [])
                    if not kline_data:
                        start_datetime = current_end_time + 1
                        continue

                    for entry in kline_data:
                        timestamp = int(entry[0])
                        close_price = float(entry[4])

                        if not historical_prices or historical_prices[-1]["timestamp"] != timestamp:
                            historical_prices.append({"timestamp": timestamp, "close_price": close_price})

                    start_datetime = current_end_time + 1
                else:
                    print(f"Error fetching historical data: {response.get('retMsg')}")
                    break

            historical_prices = sorted(historical_prices, key=lambda x: x["timestamp"])

            return historical_prices

        except Exception as e:
            print(f"An error occurred while fetching historical data: {e}")
            return []

    @staticmethod
    def _to_milliseconds_from_minutes(minutes):
        return int(minutes) * 60 * 1000

    @staticmethod
    def _format_timestamp(timestamp):
        return datetime.datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')