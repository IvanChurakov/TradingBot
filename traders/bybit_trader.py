from models.coin_balance import CoinBalance
from models.order import Order
from models.order_placement_result import OrderActionResult
from models.portfolio_balance import PortfolioBalance
from traders.base_trader import BaseTrader
from utils.logging_utils import setup_logger


logger = setup_logger(log_dir="logs", days_to_keep=30)


class BybitTrader(BaseTrader):
    def __init__(self, api_manager):
        self.api_manager = api_manager

    def get_available_coin_balance(self, coin: str, account_type: str = "UNIFIED") -> float:
        logger.info(f"Fetching balance information for accountType={account_type}, coin={coin}.")
        try:
            response = self.api_manager.safe_api_call(
                self.api_manager.http_session.get_wallet_balance,
                accountType=account_type,
                coin=coin
            )
        except Exception as e:
            logger.error(f"Error during balance fetching: {e}", exc_info=True)
            return 0.0

        if response.get("retCode") != 0:
            logger.error(f"Error fetching balance: {response.get('retMsg')}")
            return 0.0

        balance_data = response["result"].get("list", [])
        if not balance_data:
            logger.warning("No balance data available from API response.")
            return 0.0

        for account in balance_data:
            if account.get("accountType") == account_type:
                coins = account.get("coin", [])
                for item in coins:
                    if item["coin"] == coin:
                        wallet_balance = float(item.get("walletBalance", 0))
                        locked_balance = float(item.get("locked", 0))
                        available_balance = wallet_balance - locked_balance

                        logger.info(
                            f"Coin: {coin}, Wallet Balance: {wallet_balance:.6f}, "
                            f"Locked Balance: {locked_balance:.6f}, Available Balance: {available_balance:.6f}"
                        )
                        return available_balance

                logger.info(f"Coin {coin} not found in accountType={account_type}. Returning 0.0 balance.")
                return 0.0

        logger.warning(f"No account found with type {account_type} in API response.")
        return 0.0

    def is_order_closed(self, order_link_id: str) -> bool:
        logger.info(f"Checking if order with orderLinkId: {order_link_id} is closed...")

        try:
            response = self.api_manager.safe_api_call(
                self.api_manager.http_session.get_open_orders,
                category="spot",
                orderLinkId=order_link_id
            )
        except Exception as e:
            logger.error(f"Error during order status check: {e}", exc_info=True)
            return False

        if response.get("retCode") == 0:
            orders = response.get("result", {}).get("list", [])

            for order in orders:
                if order.get("orderLinkId") == order_link_id:
                    order_status = order.get("orderStatus")
                    if order_status == "Filled":
                        logger.info(f"Order {order_link_id} is closed (status: Filled).")
                        return True
                    else:
                        logger.info(f"Order {order_link_id} is still open (status: {order_status}).")
                        return False

            logger.info(f"Order {order_link_id} not found in the response. Assuming it is not closed.")
            return False
        else:
            logger.error(f"Error fetching open orders: {response.get('retMsg')}")
            return False

    def place_order(self, symbol: str, decision: Order) -> OrderActionResult:
        logger.info(f"Placing {decision.action} order for {symbol} with orderLinkId {decision.order_link_id}...")

        response = self.api_manager.safe_api_call(
            self.api_manager.http_session.place_order,
            category="spot",
            symbol=symbol,
            side=decision.action,
            orderType="Limit",
            qty=decision.amount,
            price=decision.price,
            timeInForce="GTC",
            orderLinkId=decision.order_link_id
        )

        if response is None:
            logger.error(f"Failed to place order {decision.order_link_id}. No response from API.")
            return OrderActionResult(success=False, error_message="No response from API")

        if response.get("retCode") == 0:
            logger.info(f"Order placed successfully: {response['result']}")
            return OrderActionResult(success=True, result=response["result"])
        else:
            error_message = response.get("retMsg", "Unknown error")
            logger.error(f"Error placing order: {error_message}")
            return OrderActionResult(success=False, error_message=error_message)

    def get_portfolio_balance(self, account_type="UNIFIED") -> PortfolioBalance:
        logger.info(f"Fetching portfolio balance for accountType={account_type}...")
        try:
            response = self.api_manager.safe_api_call(
                self.api_manager.http_session.get_wallet_balance,
                accountType=account_type
            )
        except Exception as e:
            logger.error(f"Error fetching portfolio balance: {e}", exc_info=True)
            return PortfolioBalance(
                total_equity=0.0,
                total_available_balance=0.0,
                details=[]
            )

        if response.get("retCode") == 0:
            balance_data = response["result"].get("list", [])
            if not balance_data:
                logger.warning("No balance data available from API response.")
                return PortfolioBalance(
                    total_equity=0.0,
                    total_available_balance=0.0,
                    details=[]
                )

            total_equity = 0.0
            total_available_balance = 0.0
            coin_balances = []

            #TODO: Maybe 1 iteration everytime
            for account in balance_data:
                if account.get("accountType") == account_type:
                    total_equity += float(account.get("totalEquity", 0))
                    total_available_balance += float(account.get("totalAvailableBalance", 0))

                    for coin in account.get("coin", []):
                        coin_balances.append(
                            CoinBalance(
                                coin=coin["coin"],
                                equity=float(coin.get("equity", 0)),
                                wallet_balance=float(coin.get("walletBalance", 0)),
                                locked_balance=float(coin.get("locked", 0)),
                                available_balance=float(coin.get("walletBalance", 0)) - float(coin.get("locked", 0)),
                                usd_value=float(coin.get("usdValue", 0)),
                            )
                        )

            logger.info(
                f"Portfolio balance fetched successfully: Total Equity = {total_equity:.6f}, "
                f"Total Available Balance = {total_available_balance:.6f}, Details: {len(coin_balances)} coins."
            )
            return PortfolioBalance(
                total_equity=total_equity,
                total_available_balance=total_available_balance,
                details=coin_balances
            )
        else:
            logger.error(f"Error fetching portfolio balance: {response.get('retMsg')}")
            return PortfolioBalance(
                total_equity=0.0,
                total_available_balance=0.0,
                details=[]
            )

    def cancel_order(self, order_link_id: str) -> OrderActionResult:
        logger.info(f"Attempting to cancel order with orderLinkId: {order_link_id}...")

        try:
            response = self.api_manager.safe_api_call(
                self.api_manager.http_session.cancel_order,
                category="spot",
                orderLinkId=order_link_id
            )
        except Exception as e:
            logger.error(f"Error during order cancellation: {e}", exc_info=True)
            return OrderActionResult(success=False, error_message=str(e))

        if response is None:
            logger.error("Failed to cancel order. No response from API.")
            return OrderActionResult(success=False, error_message="No response from API")

        if response.get("retCode") == 0:
            logger.info(f"Order {order_link_id} successfully canceled: {response.get('result', {})}")
            return OrderActionResult(
                success=True,
                result=response.get("result", {})
            )
        else:
            error_message = response.get("retMsg", "Unknown error")
            logger.error(f"Error canceling order {order_link_id}: {error_message}")
            return OrderActionResult(success=False, error_message=error_message)