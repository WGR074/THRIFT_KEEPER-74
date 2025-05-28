# THRIFT_KEEPER-74

**THRIFT_KEEPER** — это Telegram-бот для ведения личного бюджета. Позволяет добавлять доходы и расходы, управлять целями, отслеживать статистику и получать отчёты.

## 🚀 Возможности
- Учёт доходов и расходов
- Финансовые цели и прогресс
- Статистика и отчёты
- Мультивалютность
- FSM-сценарии и интерактивные клавиатуры
- Хранение данных в SQLite

## 📦 Установка

```bash
git clone https://github.com/yourusername/thrift_keeper_bot.git
cd thrift_keeper_bot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## ⚙️ Настройка

Создайте файл `.env` в корне проекта:

```
BOT_TOKEN=ваш_токен_бота
```

Файл `.env` добавлен в `.gitignore`, чтобы не попасть в репозиторий.

## 🏃 Запуск

```bash
python main.py
```

## 📄 Лицензия

Проект распространяется под лицензией MIT.
