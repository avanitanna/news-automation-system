import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free")

def get_llm_summary(article: Dict[str, Any], model: Optional[str] = None) -> str:
    """Generate a summary of an article using an LLM via OpenRouter."""
    if not OPENROUTER_API_KEY:
        logger.error("OpenRouter API key not found. Set the OPENROUTER_API_KEY environment variable.")
        return "Summary not available - OpenRouter API key not configured."
    
    if not article.get('content'):
        return "No content available for summarization."
    
    content = article['content']
    title = article.get('title', 'Untitled Article')
    source = article.get('source', 'Unknown Source')
    
    # Truncate content if it's too long (most models have token limits)
    max_chars = 4000
    if len(content) > max_chars:
        content = content[:max_chars] + "..."
    
    # Prepare the prompt
    prompt = f"""
    Article Title: {title}
    Source: {source}
    
    Content:
    {content}
    
    Please provide a concise summary of this article in 3-5 sentences. 
    Extract the most important information, key facts, and main points.
    """
    
    # Prepare the request
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model or DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that summarizes news articles."},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        summary = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not summary:
            logger.warning("Empty summary returned from LLM")
            return "Summary generation failed - empty response."
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting LLM summary: {str(e)}")
        return f"Summary generation failed: {str(e)}"
