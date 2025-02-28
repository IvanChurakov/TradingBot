import json
import datetime
from tabulate import tabulate
from concurrent.futures import ProcessPoolExecutor  # Для розпаралелення

from bot.grid_strategy import GridStrategy
from bot.trading_strategy import TradingStrategy
from configs.settings import Settings


def backtest_task(args):
    """
    Одна задача для бектесту з певними параметрами.
    :param args: Кортеж з параметрами.
    :return: Результати бектесту для однієї комбінації параметрів.
    """
    filepath, symbol, start_date, end_date, grid_levels_count, days_period = args

    # Завантаження даних
    with open(filepath, "r") as file:
        historical_data = json.load(file)

    # Конвертуємо дати в UNIX timestamp (мс)
    start_timestamp = int(datetime.datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
    end_timestamp = int(datetime.datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)

    # Відбираємо дані для бектесту
    backtest_data = [point for point in historical_data if start_timestamp <= point["timestamp"] <= end_timestamp]
    if not backtest_data:
        return None  # Пропускаємо, якщо даних для бектесту немає

    # Попередні дані для розрахунку грідів
    historical_data_for_grid = [
        point for point in historical_data if
        start_timestamp > point["timestamp"] >= start_timestamp - days_period * 24 * 60 * 60 * 1000
    ]

    if not historical_data_for_grid:
        return None  # Пропускаємо, якщо недостатньо попередніх даних

    # Ініціалізуємо стратегії
    grid_strategy = GridStrategy(Settings())
    trading_strategy = TradingStrategy(Settings())

    # Початковий розрахунок грідів
    historical_prices = [item["close_price"] for item in historical_data_for_grid]
    grid_levels = grid_strategy.calculate_grid_levels_with_percentile(historical_prices, grid_levels_count)
    trading_strategy.update_grid_levels(grid_levels)

    # Запуск бектесту
    next_grid_recalculation_time = start_timestamp
    one_day_ms = 24 * 60 * 60 * 1000  # Один день у мілісекундах
    recalculation_interval_ms = one_day_ms  # Інтервал оновлення грідів у 1 день

    for point in backtest_data:
        timestamp = point["timestamp"]
        close_price = point["close_price"]

        # Перерахунок грідів для поточного періоду
        if timestamp >= next_grid_recalculation_time:
            start_time_for_calculation = timestamp - days_period * one_day_ms
            relevant_prices = [
                p["close_price"]
                for p in historical_data
                if start_time_for_calculation <= p["timestamp"] < timestamp
            ]
            if relevant_prices:
                grid_levels = grid_strategy.calculate_grid_levels_with_percentile(relevant_prices,
                                                                                  grid_levels_count)
                trading_strategy.update_grid_levels(grid_levels)

            next_grid_recalculation_time += recalculation_interval_ms

        # Передаємо поточну ціну в торгову стратегію
        trading_strategy.process_price(close_price, timestamp=timestamp)

    # Розрахунок результатів
    portfolio_balance = trading_strategy.get_portfolio_balance(backtest_data[-1]["close_price"])

    print(f"RESULT: Grid Levels: {grid_levels_count}, Period: {days_period} days, "
          f"Total Balance: {portfolio_balance['total_balance']:.2f}, "
          f"USDT + BTC Bought Value: {portfolio_balance['usdt_balance'] + portfolio_balance['btc_bought_value']:.2f}")

    return {
        "grid_levels_count": grid_levels_count,
        "days_period": days_period,
        "total_balance": portfolio_balance['total_balance'],
        "usdt_balance_plus_btc_bought_value": portfolio_balance['usdt_balance'] + portfolio_balance['btc_bought_value']
    }


def run_parallel_backtest(filepath, symbol, start_date, end_date, output_file):
    results = []  # Список для збереження результатів
    days_options = list(range(14, 91))  # Періоди в днях для тестування грідів (від 14 до 90 днів)
    grid_levels_counts = range(20, 21)  # Значення grid_levels_count (від 5 до 200)

    # Список усіх можливих комбінацій параметрів
    tasks = [
        (filepath, symbol, start_date, end_date, grid_levels_count, days_period)
        for grid_levels_count in grid_levels_counts
        for days_period in days_options
    ]

    # Паралельне виконання задач
    with ProcessPoolExecutor() as executor:
        for result in executor.map(backtest_task, tasks):
            if result:
                # Зберігання результатів
                results.append(result)

                # Запис у файл для збереження прогресу
                with open(output_file, "w") as file:
                    json.dump(results, file, indent=4)

    return results


# Основна точка запуску
if __name__ == "__main__":
    # Шлях до JSON-файлу
    sorted_filepath = "data/historical_data/btc_historical_data_sorted.json"
    symbol = "BTCUSDT"

    # Діапазон дат для бектесту
    start_date = "2021-07-06"
    end_date = "2027-02-26"

    # Шлях для збереження результатів
    output_filepath = "data/backtest_results_parallel.json"

    # Виконуємо паралельний бектест
    results = run_parallel_backtest(sorted_filepath, symbol, start_date, end_date, output_filepath)

    # Формування таблиці результатів
    table = [
        [result["grid_levels_count"], result["days_period"], result["total_balance"],
         result["usdt_balance_plus_btc_bought_value"]]
        for result in results
    ]

    # Виводимо таблицю у консоль
    print(tabulate(table, headers=["Grid Levels Count", "Days Period", "Total Balance",
                                   "USDT + BTC Bought Value"], tablefmt="grid"))