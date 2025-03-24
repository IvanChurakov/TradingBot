from models.order_placement_result import OrderPlacementResult
from utils.logging_utils import setup_logger


logger = setup_logger(log_dir="logs", days_to_keep=30)


class Trader:
    def __init__(self, api_manager):
        self.api_manager = api_manager

    def get_balance(self, coin=None, account_type="UNIFIED"):
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

        if response.get("retCode") == 0:
            balance_data = response["result"].get("list", [])
            if not balance_data:
                logger.warning("No balance data available from API response.")
                return 0.0

            for account in balance_data:
                if account.get("accountType") == account_type:
                    coins = account.get("coin", [])

                    if coin:
                        for item in coins:
                            if item["coin"] == coin:
                                wallet_balance = float(item.get("walletBalance", 0))
                                logger.info(f"Found wallet balance for {coin}: {wallet_balance}")
                                return wallet_balance
                        logger.info(f"Coin {coin} not found in accountType={account_type}. Returning 0.0 balance.")
                        return 0.0

                    available_balances = {
                        item["coin"]: float(item.get("walletBalance", 0))
                        for item in coins if float(item.get("walletBalance", 0)) > 0
                    }
                    logger.info(f"Available balances for accountType={account_type}: {available_balances}")
                    return available_balances

            logger.warning(f"No account found with type {account_type} in API response.")
            return 0.0
        else:
            logger.error(f"Error fetching balance: {response.get('retMsg')}")
            return 0.0

    def is_order_closed(self, order_link_id):
        logger.info(f"Checking if order with orderLinkId: {order_link_id} is closed...")

        try:
            response = self.api_manager.safe_api_call(
                self.api_manager.http_session.get_open_orders,
                category="spot",
                orderLinkId=order_link_id
            )
        except Exception as e:
            logger.error(f"Error during order status check: {e}", exc_info=True)
            return None

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

            logger.info(f"Order {order_link_id} not found in the response. Assuming it is closed.")
            return True  # Якщо немає в списку, вважаємо закритим
        else:
            logger.error(f"Error fetching open orders: {response.get('retMsg')}")
            return None

    def place_order(self, symbol, decision):
        logger.info(f"Placing {decision.action} order for {symbol} with orderLinkId {decision.orderLinkId}...")

        response = self.api_manager.safe_api_call(
            self.api_manager.http_session.place_order,
            category="spot",
            symbol=symbol,
            side=decision.action,
            orderType="Limit",
            qty=decision.amount,
            price=decision.price,
            timeInForce="GTC",
            orderLinkId=decision.orderLinkId
        )

        if response.get("retCode") == 0:
            logger.info(f"Order placed successfully: {response['result']}")
            return OrderPlacementResult(success=True, result=response["result"])
        else:
            error_message = response.get("retMsg", "Unknown error")
            logger.error(f"Error placing order: {error_message}")
            return OrderPlacementResult(success=False, error_message=error_message)