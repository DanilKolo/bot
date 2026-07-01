from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from models import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_user(self, user_id: int, first_name: str, username: str | None) -> None:
        """Додає користувача або ігнорує, якщо він вже є (без сирого SQL)"""
        stmt = insert(User).values(
            user_id=user_id,
            first_name=first_name,
            username=username
        ).on_conflict_do_nothing(index_elements=['user_id'])
        
        await self.session.execute(stmt)
        await self.session.commit()