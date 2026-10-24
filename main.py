import csv
import os
import requests
import feedparser
import time
from datetime import datetime
from bs4 import BeautifulSoup

CSV_FILE = 'leads.csv'

SUBREDDITS = ["forhire", "QualityAssurance", "cybersecurity", "webdev", "artificial", "OpenAI"]

# Ключевые слова под ВСЕ твои услуги: QA, SEO, Аудит безопасности, Боты, ИИ-сотрудники
KEYWORDS = [
    "qa", "seo", "audit", 
    "bot", "chatbot", "automation", 
    "pentest", "vulnerability", "security audit", 
    "ai", "gpt", "llm", "agent", "assistant", "parser",
    "нейросеть"
]

# Стоп-слова: отсекаем вакансии на полный день и сисадминов
STOP_WORDS = [
    "senior", "lead", "manager", "director", "full-time", "full time", 
    "clearance", "years of experience", "administrator"
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
    print(f"Найдена заявка: {link}")

def parse_reddit():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for sub in SUBREDDITS:
        print(f"Сканируем r/{sub}...")
        url = f"https://www.reddit.com/r/{sub}/new/.rss"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200:
                print(f"Ошибка {r.status_code}. Пропускаем.")
                continue
                
            feed = feedparser.parse(r.text)
            for entry in feed.entries:
                title = entry.get('title', '')
                link = entry.get('link', '')
                
                # Отсекаем фрилансеров, которые предлагают себя
                if "[hiring]" not in title.lower() and "[for hire]" in title.lower():
                    continue
                    
                raw_summary = entry.get('summary', '')
                soup = BeautifulSoup(raw_summary, 'html.parser')
                clean_text = soup.get_text(separator=' ').lower()
                full_text = f"{title.lower()} {clean_text}"
                
                # Проверяем стоп-слова (если есть сисадмин или сеньор — пропускаем)
                if any(stop in full_text for stop in STOP_WORDS):
                    continue
                
                # Ищем наши ключевые слова (QA, SEO, Аудит, Боты, ИИ)
                if any(kw in full_text for kw in KEYWORDS):
                    save_lead(f"Reddit r/{sub}", title, link)
                    
        except Exception as e:
            print(f"Сбой r/{sub}: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    parse_reddit()
    print("Сбор завершен.")
