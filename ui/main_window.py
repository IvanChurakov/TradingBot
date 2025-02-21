from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from ui.plot_widget import PlotWidget

class MainWindow(QMainWindow):
    def __init__(self, data_queue):
        super().__init__()
        self.setWindowTitle("Grid Bot Dashboard")
        self.setGeometry(100, 100, 800, 600)
        self.data_queue = data_queue

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.plot_widget = PlotWidget()
        self.layout.addWidget(self.plot_widget)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_from_queue)
        self.timer.start(1000)

    def update_from_queue(self):
        while not self.data_queue.empty():
            data = self.data_queue.get()
            self.plot_widget.update_data(data)