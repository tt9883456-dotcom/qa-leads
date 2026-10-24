import csv
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import urllib.parse

CSV_FILE = 'leads.csv'

# Фразы, которые мы ищем (как в Shikari.do)
QUERIES = [
    '"ищу qa"', '"нужен тестировщик"', '"аудит сайта"', 
    '"написать бота"', '"автоматизация бизнеса"', '"ищу сео"'
]

# Стоп-слова (чтобы не тащить вакансии)
STOP_WORDS = ["ищу работу", "резюме", "вакансия", "hh.ru", "зарплата"]

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
    if any(stop in text.lower() for stop in STOP_WORDS):
        return
        
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'query', 'text', 'url'])
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([now, query, text[:300].replace('\n', ' '), link])
    existing_urls.add(link)
    print(f"🔥 Найдена заявка по запросу {query}: {link}")

def search_ddg(query):
    print(f"🔍 Ищем: {query}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    data = {'q': query}
    
    try:
        # Отправляем запрос в HTML-версию DuckDuckGo
        r = requests.post("https://html.duckduckgo.com/html/", data=data, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"Ошибка DDG: {r.status_code}")
            return
            
        soup = BeautifulSoup(r.text, 'html.parser')
        results = soup.find_all('a', class_='result__a')
        
        for res in results:
            link = res.get('href')
            text = res.get_text(strip=True)
            # Проверяем, что это не мусорная ссылка
            if link and "duckduckgo" not in link:
                save_lead(query, text, link)
                
    except Exception as e:
        print(f"Сбой DDG {query}: {e}")
        
    time.sleep(2) # Пауза, чтобы поисковик не забанил

if __name__ == "__main__":
    for q in QUERIES:
        search_ddg(q)
    print("Сбор завершен.")
