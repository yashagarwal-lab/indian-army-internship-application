import requests
import xml.etree.ElementTree as ET
import csv
from datetime import datetime
import time

# Keywords for different sections
queries = [
    "Indian Army Northeast",
    "Border Roads Organisation Northeast",
    "Assam Rifles sports",
    "Indian Army counter-insurgency Northeast",
    "Indian Army peace accords Northeast",
    "BRO projects Northeast",
    "Indian Army vibrant villages",
    "Army goodwill schools Northeast",
    "Operation Sadbhavana Northeast",
    "NCC camps Northeast",
    "Durand Cup Northeast"
]

def fetch_news(query, after_date="2026-09-01", before_date="2026-10-04"):
    """Fetch news from Google News RSS."""
    encoded_query = f"{query} after:{after_date} before:{before_date}".replace(' ', '+')
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch {url}")
        return []

    root = ET.fromstring(response.text)
    
    articles = []
    for item in root.findall('./channel/item'):
        title = item.find('title').text
        link = item.find('link').text
        pub_date = item.find('pubDate').text
        source = item.find('source').text
        
        # Convert pubDate to a standard format
        try:
            # Example: Thu, 10 Sep 2026 12:00:00 GMT
            dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
            formatted_date = dt.strftime("%Y-%m-%d")
        except:
            formatted_date = pub_date

        # Determine category based on query
        if "sports" in query.lower() or "durand" in query.lower():
            category = "Sports & Achievements"
        elif "goodwill" in query.lower() or "sadbhavana" in query.lower() or "ncc" in query.lower():
            category = "Society & Youth"
        elif "bro" in query.lower() or "vibrant" in query.lower() or "infrastructure" in query.lower():
            category = "Development"
        else:
            category = "Security & Strategic Affairs"

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
    all_articles = []
    seen_links = set()
    
    print("Scraping articles... this may take a moment.")
    
    for query in queries:
        print(f"Fetching: {query}")
        articles = fetch_news(query)
        for article in articles:
            if article["URL Link"] not in seen_links:
                seen_links.add(article["URL Link"])
                all_articles.append(article)
        time.sleep(1) # Be polite
        
    # Sort by date (descending)
    all_articles.sort(key=lambda x: x["Date"], reverse=True)
    
    print(f"\nFound {len(all_articles)} unique articles.")
    
    # Save to CSV
    csv_file = "Master_Tracker.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["S.No", "Article Title", "Date", "Category", "Source", "URL Link", "Reasoning for Selection"])
        writer.writeheader()
        
        for i, article in enumerate(all_articles, 1):
            row = {"S.No": i}
            row.update(article)
            writer.writerow(row)
            
    print(f"Data saved to {csv_file}. You can open this in Excel or Google Sheets.")

if __name__ == "__main__":
    main()
