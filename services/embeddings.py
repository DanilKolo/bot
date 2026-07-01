import logging
from sklearn.feature_extraction.text import TfidfVectorizer
import os

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        # Використовуємо стабільний локальний TF-IDF векторизатор
        self.vectorizer = TfidfVectorizer()
        self.is_fitted = False
        self._fit_on_knowledge_base()

    def _fit_on_knowledge_base(self):
        """Навчаємо векторизатор на нашому тексті, щоб він розумів слова"""
        file_path = "knowledge_base.txt"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                text_data = f.read()
            chunks = [chunk.strip() for chunk in text_data.split("=== ") if chunk.strip()]
            if chunks:
                self.vectorizer.fit(chunks)
                self.is_fitted = True

    async def get_embedding(self, text: str) -> list[float]:
        """Локально перетворює текст на вектор без запитів до інтернету чи DLL"""
        try:
            if not self.is_fitted:
                # Резервний випадок, якщо файл не прочитався відразу
                return [0.0] * 100
                
            # Рахуємо вагу слів локально
            matrix = self.vectorizer.transform([text])
            vector = matrix.toarray()[0]
            return vector.tolist()
        except Exception as e:
            logger.error(f"Помилка локального ембеддінгу: {e}")
            return [0.0] * 100