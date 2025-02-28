from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QDateTimeEdit, QMessageBox, QDateEdit
)
from PyQt5.QtCore import QDateTime

from bot.risk_management import RiskManager
from bot.grid_strategy import GridStrategy
from bot.trading_strategy import TradingStrategy
from configs.settings import Settings
from ui.plot_widget import PlotWidget
from data.market_data import MarketData


class MainWindow(QMainWindow):
    def __init__(self, http_session):
        super().__init__()
        self.setWindowTitle("Grid Bot Dashboard")
        self.setGeometry(100, 100, 1000, 600)

        self.http_session = http_session
        self.market_data = MarketData(self.http_session)

        self.settings = Settings()
        self.grid_strategy = GridStrategy(self.settings)
        self.risk_manager = RiskManager(self.settings)
        self.trading_strategy = TradingStrategy(self.settings)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.plot_widget = PlotWidget()
        self.layout.addWidget(self.plot_widget)

        self.controls_layout = QHBoxLayout()

        # Поля вибору дати і часу з випадаючим календарем
        self.from_datetime = QDateTimeEdit(QDateTime.currentDateTime())
        self.from_datetime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.from_datetime.setCalendarPopup(True)  # Увімкнення календаря

        self.to_datetime = QDateTimeEdit(QDateTime.currentDateTime())
        self.to_datetime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.to_datetime.setCalendarPopup(True)  # Увімкнення календаря

        # Кнопки
        self.fetch_button = QPushButton("Fetch Prices")
        self.fetch_button.clicked.connect(self.fetch_prices)

        self.build_grid_button = QPushButton("Build Grids")
        self.build_grid_button.clicked.connect(self.build_grids)

        self.run_backtest_button = QPushButton("Run Backtest")
        self.run_backtest_button.clicked.connect(self.run_backtest)

        # Додавання віджетів до Layout
        self.controls_layout.addWidget(QLabel("From:"))
        self.controls_layout.addWidget(self.from_datetime)
        self.controls_layout.addWidget(QLabel("To:"))
        self.controls_layout.addWidget(self.to_datetime)
        self.controls_layout.addWidget(self.fetch_button)
        self.controls_layout.addWidget(self.build_grid_button)
        self.controls_layout.addWidget(self.run_backtest_button)

        self.layout.addLayout(self.controls_layout)

        self.price_data = []
        self.grid_levels = {"levels": [], "min": None, "max": None}
        self.trade_results = []
        self.allow_trading = False

    def fetch_prices(self):
        start = self.from_datetime.dateTime().toSecsSinceEpoch() * 1000
        end = self.to_datetime.dateTime().toSecsSinceEpoch() * 1000

        try:
            self.price_data = self.market_data.fetch_data_for_period(
                symbol=self.settings.symbol,
                start_datetime=start,
                end_datetime=end,
                interval="1",
            )

            self.plot_widget.update_data({
                "price_data": self.price_data,
                "grid_levels": self.grid_levels
            })

            prices = [item["close_price"] for item in self.price_data]
            self.allow_trading = self.risk_manager.can_execute_trade(prices)

            if self.allow_trading:
                QMessageBox.information(self, "Success", "Trading is allowed!")
            else:
                QMessageBox.information(self, "Success", "Trading is not allowed!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch prices: {e}")

    def build_grids(self):
        if not self.price_data:
            QMessageBox.warning(self, "Warning", "No price data available. Fetch prices first.")
            return

        try:
            prices = [item["close_price"] for item in self.price_data]
            self.grid_levels = self.grid_strategy.calculate_grid_levels_with_percentile(prices)

            self.plot_widget.update_data({
                "price_data": self.price_data,
                "grid_levels": self.grid_levels
            })

            QMessageBox.information(self, "Success", "Grids built and graph updated!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to build grids: {e}")

    def run_backtest(self):
        # Налаштування інтервалу оновлення грідів (у днях)
        grid_recalculation_interval_days = 1  # Можна змінити на будь-яке значення

        # Обчислюємо часові періоди у мілісекундах
        start = self.from_datetime.dateTime().toSecsSinceEpoch() * 1000
        end = self.to_datetime.dateTime().toSecsSinceEpoch() * 1000

        # Тривалість одного дня (у мс)
        one_day_ms = 24 * 60 * 60 * 1000

        # Тривалість інтервалу між оновленнями грідів (у мс)
        recalculation_interval_ms = grid_recalculation_interval_days * one_day_ms

        print("Fetching price data...")

        # Ретріваємо дані за два періоди:
        # 1. Історичні дані (за місяць до початку)
        # 2. Дані для основного періоду бектесту
        historical_price_data = self.market_data.fetch_data_for_period(
            symbol=self.settings.symbol,
            start_datetime=start - (20 * one_day_ms),  # Дані за місяць до старту
            end_datetime=start,
            interval="1",
        )

        if not historical_price_data:
            QMessageBox.warning(self, "Warning", "No historical price data for the grid calculation.")
            return

        backtest_price_data = self.market_data.fetch_data_for_period(
            symbol=self.settings.symbol,
            start_datetime=start,
            end_datetime=end,
            interval="1",
        )

        if not backtest_price_data:
            QMessageBox.warning(self, "Warning", "No price data for the backtest period.")
            return

        print("Starting backtest...")

        # Побудова грідів на основі історичних даних перед початком бектесту
        historical_prices = [item["close_price"] for item in historical_price_data]
        self.grid_levels = self.grid_strategy.calculate_grid_levels_with_percentile(historical_prices, 20)
        self.trading_strategy.update_grid_levels(self.grid_levels)

        # Запуск бектесту тільки на основному періоді
        next_grid_recalculation_time = start  # Час для першого перерахунку грідів

        for point in backtest_price_data:
            timestamp = point["timestamp"]
            close_price = point["close_price"]

            # Перевіряємо, чи настав час для перерахунку грідів
            if timestamp >= next_grid_recalculation_time:
                print(f"Recalculating grid levels at {timestamp}...")

                # Витягуємо дані за останній місяць (30 днів) до поточного моменту з основного періоду
                start_time_for_calculation = timestamp - (20 * one_day_ms)
                relevant_prices = [
                    p["close_price"]
                    for p in historical_price_data + backtest_price_data
                    if start_time_for_calculation <= p["timestamp"] < timestamp
                ]

                if not relevant_prices:
                    print(f"No sufficient data for recalculation at {timestamp}")
                else:
                    self.grid_levels = self.grid_strategy.calculate_grid_levels_with_percentile(relevant_prices, 20)
                    self.trading_strategy.update_grid_levels(self.grid_levels)

                # Оновлюємо час наступного перерахунку
                next_grid_recalculation_time += recalculation_interval_ms

            # Передаємо поточну ціну в стратегію для обробки
            self.trading_strategy.process_price(close_price, timestamp=timestamp)

        # Вивід результатів
        total_profit = sum(trade["profit"] for trade in self.trading_strategy.trade_results if "profit" in trade)
        QMessageBox.information(
            self,
            "Backtest Complete",
            f"Backtest finished successfully.\nTotal Profit: {total_profit:.2f} USDT"
        )

        # Підрахунок портфеля
        balance = self.trading_strategy.get_portfolio_balance(backtest_price_data[-1]["close_price"])

        # Передаємо фінальні дані у віджет
        self.plot_widget.update_data({
            "price_data": backtest_price_data,
            "grid_levels": self.grid_levels,
            "trade_results": self.trading_strategy.trade_results,
        })