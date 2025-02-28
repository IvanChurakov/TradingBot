import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        self.price_data = []
        self.grid_levels = {"levels": [], "min": None, "max": None}
        self.active_orders = []
        self.trade_results = []

    def update_data(self, data):
        self.price_data = data.get("price_data", [])
        self.active_orders = data.get("active_orders", [])
        self.trade_results = data.get("trade_results", [])
        self.grid_levels = data.get("grid_levels", {"levels": [], "min": None, "max": None})

        self.plot_chart()

    def _add_unique_records(self, existing_records, new_records, unique_keys):
        if isinstance(unique_keys, str):
            unique_keys = [unique_keys]

        existing_keys_set = {
            tuple(record[key] for key in unique_keys)
            for record in existing_records
        }

        for record in new_records:
            record_keys = tuple(record[key] for key in unique_keys)
            if record_keys not in existing_keys_set:
                existing_records.append(record)
                existing_keys_set.add(record_keys)

        return existing_records

    def plot_chart(self):
        ax = self.figure.add_subplot(111)
        ax.clear()

        if self.price_data:
            timestamps = [price["timestamp"] for price in self.price_data]
            prices = [price["close_price"] for price in self.price_data]

            readable_timestamps = [datetime.datetime.fromtimestamp(ts / 1000) for ts in timestamps]

            ax.plot(readable_timestamps, prices, label="Price (USDT)", color="blue", linewidth=2)

            ax.set_xticks([])
            ax.set_xlabel("")

        grid_levels = self.grid_levels.get("levels", [])
        last_price = self.price_data[-1]["close_price"] if self.price_data else None
        if last_price is not None:
            for level in grid_levels:
                color = "lightgreen" if level > last_price else "lightcoral"
                ax.axhline(
                    y=level,
                    linestyle="--",
                    color=color,
                    alpha=0.8,
                    label="Grid Level" if level == grid_levels[0] else None
                )

        """
        for order in self.active_orders:
            if order["action"] == "BUY":
                ax.scatter(datetime.datetime.fromtimestamp(order["timestamp"] / 1000), order["price"], color="green",
                           label="Buy Order" if order == self.active_orders[0] else None)
            elif order["action"] == "SELL":
                ax.scatter(datetime.datetime.fromtimestamp(order["timestamp"] / 1000), order["price"], color="red",
                           label="Sell Order" if order == self.active_orders[0] else None)
        
        for trade in self.trade_results:
            if trade["action"] == "BUY":
                ax.scatter(datetime.datetime.fromtimestamp(trade["timestamp"] / 1000), trade["price"], color="blue",
                           label="Executed Buy" if trade == self.trade_results[0] else None)
            elif trade["action"] == "SELL":
                ax.scatter(datetime.datetime.fromtimestamp(trade["timestamp"] / 1000), trade["price"], color="orange",
                           label="Executed Sell" if trade == self.trade_results[0] else None)
        """
        ax.set_title("Grid Levels, Active Orders, Executed Trades, and Token Price")
        ax.set_xlabel("Time")
        ax.set_ylabel("Price (USDT)")
        ax.legend()
        self.canvas.draw()