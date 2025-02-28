from PyQt5.QtCore import QThread, pyqtSignal
import time
from queue import Queue, Empty


class QueueProcessorThread(QThread):
    data_received = pyqtSignal(dict)  # Сигнал для передачі даних у UI

    def __init__(self, data_queue, poll_interval=0.5):
        """
        Потік для асинхронної обробки черги.

        :param data_queue: Черга обміну даними.
        :param poll_interval: Інтервал перевірки черги (в секундах).
        """
        super().__init__()
        self.data_queue = data_queue
        self.poll_interval = poll_interval
        self.running = True  # Прапорець для зупинки потоку

    def run(self):
        """Основний цикл обробки черги."""
        try:
            while self.running:
                try:
                    # Чекаємо на нові дані в черзі (зупиняємося, якщо порожньо)
                    data = self.data_queue.get(timeout=self.poll_interval)
                    print(f"QueueProcessorThread: отримано дані: {data}")  # Для діагностики

                    # Передаємо дані через сигнал
                    self.data_received.emit(data)
                except Empty:
                    # Черга порожня — чекаємо
                    continue

        except Exception as e:
            print(f"QueueProcessorThread помилка: {e}")  # Звіт про невідому помилку

    def stop(self):
        """Переривання роботи потоку."""
        self.running = False
        self.wait()