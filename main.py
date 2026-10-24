import csv
import os
import requests
import feedparser
from datetime import datetime

# Токен VK (добавим в секреты GitHub)
VK_TOKEN = os.environ.get("VK_TOKEN")
CSV_FILE = 'leads.csv'

# Запросы для VK
QUERIES = [
    "ищу qa", "нужен тестировщик", "аудит сайта", "нужен seo", "ищу сео", 
    "написать бота", "автоматизация бизнеса", "нейросети под ключ"
]

# Стоп-слова (чтобы отсеять вакансии)
STOP_WORDS = [
    "ищу работу", "резюме", "вакансия", "куплю курс", "обучение", "зарплата", "ооо", "офис"
]

# RSS-ленты фриланс-заказов (Хабр)
RSS_FEEDS = [
    "https://freelance.habr.com/tasks.rss?q=qa",
    "https://freelance.habr.com/tasks.rss?q=seo",
    "https://freelance.habr.com/tasks.rss?q=аудит"
]

# Загружаем уже сохраненные ссылки, чтобы не дублировать
existing_urls = set()
if os.path.isfile(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) > 3:
                existing_urls.add(row[3])

def is_hot(text):
    text = text.lower()
    return not any(stop in text for stop in STOP_WORDS)

def save_lead(source, text, link):
    if link in existing_urls:
        return
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'source', 'text', 'url'])
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([now, source, text[:500], link])
    existing_urls.add(link)
    print(f"🔥 Найдена заявка: {link}")

def parse_vk():
    if not VK_TOKEN:
        print("VK_TOKEN не найден, пропускаем VK")
        return
    print("Ищем в VK...")
    for q in QUERIES:
        url = "https://api.vk.com/method/newsfeed.search"
        params = {"q": q, "count": 50, "access_token": VK_TOKEN, "v": "5.199"}
        try:
            r = requests.get(url, params=params, timeout=15).json()
            if 'response' not in r:
                print("Ошибка VK API:", r)
                continue
            for item in r['response']['items']:
                if 'text' in item and is_hot(item['text']):
                    link = f"https://vk.com/wall{item['owner_id']}_{item['id']}"
                    save_lead("VK", item['text'], link)
        except Exception as e:
            print(f"Сбой VK {q}: {e}")

def parse_rss():
    print("Ищем в RSS (Хабр)...")
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                text = entry.get('summary', entry.get('title', ''))
                if is_hot(text):
                    save_lead("Habr", text, entry.link)
        except Exception as e:
            print(f"Сбой RSS {feed_url}: {e}")

if __name__ == "__main__":
    parse_vk()
    parse_rss()
    print("Сбор завершен.")
