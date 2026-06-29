import os
import asyncio
import logging
from dotenv import load_dotenv
import asyncpg

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.enums import ChatAction

# Імпортуємо наш RAG-енджин з векторним пошуком
from rag_engine import answer_with_rag

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Завантаження змінних оточення
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(current_dir, '.env'), override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Помилка: BOT_TOKEN не знайдено у файлі .env!")

# Налаштування підключення до БД в Docker
DB_CONFIG = {
    "user": "danil_user",
    "password": "super_password123",
    "database": "rag_bot_database",
    "host": "127.0.0.1",
    "port": 5432
}

# Ініціалізація бота та диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def prepare_text_for_html(text: str) -> str:
    """
    Конвертує сирий текст від Gemini у правильний HTML формат для Telegram.
    Замінює подвійні зірочки на теги жирного шрифту, а одинарні — на красиві маркери списків.
    """
    if not text:
        return ""
    
    # 1. Екрануємо базові символи, які можуть зламати HTML-парсер Telegram
    formatted_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # 2. Перетворюємо пари подвійних зірочок (**текст**) на HTML-теги жирного (<b>текст</b>)
    while "**" in formatted_text:
        formatted_text = formatted_text.replace("**", "<b>", 1).replace("**", "</b>", 1)
        
    # 3. Замінюємо одинарні зірочки списків на акуратні крапки (буліти)
    formatted_text = formatted_text.replace("\n* ", "\n• ").replace("\n    * ", "\n    • ")
    
    return formatted_text

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обробка команди /start та реєстрація юзера в БД PostgreSQL"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    print(f"[БД] Спроба реєстрації користувача: {first_name} (ID: {user_id})")

    # Підключаємось до бази даних в Docker
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        # Записуємо користувача. Якщо такий ID вже є — ON CONFLICT DO NOTHING
        await conn.execute(
            """
            INSERT INTO users (user_id, first_name, username)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO NOTHING;
            """,
            user_id, first_name, username
        )
        await conn.close()
        print(f"[БД] Користувач {first_name} успішно оброблений/перевірений в таблиці users.")
    except Exception as e:
        print(f"[ПОМИЛКА БД при /start]: {e}")

    # Привітання користувача
    welcome_text = (
        f"👋 Вітаю, <b>{first_name}</b>!\n\n"
        "Я ваш інтелектуальний технічний асистент по бензопилах STIHL\n"
        "Задайте мені будь-яке технічне питання, і я знайду точну відповідь та допоможу!"
    )

    # Відправляємо привітання в режимі HTML
    await message.answer(welcome_text, parse_mode="HTML")

@dp.message()
async def echo_handler(message: types.Message):
    """Обробка будь-яких текстових запитань через векторний RAG з форматизацією в HTML"""
    user_query = message.text
    
    # Показуємо статус "typing..." (Бот друкує)
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    # Викликаємо наш векторний RAG
    response_text = await answer_with_rag(user_query)
    
    # Форматуємо зірочки в HTML теги залізобетонним методом
    html_response = prepare_text_for_html(response_text)
    
    try:
        # Відправляємо красиво відформатовану відповідь користувачу
        await message.answer(html_response, parse_mode="HTML")
    except Exception as parse_error:
        logging.error(f"Помилка парсингу HTML: {parse_error}")
        # Резервний варіант: якщо десь теги стали криво, відправляємо чистий текст, щоб бот не ліг
        await message.answer(response_text)

async def main():
    print("=== СТАРТ СКРИПТА БОТА ===")
    print("Перевірка налаштувань завершена. Бот запускається через HTML parse mode...")
    
    # Запуск Long Polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nБот зупинений користувачем.")