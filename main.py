from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from configs.settings import Settings
from pybit.unified_trading import HTTP

if __name__ == "__main__":
    app = QApplication([])

    settings = Settings()
    http_session = HTTP(
        api_key=settings.api_key,
        api_secret=settings.api_secret,
        testnet=False
    )

    main_window = MainWindow(http_session)
    main_window.show()

    app.exec_()