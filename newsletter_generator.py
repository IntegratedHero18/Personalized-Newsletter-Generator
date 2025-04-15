import feedparser
from collections import defaultdict
from datetime import datetime
from dateutil import parser
import re
import os
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

def fetch_rss_feeds(feed_urls):
    """Fetch and parse RSS feeds with error handling"""
    articles = []
    for url in feed_urls:
        try:
            feed = feedparser.parse(url)
            if feed.bozo:  # Check for feed parsing errors
                print(f"Error parsing {url}: {feed.bozo_exception}")
                continue
                
            for entry in feed.entries:
                try:
                    pub_date = (
                        parser.parse(str(entry.published), ignoretz=True) 
                        if 'published' in entry and entry.published 
                        else datetime.min
                    )
                except (ValueError, TypeError):
                    pub_date = datetime.min
                    
                article = {
                    'title': entry.title,
                    'link': entry.link,
                    'summary': entry.summary if 'summary' in entry else '',
                    'published': entry.published if 'published' in entry else '',
                    'source': url,
                    'pub_date': pub_date  # Now guaranteed to be timezone-naive
                }
                articles.append(article)
        except Exception as e:
            print(f"Failed to fetch {url}: {str(e)}")
    return articles

# User profiles with interests and preferred sources
user_profiles = {
    "Alex Parker": {
        "interests": ["AI", "cybersecurity", "blockchain", "startups", "programming"],
        "sources": ["TechCrunch", "Wired", "MIT Technology Review", "Ars Technica"]
    },
    "Priya Sharma": {
        "interests": ["Global markets", "startups", "fintech", "cryptocurrency", "economics"],
        "sources": ["Bloomberg", "Financial Times", "Forbes", "CoinDesk"]
    },
    "Marco Rossi": {
        "interests": ["Football", "F1", "NBA", "Olympic sports", "esports"],
        "sources": ["ESPN", "BBC Sport", "Sky Sports", "The Athletic"]
    },
    "Lisa Thompson": {
        "interests": ["Movies", "celebrity news", "TV shows", "music", "books"],
        "sources": ["Variety", "Rolling Stone", "Billboard", "Hollywood Reporter"]
    },
    "David Martinez": {
        "interests": ["Space exploration", "AI", "biotech", "physics", "renewable energy"],
        "sources": ["NASA", "Science Daily", "Nature", "Ars Technica Science"]
    }
}

def categorize_article(article, user_interests):
    """Categorize articles based on user interests"""
    title = article['title'].lower()
    summary = article['summary'].lower()
    
    matches = []
    for interest in user_interests:
        if interest.lower() in title or interest.lower() in summary:
            matches.append(interest)
    
    return matches

def filter_articles_for_user(articles, user_profile):
    filtered = []
    seen_titles = set()
    
    for article in articles:
        if article['title'] in seen_titles:
            continue
        seen_titles.add(article['title'])
        
        source_match = any(src.lower() in article['source'].lower() for src in user_profile['sources'])
        interest_matches = categorize_article(article, user_profile['interests'])
        
        if source_match or interest_matches:
            article['categories'] = interest_matches
            filtered.append(article)
    
    # Now safe to sort since all dates are timezone-naive
    filtered.sort(key=lambda x: x['pub_date'], reverse=True)
    return filtered

def generate_newsletter(user_name, articles):
    """Generate markdown formatted newsletter"""
    markdown_content = f"# Personalized Newsletter for {user_name}\n"
    markdown_content += f"## {datetime.now().strftime('%B %d, %Y')}\n\n"
    
    # Group articles by category
    categorized = defaultdict(list)
    for article in articles:
        if article['categories']:
            for cat in article['categories']:
                categorized[cat].append(article)
        else:
            categorized['General'].append(article)
    
    # Top Stories section (3 most recent)
    markdown_content += "## Top Stories\n"
    for article in articles[:3]:
        markdown_content += f"- [{article['title']}]({article['link']})\n"
    markdown_content += "\n"
    
    # Categorized content
    for category, cat_articles in categorized.items():
        markdown_content += f"## {category}\n"
        for article in cat_articles:
            markdown_content += f"### {article['title']}\n"
            summary = re.sub('<[^<]+?>', '', article['summary'])  # Remove HTML tags
            markdown_content += f"{summary[:200]}... [Read more]({article['link']})\n\n"
    
    return markdown_content

def main():
    """Main execution function"""
    # Define all RSS feeds
    rss_feeds = [
        # General News
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "http://feeds.reuters.com/reuters/topNews",
        
        # Technology
        "http://feeds.feedburner.com/TechCrunch/",
        "https://www.wired.com/feed/rss",
        "https://www.technologyreview.com/feed/",
        
        # Finance
        "https://www.bloomberg.com/feeds/bnews/siteindex.rss",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://www.ft.com/?format=rss",
        
        # Sports
        "http://www.espn.com/espn/rss/news",
        "http://feeds.bbci.co.uk/sport/rss.xml",
        "https://www.skysports.com/rss/12040",
        
        # Entertainment
        "https://variety.com/feed/",
        "https://www.hollywoodreporter.com/feed/",
        "https://www.billboard.com/feed/rss/",
        
        # Science
        "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "https://www.sciencedaily.com/rss/all.xml",
        "http://feeds.arstechnica.com/arstechnica/science/"
    ]
    
    print("Fetching articles from RSS feeds...")
    articles = fetch_rss_feeds(rss_feeds)
    
    print("Generating newsletters...")
    for user_name, profile in user_profiles.items():
        user_articles = filter_articles_for_user(articles, profile)
        if not user_articles:
            print(f"No articles found for {user_name}")
            continue
            
        newsletter = generate_newsletter(user_name, user_articles)
        
        # Save to file
        filename = f"sample_output/{user_name.replace(' ', '_')}_Newsletter_{datetime.now().strftime('%Y%m%d')}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(newsletter)
        print(f"Generated newsletter for {user_name} in {filename}")

if __name__ == "__main__":
    main()