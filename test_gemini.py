import os
from dotenv import load_dotenv
import google.generativeai as genai

# Завантажуємо .env
load_dotenv()

key = os.getenv("GEMINI_API_KEY")
print(f"Зчитаний ключ: {key[:10]}... (всього символів: {len(key) if key else 0})")

genai.configure(api_key=key)

print("\n--- Список доступних моделей для твого ключа ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Доступно: {m.name}")
except Exception as e:
    print(f"Помилка отримання списку моделей: {e}")