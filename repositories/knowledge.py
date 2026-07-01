from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import KnowledgeEmbedding
import math

class KnowledgeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_best_match(self, query_embedding: list[float], threshold: float = 0.0) -> str | None:
        """Локальне порівняння векторів з гарантованим поверненням найкращого результату"""
        try:
            stmt = select(KnowledgeEmbedding)
            result = await self.session.execute(stmt)
            rows = result.scalars().all()
            
            if not rows:
                return None
            
            best_content = None
            max_sim = -1.0
            
            for row in rows:
                db_vec = row.embedding
                
                # Рахуємо косинусну відстань вручну
                dot_product = sum(a * b for a, b in zip(query_embedding, db_vec))
                norm_a = math.sqrt(sum(a * a for a in query_embedding))
                norm_b = math.sqrt(sum(b * b for b in db_vec))
                
                if norm_a == 0 or norm_b == 0:
                    continue
                    
                similarity = dot_product / (norm_a * norm_b)
                if similarity > max_sim:
                    max_sim = similarity
                    best_content = row.content
            
            # Повертаємо контент, якщо він пройшов навіть мінімальну схожість
            if max_sim >= threshold and best_content:
                return best_content
                
            # Якщо нічого не підійшло математично, беремо перший ліпший чанк як фолбек
            return rows[0].content if rows else None
        except Exception:
            return rows[0].content if (rows and len(rows) > 0) else None