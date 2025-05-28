import sqlite3
from typing import Optional, Dict
from datetime import datetime
from database.db import Database  # Импортируем наш единый класс Database

class UserManager:
    def __init__(self, db: Database):
        self.db = db

    def create_user(self, user_id: int, first_name: str, currency: str = 'RUB') -> bool:
        """
        Создает нового пользователя или обновляет существующего
        :param user_id: ID пользователя Telegram
        :param first_name: Имя пользователя
        :param currency: Валюта (по умолчанию RUB)
        :return: True если успешно, False при ошибке
        """
        return self.db.save_user(user_id, first_name, currency)

    def get_user(self, user_id: int) -> Optional[Dict]:
        """
        Получает данные пользователя
        :param user_id: ID пользователя Telegram
        :return: Словарь с данными пользователя или None если не найден
        """
        return self.db.get_user(user_id)

    def update_currency(self, user_id: int, currency: str) -> bool:
        """
        Обновляет валюту пользователя
        :param user_id: ID пользователя Telegram
        :param currency: Новая валюта (RUB, USD, EUR)
        :return: True если успешно, False при ошибке
        """
        return self.db.update_currency(user_id, currency)

    def user_exists(self, user_id: int) -> bool:
        """
        Проверяет существует ли пользователь
        :param user_id: ID пользователя Telegram
        :return: True если существует, False если нет
        """
        return self.get_user(user_id) is not None

    def get_user_currency(self, user_id: int) -> Optional[str]:
        """
        Получает валюту пользователя
        :param user_id: ID пользователя Telegram
        :return: Код валюты или None если пользователь не найден
        """
        user = self.get_user(user_id)
        return user.get('currency') if user else None

    def get_registration_date(self, user_id: int) -> Optional[datetime]:
        """
        Получает дату регистрации пользователя
        :param user_id: ID пользователя Telegram
        :return: Объект datetime или None если пользователь не найден
        """
        user = self.get_user(user_id)
        if user and 'reg_date' in user:
            return datetime.strptime(user['reg_date'], '%Y-%m-%d %H:%M:%S')
        return None