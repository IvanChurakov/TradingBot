from bot.grid_bot import GridBot
from utils.logging_utils import setup_logger
from utils.telegram_utils import send_telegram_notification

logger = setup_logger(log_dir="logs", days_to_keep=30)

if __name__ == "__main__":
    logger.info("Starting the bot...")

    try:
        grid_bot = GridBot()
        grid_bot.run_real_time_bot()
    except Exception as e:
        logger.error(f"An error occurred during bot operation: {e}", exc_info=True)

        error_message = f"🚨 Grid Bot Error: {e}"
        send_telegram_notification(error_message)
    finally:
        logger.info("Bot has stopped.")