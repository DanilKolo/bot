from clients.gemini import GeminiClient
from repositories.knowledge import KnowledgeRepository
from services.embeddings import EmbeddingService

class RagService:
    def __init__(self, db_session):
        self.embedding_service = EmbeddingService()
        self.knowledge_repo = KnowledgeRepository(db_session)
        self.gemini_client = GeminiClient()

    async def answer_question(self, user_query: str) -> str:
        """Повний цикл RAG: Ембеддінг -> Пошук в БД -> Промпт -> Gemini"""
        
        # 1. Отримуємо вектор для питання користувача (у фоновому потоці)
        query_embedding = await self.embedding_service.get_embedding(user_query)
        
        # 2. Шукаємо найкращий збіг у базі знань з порогом релевантності 0.6
        context = await self.knowledge_repo.find_best_match(query_embedding, threshold=0.6)
        
        # 3. Контроль якості: якщо точної інформації немає — не даємо ШІ вигадувати
        if not context:
            return "На жаль, у моїй базі знань немає точної технічної інформації з цього приводу. Будь ласка, зверніться до офіційного сервісного центру STIHL."

        # 4. Формуємо системний промпт (просимо модель одразу віддавати чистий HTML)
        prompt = f"""
Ти — професійний технічний асистент з обслуговування бензопил STIHL.
Дай відповідь на питання користувача, використовуючи ТІЛЬКИ наданий технічний контекст.

Контекст:
{context}

Питання користувача:
{user_query}

Правила форматування відповіді:
1. Використовуй виключно HTML-теги для оформлення тексту.
2. Для виділення важливих назв, заголовків чи кроків використовуй <b>жирний текст</b>.
3. Списки оформлюй через стандартний знак переліку (•) або цифри.
4. Категорично заборонено використовувати Markdown (зірочки ** або решітки #). Повертай чистий HTML-текст.
"""
        # 5. Викликаємо клієнт ШІ
        return await self.gemini_client.generate_answer(prompt)