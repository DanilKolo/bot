import asyncio
import logging
import os
from db import engine, Base, async_session_maker
from models import KnowledgeEmbedding
from services.embeddings import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    logger.info("=== СТАРТ ЛОКАЛЬНОЇ ІНІЦІАЛІЗАЦІЇ БАЗИ ДАНИХ ===")
    
    async with engine.begin() as conn:
        logger.info("Очищення старої структури даних...")
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("Створення нових таблиць SQLAlchemy...")
        await conn.run_sync(Base.metadata.create_all)
    
    file_path = "knowledge_base.txt"
    if not os.path.exists(file_path):
        logger.error(f"Файл {file_path} не знайдено!")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        text_data = f.read()

    chunks = [chunk.strip() for chunk in text_data.split("=== ") if chunk.strip()]
    chunks = ["=== " + chunk for chunk in chunks]

    logger.info(f"Знайдено {len(chunks)} логічних чанків.")
    embedding_service = EmbeddingService()

    async with async_session_maker() as session:
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Локальна векторизація чанку {i}/{len(chunks)}...")
            vector = await embedding_service.get_embedding(chunk)
            
            db_embedding = KnowledgeEmbedding(content=chunk, embedding=vector)
            session.add(db_embedding)
        
        await session.commit()
        logger.info("=== [УСПІХ] Локальна база знань повністю оновлена! ===")

if __name__ == "__main__":
    asyncio.run(init_database())