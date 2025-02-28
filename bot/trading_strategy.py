class TradingStrategy:
    def __init__(self, settings):
        self.settings = settings
        self.grid_levels = {"levels": [], "min": None, "max": None}
        self.balance = 1000  # Повний баланс для торгівлі
        self.positions = []  # Список активних покупок
        self.trade_results = []  # Історія виконаних угод (купівля/продаж)

    def process_price(self, current_price, timestamp):
        decisions = []

        # Якщо поточна ціна поза діапазоном — нічого не робимо
        if current_price < min(self.grid_levels["levels"]) or current_price > max(self.grid_levels["levels"]):
            return decisions

        # Визначаємо поточний рівень гріду
        lower_grid = max((level for level in self.grid_levels["levels"] if level <= current_price), default=None)
        upper_grid = min((level for level in self.grid_levels["levels"] if level >= current_price), default=None)

        grid_distance = upper_grid - lower_grid
        lower_buy_threshold = lower_grid + grid_distance * 0.49  # 49% до середини
        upper_sell_threshold = upper_grid - grid_distance * 0.49  # 49% догори

        # 1. Купівля: якщо ціна входить у нижню зону гріду
        # Розрахунок суми для покупки як % від поточного балансу
        buy_percentage = self.settings.buy_percentage
        min_transaction_amount = self.settings.min_transaction_amount

        # Розрахунок суми для покупки: або buy_percentage від балансу, або мінімальна сума
        calculated_amount_to_spend = self.balance * buy_percentage
        amount_to_spend = max(calculated_amount_to_spend, min_transaction_amount)

        if lower_grid <= current_price < lower_buy_threshold and self.balance >= amount_to_spend:
            bought_amount = amount_to_spend / current_price  # Купівля активів на розраховану суму
            self.positions.append({
                "price": current_price,
                "amount": bought_amount,
                "timestamp": timestamp,
            })
            self.balance -= amount_to_spend  # Зменшуємо баланс на витрачену суму

            self.trade_results.append({
                "action": "BUY",
                "price": current_price,
                "amount": bought_amount,
                "timestamp": timestamp,
            })
            decisions.append(f"BUY {bought_amount:.6f} @ {current_price:.2f}")
            print(f"BUY @ {current_price:.7f}, Amount: {bought_amount:.6f}, Remaining Balance: {self.balance:.2f}")

        # 2. Продаж: якщо ціна входить у верхню зону гріду
        if upper_grid >= current_price > upper_sell_threshold:
            # 2.1 Знаходимо перший прибутковий ордер
            active_order = next((order for order in self.positions if current_price > order["price"]), None)
            if active_order is not None:
                self.positions.remove(active_order)  # Видаляємо проданий ордер із позицій
                profit = (current_price - active_order["price"]) * active_order["amount"]
                sale_amount = active_order["amount"] * current_price

                self.balance += sale_amount  # Додаємо до балансу суму від продажу

                self.trade_results.append({
                    "action": "SELL",
                    "buy_price": active_order["price"],
                    "sell_price": current_price,
                    "amount": active_order["amount"],
                    "profit": profit,
                    "timestamp": timestamp,
                })
                decisions.append(f"SELL {active_order['amount']:.6f} @ {current_price:.2f}")
                print(f"SELL @ {current_price:.7f}, Profit: {profit:.2f}, "
                      f"Sold Amount: {sale_amount:.2f}, Updated Balance: {self.balance:.2f}")

        return decisions

    def update_grid_levels(self, grid_levels):
        self.grid_levels = grid_levels

    def get_portfolio_balance(self, current_price):
        """
        Повертає повну інформацію про баланс портфеля.
        :param current_price: Поточна ціна активу.
        :return: Словник з деталями балансу.
        """
        # Баланс у USDT
        usdt_balance = self.balance

        # Вартість активу, який є у портфелі, за поточною ціною
        positions_usdt_value = sum(position["amount"] * current_price for position in self.positions)

        # Сумарний баланс
        total_balance = usdt_balance + positions_usdt_value

        # Кількість BTC у портфелі
        total_btc = sum(position["amount"] for position in self.positions)

        # Вартість купленого активу за початковою ціною покупки
        btc_bought_value = sum(position["amount"] * position["price"] for position in self.positions)

        # Формуємо результат
        result = {
            "usdt_balance": usdt_balance,
            "positions_usdt_value": positions_usdt_value,
            "btc_bought_value": btc_bought_value,
            "total_btc": total_btc,
            "total_balance": total_balance
        }

        # Виводимо портфель для зручності
        print(f"Portfolio Balance: "
              f"USDT Balance = {usdt_balance:.2f}, "
              f"BTC Value (current price) = {positions_usdt_value:.2f}, "
              f"BTC Bought Value = {btc_bought_value:.2f}, "
              f"Total BTC = {total_btc:.6f}, "
              f"Total = {total_balance:.2f}")
        return result