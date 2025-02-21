import datetime

def _format_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')

def _to_milliseconds_from_minutes(minutes):
    return int(minutes) * 60 * 1000

def _to_milliseconds_from_days(days):
    return int(days) * 24 * 60 * 60 * 1000

class HistoricalData:
    def __init__(self, http_session):
        self.http_session = http_session

    def fetch_historical_data(self, symbol, interval="15", days=30):
        try:
            end_time = int(datetime.datetime.now().timestamp() * 1000)
            start_time = end_time - _to_milliseconds_from_days(days)

            historical_prices = []
            interval_milliseconds = _to_milliseconds_from_minutes(interval)
            max_duration = 200 * interval_milliseconds

            while start_time < end_time:
                current_end_time = min(start_time + max_duration, end_time)

                print(
                    f"Fetching historical data from {_format_timestamp(start_time)} to {_format_timestamp(current_end_time)}")

                response = self.http_session.get_kline(
                    category="spot",
                    symbol=symbol,
                    interval=str(interval),
                    start=int(start_time),
                    end=int(current_end_time)
                )

                if response.get("retCode") == 0:
                    kline_data = response.get("result", {}).get("list", [])
                    if not kline_data:
                        break

                    for entry in kline_data:
                        timestamp = int(entry[0])
                        close_price = float(entry[4])

                        if not historical_prices or historical_prices[-1]["timestamp"] != timestamp:
                            historical_prices.append({"timestamp": timestamp, "close_price": close_price})

                    start_time = current_end_time + 1
                else:
                    print(f"Error fetching historical data: {response.get('retMsg')}")
                    break

            historical_prices = sorted(historical_prices, key=lambda x: x["timestamp"])

            return historical_prices

        except Exception as e:
            print(f"An error occurred while fetching historical data: {e}")
            return []