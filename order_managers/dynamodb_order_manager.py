from decimal import Decimal
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from configs.settings import Settings
from models.order import Order
from order_managers.base_order_manager import BaseOrderManager
from utils.logging_utils import setup_logger

logger = setup_logger(log_dir="logs", days_to_keep=30)

#TODO: add cashing
class DynamoDBOrderManager(BaseOrderManager):
    def __init__(self):
        self.config = Settings()

        try:
            self.dynamodb = boto3.resource(
                "dynamodb",
                region_name=self.config.aws_region,
                aws_access_key_id=self.config.aws_access_key,
                aws_secret_access_key=self.config.aws_secret_key,
            )
            self.table = self.dynamodb.Table("Orders")
            logger.info(f"Connected to DynamoDB table: 'Orders'")
        except ClientError as e:
            logger.error(f"Error connecting to DynamoDB: {e}", exc_info=True)
            raise

    def add_order(self, order: Order):
        try:
            self.table.put_item(Item=order.to_dict())
            logger.info(f"Order {order.order_link_id} added to DynamoDB.")
        except ClientError as e:
            logger.error(f"Failed to add order {order.order_link_id} to DynamoDB: {e}", exc_info=True)

    def remove_order(self, order_link_id: str):
        try:
            self.table.delete_item(Key={"orderLinkId": order_link_id})
            logger.info(f"Order {order_link_id} removed from DynamoDB.")
        except ClientError as e:
            logger.error(f"Failed to remove order {order_link_id} from DynamoDB: {e}", exc_info=True)

    def update_order(self, order_link_id: str, **fields):
        try:
            for key, value in fields.items():
                if isinstance(value, float):
                    fields[key] = Decimal(str(value))

            update_expression = "SET " + ", ".join(f"{key} = :{key}" for key in fields.keys())
            expression_values = {f":{key}": value for key, value in fields.items()}

            self.table.update_item(
                Key={"orderLinkId": order_link_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            logger.info(f"Order {order_link_id} updated in DynamoDB with fields: {fields}.")
        except ClientError as e:
            logger.error(f"Failed to update order {order_link_id} in DynamoDB: {e}", exc_info=True)

    def get_orders(self) -> list[Order]:
        try:
            response = self.table.scan()
            orders = response.get("Items", [])
            logger.info(f"Fetched {len(orders)} orders from DynamoDB.")
            return [Order.from_dict(order) for order in orders]
        except ClientError as e:
            logger.error(f"Failed to fetch orders from DynamoDB: {e}", exc_info=True)
            return []

    def get_order(self, order_link_id: str) -> Optional[Order]:
        try:
            response = self.table.get_item(Key={"orderLinkId": order_link_id})
            order = response.get("Item")
            if order:
                logger.info(f"Order {order_link_id} fetched successfully from DynamoDB.")
                return Order.from_dict(order)
            else:
                logger.warning(f"Order {order_link_id} not found in DynamoDB.")
                return None
        except ClientError as e:
            logger.error(f"Failed to fetch order {order_link_id} from DynamoDB: {e}", exc_info=True)
            return None

    def update_positions(self, trader):
        active_orders = self.get_orders()

        for order in active_orders:
            if not order.allow_to_sell:
                order_placement_result = trader.is_order_closed(order.order_link_id)
                if order_placement_result and order_placement_result is True:
                    logger.info(f"OrderLinkId {order.order_link_id} is closed. Marking as 'allowToSell'.")
                    self.update_order(order.order_link_id, allowToSell=True)