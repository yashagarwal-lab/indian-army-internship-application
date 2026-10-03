import requests
import xml.etree.ElementTree as ET
import csv
from datetime import datetime
import time
import os

queries = [
    "Indian Army governance Northeast",
    "Indian Army state collaborations Northeast",
    "Indian Army civil administration Northeast",
    "Indian Army internal security Northeast",
    "Indian Army youth engagement Northeast",
    "Indian Army education initiatives Northeast",
    "Indian Army women empowerment Northeast",
    "Indian Army employment Northeast"
]

def fetch_news(query, after_date="2026-09-01", before_date="2026-10-04"):
    encoded_query = f"{query} after:{after_date} before:{before_date}".replace(' ', '+')
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
    
    root = ET.fromstring(response.text)
    articles = []
    for item in root.findall('./channel/item'):
        title = item.find('title').text
        link = item.find('link').text
        pub_date = item.find('pubDate').text
        source = item.find('source').text
        
        try:
            dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
            formatted_date = dt.strftime("%Y-%m-%d")
        except:
            formatted_date = pub_date

        if "youth" in query.lower() or "education" in query.lower() or "women" in query.lower() or "employment" in query.lower():
            category = "Society & Youth"
        else:
            category = "Regional News"

        articles.append({
            "Article Title": title,
            "Date": formatted_date,
            "Category": category,
            "Source": source,
            "URL Link": link,
            "Reasoning for Selection": f"Relevant to {category} theme, highlighting {query}."
        })
    return articles

def main():
    existing_links = set()
    csv_file = "Master_Tracker.csv"
    
    # Read existing links
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_links.add(row["URL Link"])

    new_articles = []
    
    for query in queries:
        print(f"Fetching: {query}")
        articles = fetch_news(query)
        for article in articles:
            if article["URL Link"] not in existing_links:
                existing_links.add(article["URL Link"])
                new_articles.append(article)
        time.sleep(1)
        
    if new_articles:
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["S.No", "Article Title", "Date", "Category", "Source", "URL Link", "Reasoning for Selection"])
            for article in new_articles:
                # S.No will be updated by process_tracker anyway
                row = {"S.No": 0}
                row.update(article)
                writer.writerow(row)
                
    print(f"Appended {len(new_articles)} new articles.")

if __name__ == "__main__":
    main()
