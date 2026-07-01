import google.generativeai as genai
import logging
import asyncio
from config import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        # Конфігуруємо API ключем з конфігу
        genai.configure(api_key=settings.GEMINI_API_KEY)

    async def generate_answer(self, prompt: str) -> str:
        """Надсилає промпт до актуальних моделей Gemini нового покоління"""
        
        # Використовуємо моделі строго з твого списку доступних
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-3.5-flash"
        ]
        
        last_error = None
        
        for model_name in models_to_try:
            try:
                # Ініціалізуємо актуальну модель
                model_instance = genai.GenerativeModel(model_name)
                
                # Запускаємо генерацію тексту у фоновому потоці
                response = await asyncio.to_thread(model_instance.generate_content, prompt)
                
                if response and response.text:
                    return response.text
                    
            except Exception as e:
                last_error = e
                logger.warning(f"[Gemini Клієнт] Модель {model_name} видала помилку, пробуємо наступну...")
                continue
                
        logger.error(f"Критична помилка: жодна модель з нового пулу не відповіла. Остання: {last_error}", exc_info=True)
        return "Вибачте, виникла технічна помилка при генерації відповіді ШІ."