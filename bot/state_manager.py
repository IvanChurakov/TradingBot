import boto3
from botocore.exceptions import ClientError
from configs.settings import Settings
from utils.logging_utils import setup_logger


logger = setup_logger(log_dir="logs", days_to_keep=30)


class StateManager:
    def __init__(self, table_name="Orders"):
        self.table_name = table_name
        self.config = Settings()

        try:
            self.dynamodb = boto3.resource(
                "dynamodb",
                region_name=self.config.aws_region,
                aws_access_key_id=self.config.aws_access_key,
                aws_secret_access_key=self.config.aws_secret_key,
            )
            self.table = self.dynamodb.Table(self.table_name)
            logger.info(f"Connected to DynamoDB table: {self.table_name}")
        except ClientError as e:
            logger.error(f"Error connecting to DynamoDB: {e}", exc_info=True)
            raise

    def add_order(self, order_link_id, amount, price):
        try:
            item = {
                "orderLinkId": order_link_id,
                "amount": amount,
                "price": price,
                "allowToSell": False
            }
            self.table.put_item(Item=item)
            logger.info(f"Order {order_link_id} added to DynamoDB.")
        except ClientError as e:
            logger.error(f"Failed to add order {order_link_id} to DynamoDB: {e}", exc_info=True)

    def remove_order(self, order_link_id):
        try:
            self.table.delete_item(Key={"orderLinkId": order_link_id})
            logger.info(f"Order {order_link_id} removed from DynamoDB.")
        except ClientError as e:
            logger.error(f"Failed to remove order {order_link_id} from DynamoDB: {e}", exc_info=True)

    def update_order(self, order_link_id, **fields):
        try:
            update_expression = "SET " + ", ".join(f"{key} = :{key}" for key in fields.keys())
            expression_values = {f":{key}": value for key, value in fields.items()}

            self.table.update_item(
                Key={"orderLinkId": order_link_id},  # Ідентифікатор
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            logger.info(f"Order {order_link_id} updated in DynamoDB with fields: {fields}.")
        except ClientError as e:
            logger.error(f"Failed to update order {order_link_id} in DynamoDB: {e}", exc_info=True)

    def get_orders(self):
        try:
            response = self.table.scan()
            orders = response.get("Items", [])
            logger.info(f"Fetched {len(orders)} orders from DynamoDB.")
            return orders
        except ClientError as e:
            logger.error(f"Failed to fetch orders from DynamoDB: {e}", exc_info=True)
            return []

    def get_order(self, order_link_id):
        try:
            response = self.table.get_item(Key={"orderLinkId": order_link_id})
            order = response.get("Item")
            if order:
                logger.info(f"Order {order_link_id} fetched successfully from DynamoDB.")
                return order
            else:
                logger.warning(f"Order {order_link_id} not found in DynamoDB.")
                return None
        except ClientError as e:
            logger.error(f"Failed to fetch order {order_link_id} from DynamoDB: {e}", exc_info=True)
            return None