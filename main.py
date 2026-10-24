import csv
import os
import requests
import feedparser
import time
from datetime import datetime
from bs4 import BeautifulSoup

CSV_FILE = 'leads.csv'

# Сабреддиты для проверки
SUBREDDITS = ["forhire", "QualityAssurance", "cybersecurity", "webdev"]
# Ключевые слова (QA, SEO, аудит, боты, безопасность)
KEYWORDS = ["qa", "seo", "audit", "bot", "automation", "pentest", "vulnerability", "security"]

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

def parse_reddit():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
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
                
                # 1. Отсекаем фрилансеров (ищем только [Hiring])
                if "[hiring]" not in title.lower() and "[for hire]" in title.lower():
                    continue
                    
                # 2. Чистим HTML из тела поста
                raw_summary = entry.get('summary', '')
                soup = BeautifulSoup(raw_summary, 'html.parser')
                clean_text = soup.get_text(separator=' ').lower()
                
                # 3. Ищем ключевые слова
                if any(kw in clean_text or kw in title.lower() for kw in KEYWORDS):
                    save_lead(f"Reddit r/{sub}", title, link)
                    
        except Exception as e:
            print(f"Сбой r/{sub}: {e}")
            
        time.sleep(5) # Пауза 5 секунд, чтобы Reddit не забанил

if __name__ == "__main__":
    parse_reddit()
    print("Сбор завершен.")
