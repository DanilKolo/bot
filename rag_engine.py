import os
import asyncio
import asyncpg
import json
import httpx
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Завантаження .env
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(current_dir, '.env'), override=True)

DB_CONFIG = {
    "user": "danil_user",
    "password": "super_password123",
    "database": "rag_bot_database",
    "host": "127.0.0.1",
    "port": 5432
}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Ініціалізуємо ту саму локальну модель для запитів
model = SentenceTransformer('all-MiniLM-L6-v2')

async def get_top_3_chunks(user_query: str) -> str:
    """Шукає ТОП-3 релевантних чанки в БД через локальний вектор"""
    try:
        # Локально перетворюємо питання в масив чисел
        embedding = model.encode(user_query)
        query_vector_json = json.dumps(embedding.tolist())
    except Exception as e:
        print(f"[ПОМИЛКА ЕМБЕДІНГУ]: {e}")
        return "Помилка при створенні вектора запиту."

    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        rows = await conn.fetch(
            """
            SELECT content 
            FROM knowledge_embeddings 
            ORDER BY embedding <=> $1::vector 
            LIMIT 3;
            """,
            query_vector_json
        )
        if not rows:
            return "Контекст відсутній."
        return "\n---\n".join([row['content'] for row in rows])
    except Exception as e:
        print(f"[ПОМИЛКА БД SQL]: {e}")
        return "Помилка при пошуку в базі даних."
    finally:
        await conn.close()

async def answer_with_rag(user_query: str) -> str:
    """Формує відповідь через прямий HTTP запит з обробкою помилок серверов Google"""
    context = await get_top_3_chunks(user_query)
    
    full_prompt = (
        "Ти — асистент бази знань по бензопилах STIHL MS 162 / MS 172.\n"
        "Відповідай на запитання, використовуючи ТІЛЬКИ наданий ТЕХНІЧНИЙ КОНТЕКСТ.\n"
        "Якщо в контексті немає відповіді, дай відповідь строго за цим шаблоном:\n"
        "'Вибачте, але у моїй базі знань немає технічної інформації з цього приводу.'\n\n"
        f"ТЕХНІЧНИЙ КОНТЕКСТ:\n{context}\n\n"
        f"ЗАПИТАННЯ КЛІЄНТА: {user_query}\n\n"
        "ВІДПОВІДЬ:"
    )
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": full_prompt}]
        }],
        "generationConfig": {
            "temperature": 0.2
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=60.0)
            
            # Якщо сервер перевантажений (Помилка 503)
            if response.status_code == 503:
                return "⚠️ Сервер Gemini зараз перевантажений (Помилка 503). Будь ласка, повторіть запит через 10-15 секунд."
                
            if response.status_code != 200:
                return f"⚠️ Помилка сервера Google (Код {response.status_code}). Спробуйте трохи пізніше."
                
            result = response.json()
            
            # Перевіряємо, чи є взагалі відповідь від моделі в JSON
            if "candidates" in result and result["candidates"]:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            elif "error" in result:
                return f"⚠️ Помилка від API: {result['error']['message']}"
            else:
                return "⚠️ Не вдалося отримати коректну відповідь від сервісу. Спробуйте ще раз."
                
    except Exception as e:
        return f"Помилка генерації тексту: {e}"