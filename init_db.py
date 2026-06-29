import os
import asyncio
import asyncpg
import json  # ДОДАЛИ ІМПОРТ ДЛЯ ФОРМАТУВАННЯ ВЕКТОРУ
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Завантажуємо конфігурацію
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(current_dir, '.env'), override=True)

# Налаштування підключення до PostgreSQL в Docker
DB_CONFIG = {
    "user": "danil_user",
    "password": "super_password123",
    "database": "rag_bot_database",
    "host": "127.0.0.1",
    "port": 5432
}

print("[ІНФО] Завантаження локальної моделі векторів...")
model = SentenceTransformer('all-MiniLM-L6-v2')

async def init_database():
    print("=== ЗАПУСК ЛОКАЛЬНОЇ ІНІЦІАЛІЗАЦІЇ БД ===")
    
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        print("[ОК] Успішно підключено до PostgreSQL в Docker.")
    except Exception as e:
        print(f"[ПОМИЛКА] Не вдалося підключитися до БД: {e}")
        return

    try:
        # Активація pgvector
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("[ОК] Розширення pgvector активовано.")

        # Створення таблиці користувачів
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                first_name VARCHAR(255) NOT NULL,
                username VARCHAR(255),
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("[ОК] Таблиця 'users' перевірена/створена.")

        # Створення таблиці для векторів (384 вимірів)
        await conn.execute("DROP TABLE IF EXISTS knowledge_embeddings;")
        await conn.execute("""
            CREATE TABLE knowledge_embeddings (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding vector(384)
            );
        """)
        print("[ОК] Таблиця 'knowledge_embeddings' створена.")

        # Читання тексту інструкції
        kb_path = os.path.join(current_dir, "knowledge_base.txt")
        with open(kb_path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
        print(f"[ІНФО] Знайдено {len(chunks)} чанків для обробки.")

        for idx, chunk in enumerate(chunks, 1):
            print(f"Обробка чанка {idx}/{len(chunks)}...")
            
            # Локальний прорахунок вектора
            embedding = model.encode(chunk)
            vector_data = embedding.tolist()
            
            # КОНВЕРТУЄМО LIST У STRING ДЛЯ PGVECTOR
            vector_string = json.dumps(vector_data)
            
            # Записуємо в PostgreSQL
            await conn.execute(
                "INSERT INTO knowledge_embeddings (content, embedding) VALUES ($1, $2);",
                chunk, vector_string
            )

        print("[УСПІХ] Локальна база знань про бензопилу успішно збережена в БД!")

    except Exception as e:
        print(f"[КРИТИЧНА ПОМИЛКА]: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(init_database())