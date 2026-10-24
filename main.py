import csv
import os
import requests
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup

CSV_FILE = 'leads.csv'

# Каналы с ЖИВЫМИ сообществами (а не биржевые ленты)
CHANNELS = [
    "searchengines",      # Форум вебмастеров (там часто ищут аудит и сео)
    "nocode_ru",          # Сообщество автоматизаторов (боты, парсинг)
    "make_ru",            # Еще одно крупное сообщество по автоматизации
    "startup_ideas_ru",   # Стартапы (ищут QA, разработчиков)
    "webmaster_chat"      # Общий чат вебмастеров
]

# Ключевые слова
KEYWORDS = [
    "ищу", "нужен", "нужна", "аудит", "qa", "тестировщик", 
    "seo", "сео", "бот", "нейросеть", "ии", "автоматизация", "парсинг"
]

# Стоп-слова: отсекаем биржи, вакансии и поиск работы
STOP_WORDS = [
    "ищу работу", "резюме", "вакансия", "куплю курс", 
    "обучение", "зарплата", "офис", "обязанности",
    "kwork", "кворк", "fl.ru", "фриланс", "биржа" # <--- АНТИ-БИРЖЕВОЙ ФИЛЬТР
]

existing_urls = set()
if os.path.isfile(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) > 3:
                existing_urls.add(row[3])

def save_lead(source, text, link):
    if link in existing_urls:
        return
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'source', 'text', 'url'])
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([now, source, text[:300].replace('\n', ' '), link])
    existing_urls.add(link)
    print(f"🔥 Найдена заявка: {link}")

def parse_telegram_web():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for channel in CHANNELS:
        print(f"Сканируем канал: {channel}...")
        url = f"https://t.me/s/{channel}"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200:
                print(f"Ошибка {r.status_code} (возможно канал закрыт). Пропускаем.")
                continue
                
            soup = BeautifulSoup(r.text, 'html.parser')
            messages = soup.find_all('div', class_='tgme_widget_message_wrap')
            
            for msg in messages:
                text_div = msg.find('div', class_='tgme_widget_message_text')
                if not text_div:
                    continue
                    
                text = text_div.get_text(separator=' ', strip=True)
                text_lower = text.lower()
                
                # Проверяем стоп-слова (включая кворк)
                if any(stop in text_lower for stop in STOP_WORDS):
                    continue
                    
                # Ищем ключевые слова
                if any(re.search(r'\b' + re.escape(kw) + r'\b', text_lower) for kw in KEYWORDS):
                    link_tag = msg.find('a', class_='tgme_widget_message_date')
                    if link_tag:
                        link = link_tag['href']
                        save_lead(f"TG @{channel}", text, link)
                        
        except Exception as e:
            print(f"Сбой канала {channel}: {e}")
            
        time.sleep(3)

if __name__ == "__main__":
    parse_telegram_web()
    print("Сбор завершен.")
