import csv
import os
import nltk
from newspaper import Article
from concurrent.futures import ThreadPoolExecutor, as_completed

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

def summarize_article(row):
    link = row["URL Link"]
    title = row["Article Title"]
    source = row["Source"]
    date = row["Date"]
    category = row["Category"]
    
    try:
        article = Article(link)
        article.download()
        article.parse()
        article.nlp()
        
        # newspaper3k built-in NLP summary
        summary = article.summary
        
        if not summary or len(summary.strip()) < 50:
            # fallback to text snippet if NLP fails
            summary = article.text[:800] + "..."
            
        # Ensure it fits the roughly 150-200 words constraint by trimming
        words = summary.split()
        if len(words) > 200:
            summary = " ".join(words[:180]) + "..."
            
        return {
            "title": title,
            "category": category,
            "summary": summary,
            "citation": f"(Source: {source} | Date: {date} | [Link]({link}))"
        }
    except Exception as e:
        return {
            "title": title,
            "category": category,
            "summary": "Error fetching content. (Requires manual check)",
            "citation": f"(Source: {source} | Date: {date} | [Link]({link}))"
        }

def main():
    input_file = "Filtered_Master_Tracker.csv"
    output_file = "Final_Magazine_Content.md"
    
    articles = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            articles.append(row)
            
    print(f"Summarizing {len(articles)} articles using NLP...")
    
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(summarize_article, row): row for row in articles}
        for i, future in enumerate(as_completed(futures), 1):
            res = future.result()
            results.append(res)
            print(f"Processed {i}/{len(articles)}: {res['title'][:30]}...")

    # Group by category for the magazine structure
    grouped = {}
    for res in results:
        cat = res["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(res)
        
    # Write to Markdown template
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Final Magazine Content Template\n\n")
        f.write("*Ready to be copy-pasted into Canva/InDesign*\n\n")
        
        for category, items in grouped.items():
            f.write(f"## {category}\n\n")
            for item in items:
                f.write(f"### {item['title']}\n\n")
                f.write(f"{item['summary']}\n\n")
                f.write(f"> {item['citation']}\n\n")
                f.write("---\n\n")

    print(f"\nAll content generated and saved to {output_file}!")

if __name__ == "__main__":
    main()
