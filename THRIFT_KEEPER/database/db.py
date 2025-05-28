import sqlite3
from datetime import datetime, date
from typing import Optional, Dict, List
from decimal import Decimal

import sqlite3
from datetime import datetime, date
from typing import Optional, Dict, List
from decimal import Decimal, InvalidOperation

class Database:
    def __init__(self, db_name='finance.db'):
        self.db_name = db_name
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Инициализация структуры базы данных"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    currency TEXT DEFAULT 'RUB',
                    reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Таблица транзакций
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL CHECK(amount > 0),
                    category TEXT NOT NULL,
                    type TEXT CHECK(type IN ('income', 'expense')) NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            # Таблица целей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    target_amount REAL NOT NULL CHECK(target_amount > 0),
                    current_amount REAL DEFAULT 0,
                    deadline DATE,
                    is_completed BOOLEAN DEFAULT 0,
                    created_at DATE DEFAULT CURRENT_DATE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при инициализации БД: {e}")
        finally:
            conn.close()

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получает данные пользователя"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Ошибка при получении пользователя: {e}")
            return None
        finally:
            conn.close()

    def save_user(self, user_id: int, name: str, currency: str = 'RUB') -> bool:
        """Сохраняет или обновляет пользователя"""
        conn = self._get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO users (user_id, first_name, currency) VALUES (?, ?, ?)",
                (user_id, name, currency)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении пользователя: {e}")
            return False
        finally:
            conn.close()

    def add_transaction(self, user_id: int, amount: Decimal, category: str,
                        transaction_type: str, description: str = None) -> bool:
        """Добавляет транзакцию"""
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT INTO transactions 
                (user_id, amount, category, type, description, date)
                VALUES (?, ?, ?, ?, ?, datetime('now'))""",
                (user_id, float(amount), category, transaction_type, description)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при добавлении транзакции: {e}")
            return False
        finally:
            conn.close()

    def get_balance(self, user_id: int) -> Decimal:
        """Возвращает текущий баланс пользователя"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    (SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = 'income') -
                    (SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = 'expense')
                AS balance
            """, (user_id, user_id))
            result = cursor.fetchone()
            balance = result['balance'] if result and result['balance'] is not None else 0.0
            return Decimal(balance).quantize(Decimal('0.00'))
        except sqlite3.Error as e:
            print(f"Ошибка при получении баланса: {e}")
            return Decimal('0.00')
        finally:
            conn.close()

    def get_user_registration_date(self, user_id: int) -> Optional[datetime]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT reg_date FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            if result and result['reg_date']:
                date_str = result['reg_date']
                if len(date_str) == 10:
                    return datetime.strptime(date_str, '%Y-%m-%d')
                else:
                    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            return None
        except sqlite3.Error as e:
            print(f"Ошибка при получении даты регистрации: {e}")
            return None
        finally:
            conn.close()

    def get_statistics_by_period(self, user_id: int, start_date: datetime, end_date: datetime) -> dict:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Баланс
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) -
                    COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS balance
                FROM transactions
                WHERE user_id = ? AND date BETWEEN ? AND ?
            """, (user_id, start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")))
            balance_row = cursor.fetchone()
            balance = Decimal(balance_row['balance']).quantize(Decimal('0.00'))

            # Доходы и расходы
            cursor.execute("""
                SELECT type, SUM(amount) as total
                FROM transactions
                WHERE user_id = ? AND date BETWEEN ? AND ?
                GROUP BY type
            """, (user_id, start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")))
            totals = cursor.fetchall()
            total_income = sum(t['total'] for t in totals if t['type'] == 'income')
            total_expenses = sum(t['total'] for t in totals if t['type'] == 'expense')

            # Расходы по категориям
            cursor.execute("""
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE user_id = ? AND type = 'expense' AND date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY total DESC
                LIMIT 5
            """, (user_id, start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")))
            expenses_by_category = [(row['category'], row['total']) for row in cursor.fetchall()]

            # Последние транзакции
            cursor.execute("""
                SELECT category, amount, description, type, date
                FROM transactions
                WHERE user_id = ? AND date BETWEEN ? AND ?
                ORDER BY date DESC
                LIMIT 5
            """, (user_id, start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")))
            recent_transactions = [dict(row) for row in cursor.fetchall()]

            return {
                "balance": balance,
                "total_income": Decimal(total_income).quantize(Decimal('0.00')),
                "total_expenses": Decimal(total_expenses).quantize(Decimal('0.00')),
                "expenses_by_category": expenses_by_category,
                "recent_transactions": recent_transactions
            }

        except sqlite3.Error as e:
            print(f"Ошибка при получении статистики: {e}")
            return {}
        finally:
            conn.close()

    def get_goals(self, user_id: int) -> List[Dict]:
        """Возвращает активные цели пользователя"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM goals WHERE user_id = ? AND is_completed = 0", (user_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Ошибка при получении целей: {e}")
            return []
        finally:
            conn.close()

    def get_goal_by_id(self, goal_id: int) -> Optional[Dict]:
        """Получает цель по её ID"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Ошибка при получении цели: {e}")
            return None
        finally:
            conn.close()

    def update_goal_amount(self, goal_id: int, amount: Decimal) -> tuple[bool, bool]:
        """Обновляет сумму в цели и проверяет завершение"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT current_amount, target_amount FROM goals WHERE id = ?", (goal_id,))
            result = cursor.fetchone()
            if not result:
                return False, False

            new_amount = result['current_amount'] + float(amount)
            completed = new_amount >= result['target_amount']

            cursor.execute(
                "UPDATE goals SET current_amount = ?, is_completed = ? WHERE id = ?",
                (new_amount, 1 if completed else 0, goal_id)
            )
            conn.commit()
            return True, completed
        except sqlite3.Error as e:
            print(f"Ошибка при пополнении цели: {e}")
            return False, False
        finally:
            conn.close()

    def withdraw_from_goal(self, goal_id: int, amount: Decimal) -> bool:
        """Снимает средства с цели"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT current_amount FROM goals WHERE id = ?", (goal_id,))
            result = cursor.fetchone()
            if not result or result['current_amount'] < float(amount):
                return False

            new_amount = max(result['current_amount'] - float(amount), 0)
            cursor.execute(
                "UPDATE goals SET current_amount = ? WHERE id = ?", 
                (new_amount, goal_id)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при снятии средств: {e}")
            return False
        finally:
            conn.close()

    def add_goal(self, user_id: int, name: str, target_amount: Decimal, deadline: Optional[date] = None) -> bool:
        """Добавляет новую цель"""
        conn = self._get_connection()
        try:
            deadline_str = deadline.strftime("%Y-%m-%d") if deadline else None
            conn.execute("""
                INSERT INTO goals (user_id, name, target_amount, deadline)
                VALUES (?, ?, ?, ?)
            """, (user_id, name, float(target_amount), deadline_str))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при добавлении цели: {e}")
            return False
        finally:
            conn.close()

    def get_expired_goals(self, user_id: int) -> List[Dict]:
        """Возвращает истёкшие цели"""
        today = date.today().strftime("%Y-%m-%d")
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM goals 
                WHERE user_id = ? AND deadline < ? AND is_completed = 0
            """, (user_id, today))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Ошибка при получении истёкших целей: {e}")
            return []
        finally:
            conn.close()

    def extend_goal_deadline(self, goal_id: int, new_date: date) -> bool:
        """Продлевает срок цели"""
        conn = self._get_connection()
        try:
            new_date_str = new_date.strftime("%Y-%m-%d")
            conn.execute(
                "UPDATE goals SET deadline = ?, is_completed = 0 WHERE id = ?",
                (new_date_str, goal_id)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при продлении дедлайна: {e}")
            return False
        finally:
            conn.close()

    def delete_goal(self, goal_id: int) -> bool:
        """Удаляет цель"""
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при удалении цели: {e}")
            return False
        finally:
            conn.close()

    def mark_goal_as_failed(self, goal_id: int) -> bool:
        """Помечает цель как проваленную"""
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE goals SET is_completed = 1 WHERE id = ?",
                (goal_id,)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при отметке цели: {e}")
            return False
        finally:
            conn.close()

    def get_all_goals(self, user_id: int) -> List[Dict]:
        """Получает все цели пользователя"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM goals WHERE user_id = ?", (user_id,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Ошибка при получении целей: {e}")
            return []
        finally:
            conn.close()
    
    def get_completed_goals(self, user_id: int) -> List[Dict]:
        """Возвращает выполненные цели"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM goals 
                WHERE user_id = ? AND is_completed = 1
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def extend_goal_deadline(self, goal_id: int, new_date: date) -> bool:
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE goals SET deadline = ? WHERE id = ?",
                (new_date.strftime("%Y-%m-%d"), goal_id)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при продлении дедлайна: {e}")
            return False
        finally:
            conn.close()

    def update_goal_name(self, goal_id: int, new_name: str) -> bool:
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE goals SET name = ? WHERE id = ?",
                (new_name, goal_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при изменении названия цели: {e}")
            return False
        finally:
            conn.close()

    def update_goal_target_amount(self, goal_id: int, new_amount: float) -> bool:
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE goals SET target_amount = ? WHERE id = ?",
                (new_amount, goal_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при изменении суммы цели: {e}")
            return False
        finally:
            conn.close()

    def update_goal_deadline(self, goal_id: int, new_deadline: date) -> bool:
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE goals SET deadline = ? WHERE id = ?",
                (new_deadline.strftime("%Y-%m-%d"), goal_id)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при изменении дедлайна: {e}")
            return False
        finally:
            conn.close()

    def get_goal_by_name(self, user_id: int, goal_name: str) -> Optional[Dict]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM goals WHERE user_id = ? AND name = ?",
                (user_id, goal_name)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Ошибка при получении цели по имени: {e}")
            return None
        finally:
            conn.close()

    def update_goal_current_amount(self, goal_id: int, amount: float) -> bool:
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE goals SET current_amount = ? WHERE id = ?",
                (amount, goal_id)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении текущей суммы цели: {e}")
            return False
        finally:
            conn.close()