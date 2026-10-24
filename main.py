import csv
import os
from datetime import datetime

filename = 'leads.csv'
file_exists = os.path.isfile(filename)

with open(filename, mode='a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(['timestamp', 'source', 'text', 'url'])
    
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    writer.writerow([now, 'Тест', 'Ищу специалиста по аудиту', 'https://example.com'])

print("Данные успешно записаны в leads.csv")
