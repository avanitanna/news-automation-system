"""Asynchronous news extraction functions."""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import random
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Common user agents for avoiding bot detection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
]

async def fetch_with_retry(session, url, max_retries=3, headers=None):
    for attempt in range(1, max_retries + 1):
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logging.warning(f"Attempt {attempt}/{max_retries} failed for {url}: {response.status}, message='{response.reason}', url='{url}'")
        except Exception as e:
            logging.error(f"Attempt {attempt}/{max_retries} failed for {url}: {e}")
    return None

def extract_article_links(soup, base_url):
    """Extract article links from the soup object"""
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Convert relative URLs to absolute
        if href.startswith('/'):
            if base_url.endswith('/'):
                href = base_url + href[1:]
            else:
                href = base_url + href
        # Filter for likely article URLs
        if href.startswith('http') and '/article' in href or '/news/' in href or '/story/' in href:
            if href not in links:
                links.append(href)
    return links

def extract_title(soup):
    """Extract article title from soup"""
    if title_tag := soup.find('h1'):
        return title_tag.get_text().strip()
    if title_meta := soup.find('meta', property='og:title'):
        return title_meta.get('content', '').strip()
    return None

async def fetch_articles(sources, max_articles_per_source=2):
    articles = []
    async with aiohttp.ClientSession() as session:
        for source_url in sources:
            source_name = source_url.split('//')[1].split('/')[0].replace('www.', '')
            try:
                html = await fetch_with_retry(session, source_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                if html:
                    soup = BeautifulSoup(html, 'html.parser')
                    links = extract_article_links(soup, source_url)
                    
                    for i, link in enumerate(links[:max_articles_per_source]):
                        try:
                            article_html = await fetch_with_retry(session, link, headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                            })
                            if article_html:
                                article_soup = BeautifulSoup(article_html, 'html.parser')
                                title = extract_title(article_soup)
                                if title:
                                    articles.append({
                                        'url': link,
                                        'title': title,
                                        'html': article_html,
                                        'source': source_name
                                    })
                        except Exception as e:
                            logging.error(f"Error fetching article {link}: {e}")
            except Exception as e:
                logging.error(f"Error fetching source {source_url}: {e}")
    
    return articles

async def batch_process_sources(sources: List[Dict[str, str]], max_per_source: int) -> List[Dict[str, Any]]:
    """
    Process multiple sources in parallel to extract article links.
    
    Args:
        sources: List of source dictionaries with 'name' and 'url' keys
        max_per_source: Maximum number of articles per source
        
    Returns:
        List of article dictionaries
    """
    source_urls = [source['url'] for source in sources]
    articles = await fetch_articles(source_urls, max_per_source)
    
    # Update source names if needed
    for article in articles:
        for source in sources:
            if article['source'] in source['url']:
                article['source'] = source['name']
                break
                
    logger.info(f"Processed {len(sources)} sources, found {len(articles)} articles")
    return articles

async def extract_article_content(session: aiohttp.ClientSession, article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract content from a single article that already has HTML.
    
    Args:
        session: aiohttp ClientSession
        article: Article dictionary with 'html' key
        
    Returns:
        Article dictionary with added 'content' key
    """
    result = article.copy()
    
    try:
        if not article.get('html'):
            html = await fetch_with_retry(session, article['url'], headers={
                'User-Agent': random.choice(USER_AGENTS)
            })
            if not html:
                result['error'] = "Failed to fetch article content"
                return result
        else:
            html = article['html']
            
        # Parse the HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
            
        # Extract paragraphs
        paragraphs = soup.find_all('p')
        content = ' '.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
        
        # Clean up whitespace
        content = ' '.join(content.split())
        
        if not content or len(content) < 50:
            result['error'] = "Insufficient content extracted"
            return result
            
        result['content'] = content
        
    except Exception as e:
        result['error'] = f"Error extracting content: {str(e)}"
        
    return result

async def batch_process_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process multiple articles in parallel to extract content.
    
    Args:
        articles: List of article dictionaries
        
    Returns:
        List of article dictionaries with added 'content' or 'error' keys
    """
    processed_articles = []
    
    async with aiohttp.ClientSession() as session:
        tasks = [extract_article_content(session, article) for article in articles]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in article processing: {result}")
                continue
                
            processed_articles.append(result)
    
    logger.info(f"Processed {len(processed_articles)} articles with content")
    return processed_articles