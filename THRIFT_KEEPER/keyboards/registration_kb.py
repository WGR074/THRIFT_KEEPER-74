from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

VALID_CURRENCIES = ['RUB', 'USD', 'EUR']

def get_currency_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 RUB", callback_data="currency_RUB")],
        [InlineKeyboardButton(text="🇺🇸 USD", callback_data="currency_USD")],
        [InlineKeyboardButton(text="🇪🇺 EUR", callback_data="currency_EUR")]
    ])

def get_notification_period_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ежедневно", callback_data="notify_day")],
        [InlineKeyboardButton(text="Еженедельно", callback_data="notify_week")],
        [InlineKeyboardButton(text="Ежемесячно", callback_data="notify_month")],
    ])

def get_period_name(period):
    return {
        'day': 'день',
        'week': 'неделю',
        'month': 'месяц'
    }.get(period, 'неизвестный период')