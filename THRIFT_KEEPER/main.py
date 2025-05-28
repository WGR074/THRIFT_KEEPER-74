import asyncio
import logging
import signal

from aiogram import Bot, Dispatcher

# Включаем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Временное решение - токен прямо в коде
BOT_TOKEN = "7717955107:AAHx0IQnaRy3TxNtRong3HK5DXUIan9cI70"

async def main():
    logger.info("🚀 Запуск бота...")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Удаляем вебхук
    await bot.delete_webhook(drop_pending_updates=True)

    # Подключаем роутеры
    from handlers.start import router as start_router
    from handlers.registration import router as registration_router
    from handlers.expenses import router as expenses_router
    from handlers.statistics import router as statistics_router
    from handlers.goals import router as goals_router
    from handlers.incomes import router as income_router
    from handlers.about import router as about_router
    from handlers.help import router as help_router
    

# Подключаем роутер
    dp.include_router(help_router)
    dp.include_router(about_router)
    dp.include_router(start_router)
    dp.include_router(registration_router)
    dp.include_router(expenses_router)
    dp.include_router(statistics_router)
    dp.include_router(goals_router)
    dp.include_router(income_router)

    logger.info("✅ Бот успешно запущен. Ожидание сообщений...")

    def stop_handler(*_):
        logger.info("🛑 Получен сигнал остановки бота...")
        raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем.")
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("🔌 Сессия бота закрыта.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Бот остановлен вручную.")