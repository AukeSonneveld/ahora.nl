import feedparser
import requests
from bs4 import BeautifulSoup
import time

# Constants
RSS_URL = "https://feeds.nos.nl/nosnieuwsalgemeen"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def fetch_nos_article(url):
    """
    Visits a NOS article and extracts text and image based on the <main> structure.
    """
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # --- 1. Text Extraction ---
        full_text = ""
        
        # The content is inside the <main> tag
        main_content = soup.find('main')
        
        if main_content:
            text_parts = []
            # We grab all paragraphs (<p>) AND subheaders (<h2>)
            # find_all keeps them in the correct order as they appear in the HTML
            for element in main_content.find_all(['p', 'h2']):
                text = element.get_text(strip=True)
                # As soon as we hit "Deel artikel:", we reached the end and stop
                if "Deel artikel:" in text and len(text) == len("Deel artikel:"):
                    break
                text_parts.append(text)

            # The last text_parts could be links to news categories, such as "Binnenland", "Buitenland", etc.
            # We filter these out by removing trailing parts that are likely not part of the article
            while True:
                last_part = text_parts[-1]
                if len(last_part) < 20: # Arbitrary threshold for short non-article texts
                    text_parts.pop()
                else:
                    break

            full_text = "\n\n".join(text_parts)

        # --- 2. Image Extraction ---
        image_url = None
        
        # Based on your snippet, the image is directly inside the <article> tag
        article_tag = soup.find('article')
        if article_tag:
            img_tag = article_tag.find('img')
            if img_tag:
                image_url = img_tag.get('src')

        return full_text, image_url

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None, None

def get_latest_news(limit=10):
    print(f"Fetching RSS feed from {RSS_URL}...")
    feed = feedparser.parse(RSS_URL)
    
    articles = []
    
    # Iterate through entries (up to the limit)
    for entry in feed.entries[:limit]:
        print(f"Processing: {entry.title}")
        
        # 1. Try to get image from RSS enclosure (usually best quality/reliability)
        rss_image = None
        if hasattr(entry, 'enclosures'):
            for enclosure in entry.enclosures:
                if enclosure.type.startswith('image/'):
                    rss_image = enclosure.href
                    break
        
        # 2. Scrape the page content
        body_text, html_image = fetch_nos_article(entry.link)
        
        # Prioritize RSS image, fallback to the one found on the page
        final_image = rss_image if rss_image else html_image

        if body_text:
            article_data = {
                "id": entry.id,
                "title": entry.title,
                "url": entry.link,
                "published": entry.published,
                "image_url": final_image,
                "original_text": body_text,
                # Placeholders for the AI translations we will add next
                "translations": {
                    "A1": "",
                    "A2": "",
                    "B1": "",
                    "B2": "",
                    "C1": "",
                    "C2": ""
                }
            }
            articles.append(article_data)
            time.sleep(0.3) # Short pause to be polite to the server
        else:
            print(f"Skipping: {entry.title} (No text found)")

    return articles

if __name__ == "__main__":
    # Test the scraper immediately
    news = get_latest_news(limit=3)
    print(f"\nSuccessfully scraped {len(news)} articles.")
    if news:
        print(f"\n--- SAMPLE ARTICLE ---")
        print(f"Title: {news[0]['title']}")
        print(f"Image: {news[0]['image_url']}")
        print(f"URL: {news[0]['url']}")
        print(f"Published: {news[0]['published']}")
        print(f"Text Preview:\n{news[0]['original_text'][:300]}...")

        # save original_text to file debug_scraper_output.txt
        with open("debug_scraper_output.txt", "w", encoding="utf-8") as f:
            f.write(news[0]['original_text'])