from configs.settings import Settings
from utils.datetime_utils import to_milliseconds_from_minutes, format_timestamp
from utils.logging_utils import setup_logger


logger = setup_logger(log_dir="logs", days_to_keep=30)


class MarketData:
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.settings = Settings()
        logger.info("MarketData initialized successfully.")

    def get_min_order_amt(self, symbol):
        logger.info(f"Fetching min order amount for symbol: {symbol}...")
        try:
            response = self.api_manager.safe_api_call(
                self.api_manager.http_session.get_instruments_info, category="spot", symbol=symbol)

            if response.get("retCode") == 0:
                instruments = response.get("result", {}).get("list", [])
                if instruments:
                    min_order_amt = float(instruments[0]["lotSizeFilter"]["minOrderAmt"])
                    logger.info(f"Min order amount for {symbol}: {min_order_amt}")
                    return min_order_amt
            logger.error(f"Error fetching min order amount: {response.get('retMsg')}")
            return 5

        except Exception as e:
            logger.error(f"An error occurred while fetching min order amount for {symbol}: {e}", exc_info=True)
            return 5

    def get_current_price(self, symbol):
        logger.info(f"Fetching current price for symbol: {symbol}...")
        try:
            response = self.api_manager.safe_api_call(
                self.api_manager.http_session.get_tickers, category="spot", symbol=symbol)

            if response.get("retCode") == 0:
                current_price = float(response["result"]["list"][0]["lastPrice"])
                logger.info(f"Current price for {symbol}: {current_price}")
                return current_price
            else:
                logger.error(f"Error fetching market price for {symbol}: {response['retMsg']}")
                return 0.0
        except Exception as e:
            logger.error(f"An error occurred while fetching market price for {symbol}: {e}", exc_info=True)
            return 0.0

    def fetch_data_for_period(self, symbol, start_datetime, end_datetime, interval="1"):
        logger.info(f"Fetching historical data for symbol: {symbol} "
                    f"from {format_timestamp(start_datetime)} to {format_timestamp(end_datetime)} with interval {interval}...")
        try:
            historical_prices = []
            interval_milliseconds = to_milliseconds_from_minutes(interval)
            max_duration = 200 * interval_milliseconds

            while start_datetime < end_datetime:
                current_end_time = min(start_datetime + max_duration, end_datetime)

                logger.info(f"Fetching data from {format_timestamp(start_datetime)} to {format_timestamp(current_end_time)}...")

                response = self.api_manager.safe_api_call(
                    self.api_manager.http_session.get_kline,
                    category="spot",
                    symbol=symbol,
                    interval=interval,
                    start=start_datetime,
                    end=current_end_time
                )

                if response.get("retCode") == 0:
                    kline_data = response.get("result", {}).get("list", [])
                    if not kline_data:
                        logger.warning(f"No kline data for the time period: {format_timestamp(start_datetime)} to {format_timestamp(current_end_time)}.")
                        start_datetime = current_end_time + 1
                        continue

                    for entry in kline_data:
                        timestamp = int(entry[0])
                        close_price = float(entry[4])

                        historical_prices.append({"timestamp": timestamp, "close_price": close_price})

                    logger.info(f"Fetched {len(kline_data)} entries for {symbol} from {format_timestamp(start_datetime)} to {format_timestamp(current_end_time)}.")
                    start_datetime = current_end_time + 1
                else:
                    logger.error(f"Error fetching historical data: {response.get('retMsg')}")
                    break

            historical_prices = sorted(historical_prices, key=lambda x: x["timestamp"])
            logger.info(f"Fetched total {len(historical_prices)} historical entries for {symbol}.")
            return historical_prices

        except Exception as e:
            logger.error(f"An error occurred while fetching historical data for {symbol}: {e}", exc_info=True)
            return []