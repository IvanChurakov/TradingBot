import matplotlib.pyplot as plt
import pandas as pd
import json

# Завантаження даних з файлу
with open('data/backtest_results_parallel.json', 'r') as file:
    data = json.load(file)

# Створення DataFrame
df = pd.DataFrame(data)

# Відфільтрування даних для grid_levels_count = 20
df_filtered = df[df['grid_levels_count'] == 20]

# Сортування даних за days_period
df_sorted = df_filtered.sort_values('days_period')

# Створення графіків
plt.figure(figsize=(10, 5))

# Графік для total_balance
plt.plot(df_sorted['days_period'], df_sorted['total_balance'], label='Total Balance', marker='o')

# Графік для usdt_balance_plus_btc_bought_value
plt.plot(df_sorted['days_period'], df_sorted['usdt_balance_plus_btc_bought_value'], label='USDT + BTC Bought Value', marker='x')

# Налаштування графіка
plt.title('Backtest Results for Grid Level Count 20')
plt.xlabel('Days Period')
plt.ylabel('Balance')
plt.grid(True)
plt.legend()

# Показати графік
plt.show()