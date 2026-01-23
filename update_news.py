import os
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from backend.scraper import get_latest_news
from backend.translator import translate_article

# Database Setup
DB_URI = os.getenv("DB_CONNECTION_STRING")

def get_existing_ids(engine):
    """Fetch all article IDs already in the database to avoid duplicates."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM news_articles"))
        return {row[0] for row in result}

def save_article_to_db(engine, article):
    """Inserts a single article into Postgres."""
    # We use JSONB for translations, so we dump the dict to a string
    stmt = text("""
        INSERT INTO news_articles (id, title, title_es, url, image_url, published_at, original_text, translations)
        VALUES (:id, :title, :title_es, :url, :image_url, :published, :original_text, :translations)
    """)
    
    with engine.connect() as conn:
        conn.execute(stmt, {
            "id": article["id"],
            "title": article["title"],
            "title_es": article.get("title_es"),
            "url": article["url"],
            "image_url": article["image_url"],
            "published": article["published"], # Ensure scraper returns ISO format or datetime object
            "original_text": article["original_text"],
            "translations": json.dumps(article["translations"]) # Convert dict to JSON string
        })
        conn.commit()

def cleanup_old_articles(engine, limit=100):
    """Deletes oldest articles, keeping only the newest 'limit' amount."""
    print(f"--- CLEANUP CHECK (Max {limit}) ---")
    
    # This Query says: "Delete everything that is NOT in the Top 100 newest list"
    stmt = text("""
        DELETE FROM news_articles 
        WHERE id NOT IN (
            SELECT id 
            FROM news_articles 
            ORDER BY published_at DESC 
            LIMIT :limit
        );
    """)
    
    with engine.connect() as conn:
        result = conn.execute(stmt, {"limit": limit})
        conn.commit()
        
        if result.rowcount > 0:
            print(f"  -> Deleted {result.rowcount} old articles to save space.")
        else:
            print("  -> Database size is within limits. No deletion needed.")

def main():
    print(f"--- STARTING SQL UPDATE: {datetime.now()} ---")
    
    if not DB_URI:
        print("ERROR: DB_CONNECTION_STRING is missing.")
        return

    engine = create_engine(DB_URI)
    
    # 1. Check what we already have
    try:
        existing_ids = get_existing_ids(engine)
        print(f"Database currently has {len(existing_ids)} articles.")
    except Exception as e:
        print(f"Database Error: {e}")
        return

    # 2. Scrape
    print("Scraping NOS...")
    latest_scraped = get_latest_news(limit=5)
    
    # 3. Filter New
    new_articles = [a for a in latest_scraped if a["id"] not in existing_ids]
    
    if not new_articles:
        print("No new articles.")
        print("--- UPDATE COMPLETE ---")
        return

    print(f"Found {len(new_articles)} new articles.")

    # 4. Translate & Save (One by One)
    for index, article in enumerate(new_articles):
        print(f"Processing {index+1}/{len(new_articles)}: {article['title']}")
        
        try:
            # Translate
            translations = translate_article(article['title'], article['original_text'])
            
            # Enrich
            article['title_es'] = translations['title_es']
            article['translations'] = translations # This is a dict
            if 'title_es' in article['translations']:
                del article['translations']['title_es']

            # Check for translation errors
            has_error = False
            for level, text in article['translations'].items():
                if "[Translation Error]" in text:
                    has_error = True
                    break
            if has_error:
                print(f"   X Skipping '{article['title']}' due to translation errors.")
                continue # Skip to the next article in the loop, discarding this one

            # Save to DB immediately
            save_article_to_db(engine, article)
            print("  -> Saved to DB")
            
        except Exception as e:
            print(f"  X Failed to process article: {e}")

    # 5. Cleanup at the very end
    cleanup_old_articles(engine, limit=100)

    print("--- UPDATE COMPLETE ---")

if __name__ == "__main__":
    main()