from bot.grid_bot import GridBot
from bot.utils import setup_logger

if __name__ == "__main__":
    logger = setup_logger(log_file="logs/bot.log")
    try:
        bot = GridBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
        print("Bot stopped.")