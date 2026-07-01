from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config import settings

# Створюємо єдиний двигун для роботи з БД
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Постав True, якщо захочеш бачити сирі SQL-запити в консолі
    pool_size=10,
    max_overflow=20
)

# Фабрика для створення асинхронних сесій
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Базовий клас для наших моделей
class Base(DeclarativeBase):
    pass

async def get_session() -> AsyncSession:
    """Генератор сесій для використання в сервісах"""
    async with async_session_maker() as session:
        yield session