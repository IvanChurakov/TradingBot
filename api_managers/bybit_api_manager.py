from pybit.unified_trading import HTTP
import time

from api_managers.base_api_manager import BaseAPIManager
from utils.logging_utils import setup_logger
from utils.telegram_utils import send_telegram_notification


logger = setup_logger(log_dir="logs", days_to_keep=30)


class BybitAPIManager(BaseAPIManager):
    def __init__(self, api_key, api_secret, testnet=False, timeout=30):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.timeout = timeout

        self.http_session = self.__create_http_session()

    def get_http_session(self) -> HTTP:
        return self.http_session

    def safe_api_call(self, api_func, *args, **kwargs):
        max_retries = 3
        retry_interval = 30

        for attempt in range(max_retries):
            try:
                return api_func(*args, **kwargs)

            except Exception as e:
                logger.error(f"Unexpected error occurred: {e}. Attempt {attempt + 1}/{max_retries}", exc_info=True)

                if attempt < max_retries - 1:
                    send_telegram_notification(f"⚠ Unexpected API call error: {e}. Attempt {attempt + 1}/{max_retries}")
                    self.http_session = self.__create_http_session()
                    time.sleep(retry_interval)
                else:
                    logger.error(f"Unexpected error after {max_retries} retries. Giving up...")
                    send_telegram_notification(f"⚠ Unexpected API call error: {e}. Final")

    def __create_http_session(self):
        return HTTP(
            testnet=self.testnet,
            api_key=self.api_key,
            api_secret=self.api_secret,
            timeout=self.timeout
        )