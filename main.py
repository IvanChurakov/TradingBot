from bot.grid_bot import GridBot
from bot.utils import setup_logger
from ui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
import sys
import threading
import queue

data_queue = queue.Queue()

def run_bot():
    logger = setup_logger(log_file="logs/bot.log")
    try:
        bot = GridBot(test_mode=True, data_queue=data_queue)
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
        print("Bot stopped.")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    app = QApplication(sys.argv)
    main_window = MainWindow(data_queue)
    main_window.show()
    sys.exit(app.exec_())