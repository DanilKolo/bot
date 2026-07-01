import logging
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.enums import ChatAction

from config import settings
from db import async_session_maker
from repositories.users import UserRepository
from services.rag import RagService

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація бота з об'єкта єдиного конфігу
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()


def clean_html_for_telegram(text: str) -> str:
    """Очищає текст від будь-яких HTML-тегів та маркдаун-блоків, які не підтримує Telegram"""
    if not text:
        return ""
    
    # Видаляємо маркдаун-обгортки коду типу ```html або ```, які ШІ іноді додає на початку/в кінці
    text = re.sub(r'```html', '', text)
    text = re.sub(r'```', '', text)
    
    # Замінюємо абзаци на переноси рядків
    text = text.replace("<p>", "").replace("</p>", "\n")
    text = text.replace("<li>", "• ").replace("</li>", "\n")
    
    # Повністю видаляємо теги структури документу, які блокує Telegram
    unsupported_tags = [
        "<html>", "</html>", "<head>", "</head>", "<body>", "</body>",
        "<ul>", "</ul>", "<ol>", "</ol>", "<div>", "</div>", "<span>", "</span>"
    ]
    for tag in unsupported_tags:
        text = text.replace(tag, "")
        text = text.replace(tag.upper(), "") # Про всяк випадок у верхньому регістрі
        
    # Чистимо будь-які інші випадкові теги, крім дозволених (b, i, code, s, u, a)
    # залишаємо тільки текст всередині них
    text = re.sub(r'<(?!/?(b|i|code|s|u|a)\b)[^>]+>', '', text)
        
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обробка команди /start за архітектурним патерном Handler -> Repository"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    # Працюємо з БД через сесію з пулу
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        try:
            await user_repo.upsert_user(user_id, first_name, username)
            logger.info(f"[БД] Успішна перевірка/реєстрація юзера {user_id}")
        except Exception as e:
            logger.error(f"[Помилка БД при /start]: {e}", exc_info=True)

    welcome_text = (
        f"👋 Вітаю, <b>{first_name}</b>!\n\n"
        "Я ваш новий архітектурно правильний технічний асистент по бензопилах STIHL.\n"
        "Задайте мені будь-яке текстове питання, і я допоможу!"
    )
    await message.answer(welcome_text, parse_mode="HTML")


@dp.message()
async def echo_handler(message: types.Message):
    """Обробка повідомлень за патерном Handler -> Service -> Repository -> DB"""
    
    # Контроль вхідних даних: якщо прилетіло фото/стікер замість тексту
    if not message.text:
        await message.answer("🤖 Я підтримую лише текстові запитання щодо обслуговування бензопил.")
        return

    user_query = message.text
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    # Створюємо сесію та викликаємо бізнес-логіку RAG
    async with async_session_maker() as session:
        rag_service = RagService(session)
        try:
            response_text = await rag_service.answer_question(user_query)
            
            # ФІЛЬТРАЦІЯ: Очищаємо згенерований текст від заборонених тегів перед відправкою
            formatted_text = clean_html_for_telegram(response_text)
            
            await message.answer(formatted_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"[Критична помилка хандлера]: {e}", exc_info=True)
            # Користувач бачить дружнє повідомлення, а не сирий код помилки
            await message.answer("⚙️ Вибачте, виникла внутрішня помилка сервера. Спробуйте пізніше або перевірте налаштування бази даних.")


async def main():
    logger.info("=== СТАРТ СКРИПТА БОТА ===")
    logger.info("Усі архітектурні шари підключено. Запуск Long Polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nБот зупинений.")