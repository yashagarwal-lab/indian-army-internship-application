import csv
from collections import Counter

def process_tracker():
    input_file = "Master_Tracker.csv"
    output_file = "Filtered_Master_Tracker.csv"
    
    # User's required allocations
    # Assuming 2 articles per page
    allocations = {
        "Security & Strategic Affairs": 18, # 9 pages
        "Regional News": 16, # 8 pages (We'll map leftovers to this if needed)
        "Development": 16, # 8 pages
        "Society & Youth": 16, # 8 pages
        "Sports & Achievements": 16 # 8 pages
    }
    
    articles_by_category = {k: [] for k in allocations.keys()}
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row["Date"]
            # Phase 6 Strict Date Check: Must be >= 2026-09-01 and <= 2026-10-03
            if "2026-09-01" <= date <= "2026-10-03":
                cat = row["Category"]
                if cat in articles_by_category:
                    articles_by_category[cat].append(row)
                else:
                    # Map any unknown to Regional News
                    articles_by_category["Regional News"].append(row)
                    
    # Select the exact number of articles per category
    final_selection = []
    for cat, needed in allocations.items():
        available = articles_by_category[cat]
        # if we don't have enough in a category, we take all we have
        selected = available[:needed]
        final_selection.extend(selected)
        print(f"Category '{cat}': Target {needed}, Found/Selected {len(selected)}")
        
    # Sort final selection by Date descending
    final_selection.sort(key=lambda x: x["Date"], reverse=True)
    
    # Save the filtered CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["S.No", "Article Title", "Date", "Category", "Source", "URL Link", "Reasoning for Selection"])
        writer.writeheader()
        for i, row in enumerate(final_selection, 1):
            row["S.No"] = i
            writer.writerow(row)
            
    # --- Generate Appendix 1 ---
    sources = [row["Source"] for row in final_selection]
    source_counts = Counter(sources)
    
    with open("Appendix_1_Sources.md", "w", encoding='utf-8') as f:
        f.write("# Appendix 1: Sources & Count\n\n")
        f.write("| Publication | Article Count |\n")
        f.write("|-------------|---------------|\n")
        for source, count in source_counts.most_common():
            f.write(f"| {source} | {count} |\n")
            
    # --- Generate Appendix 2 ---
    with open("Appendix_2_Reasoning.md", "w", encoding='utf-8') as f:
        f.write("# Appendix 2: Reasoning for Selection\n\n")
        f.write("| Article Title | Reasoning for Selection |\n")
        f.write("|---------------|-------------------------|\n")
        for row in final_selection:
            title = row["Article Title"].replace("|", "-") # avoid markdown table breaking
            reason = row["Reasoning for Selection"].replace("|", "-")
            f.write(f"| {title} | {reason} |\n")
            
    print(f"\nSuccessfully selected {len(final_selection)} articles.")
    print("Generated Filtered_Master_Tracker.csv, Appendix_1_Sources.md, and Appendix_2_Reasoning.md")

if __name__ == "__main__":
    process_tracker()
