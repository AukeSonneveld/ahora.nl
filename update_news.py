import json
import os
from backend.scraper import get_latest_news
from backend.translator import translate_article
from datetime import datetime

DATA_FILE = "data/news.json"

def load_existing_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not read existing data ({e}). Starting fresh.")
        return []

def main():
    print(f"--- STARTING NEWS UPDATE: {datetime.now()} ---")
    
    # 1. Load existing articles to check for duplicates
    existing_articles = load_existing_data()
    existing_ids = {article["id"] for article in existing_articles}
    print(f"Loaded {len(existing_articles)} existing articles.")

    # 2. EXTRACT: Scrape the latest news
    print("1. Scraping NOS.nl...")
    # Scrape more candidates (e.g., 20) to ensure we find new ones even if the top 5 haven't changed much
    latest_scraped = get_latest_news(limit=5) 
    
    if not latest_scraped:
        print("No articles found on NOS. Aborting.")
        return

    # 3. FILTER: Keep only new articles
    new_articles_to_process = []
    for article in latest_scraped:
        if article["id"] not in existing_ids:
            new_articles_to_process.append(article)
    
    if not new_articles_to_process:
        print("No new articles found. Database is up to date.")
        return

    print(f"Found {len(new_articles_to_process)} NEW articles to process.")

    # 4. TRANSFORM: Translate only the new articles
    processed_new_articles = []
    
    for index, article in enumerate(new_articles_to_process):
        print(f"   Processing New Article {index + 1}/{len(new_articles_to_process)}: {article['title']}")
        
        # Call our deep translator (paragraph by paragraph)
        translations = translate_article(article['title'], article['original_text'])
        
        # Enrich the article object
        article['title_es'] = translations['title_es']
        article['translations'] = translations
        
        # Optional cleanup of temp key inside translations if present
        if 'title_es' in article['translations']:
            del article['translations']['title_es']

        # Check if there were translation errors. 
        has_error = False
        error_marker = "[Translation Error]"
        for level, text in article['translations'].items():
            if error_marker in text:
                has_error = True
                break
        if has_error:
            print(f"   X Skipping '{article['title']}' due to translation errors.")
            continue # Skip to the next article in the loop, discarding this one
            
        processed_new_articles.append(article)

    # 5. LOAD: Merge and Save
    # We put the NEW articles at the FRONT of the list [New, Old...]
    updated_database = processed_new_articles + existing_articles
    
    # Optional: Keep database size manageable (e.g., keep last 100 articles only)
    # updated_database = updated_database[:100]

    print(f"3. Saving updated database ({len(updated_database)} total articles)...")
    
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_database, f, indent=4, ensure_ascii=False)
        
    print(f"--- SUCCESS: Added {len(processed_new_articles)} new articles. ---")

if __name__ == "__main__":
    main()