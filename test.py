from pybit.unified_trading import HTTP
from unicodedata import category

from configs.settings import Settings

settings = Settings()

http_session = HTTP(
    testnet=False,
    api_key=settings.api_key,
    api_secret=settings.api_secret,
)

print(http_session.get_account_info())