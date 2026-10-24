import csv
import os
import requests
import time
from datetime import datetime

# Берем токен из секретов GitHub
VK_TOKEN = os.environ.get("VK_TOKEN")
if not VK_TOKEN:
    print("Ошибка: нет VK_TOKEN в переменных окружения!")
    exit(1)

CSV_FILE = 'leads.csv'
VERSION = '5.199'

# Расширенный список запросов (QA, SEO, Аудит, Боты, ИИ)
QUERIES = [
    "ищу qa", "нужен тестировщик", "тестирование сайта", "аудит кода", "проверить сайт",
    "ищу сео", "нужен seo", "продвижение сайта", "аудит сайта", "оптимизация сайта",
    "написать бота", "нужен бот", "чат бот", "телеграм бот", "парсинг сайта",
    "нейросеть", "внедрение ии", "ии сотрудник", "автоматизация бизнеса", "gpt",
    "пентест", "аудит безопасности", "уязвимости сайта", "проверка на взлом"
]

# Стоп-слова: чтобы не тащить вакансии и тех, кто ищет работу
STOP_WORDS = [
    "ищу работу", "резюме", "вакансия", "куплю курс", 
    "обучение", "зарплата", "офис", "обязанности", "требования"
]

existing_urls = set()
if os.path.isfile(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) > 3:
                existing_urls.add(row[3])

def save_lead(query, text, link):
    if link in existing_urls:
        return
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'source', 'text', 'url'])
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([now, f"VK ({query})", text[:500].replace('\n', ' '), link])
    existing_urls.add(link)
    print(f"🔥 Найдена заявка по '{query}': {link}")

def parse_vk():
    url = "https://api.vk.com/method/newsfeed.search"
    for q in QUERIES:
        print(f"Сканируем VK по запросу: {q}...")
        params = {
            "q": q,
            "count": 50,
            "access_token": VK_TOKEN,
            "v": VERSION
        }
        try:
            r = requests.get(url, params=params, timeout=15)
            data = r.json()
            
            # Если VK вернул ошибку (например, Flood control)
            if 'error' in data:
                print(f"Ошибка VK API: {data['error'].get('error_msg')}")
                print("Ждем 30 секунд из-за ошибки...")
                time.sleep(30)
                continue
                
            items = data.get('response', {}).get('items', [])
            found = 0
            for item in items:
                text = item.get('text', '')
                if not text:
                    continue
                
                text_lower = text.lower()
                # Проверяем стоп-слова (если это вакансия или резюме — пропускаем)
                if any(stop in text_lower for stop in STOP_WORDS):
                    continue
                
                # Собираем ссылку на пост
                link = f"https://vk.com/wall{item.get('owner_id')}_{item.get('id')}"
                save_lead(q, text, link)
                found += 1
            
            print(f"  -> Найдено постов по '{q}': {found}")
            
        except Exception as e:
            print(f"Сбой VK по '{q}': {e}")
        
        # Пауза 15 секунд, чтобы VK не забанил за частые запросы
        print("Пауза 15 секунд...")
        time.sleep(15)

if __name__ == "__main__":
    parse_vk()
    print("Сбор завершен.")
