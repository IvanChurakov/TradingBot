from bot.grid_bot import GridBot
from utils.logging_utils import setup_logger


if __name__ == "__main__":
    logger = setup_logger(log_dir="logs", days_to_keep=30)

    logger.info("Starting the bot...")

    try:
        grid_bot = GridBot()
        grid_bot.run_real_time_bot()
    except Exception as e:
        logger.error(f"An error occurred during bot operation: {e}", exc_info=True)
    finally:
        logger.info("Bot has stopped.")