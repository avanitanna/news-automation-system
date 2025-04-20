from typing import Dict, List, Any, TypedDict
import logging
import asyncio
from langgraph.graph import StateGraph, START, END
from config import MAX_ARTICLES_PER_SOURCE, EMAIL_CONFIG, OPENROUTER_API_KEY, OPENROUTER_MODEL
from news_extraction_async import batch_process_sources, batch_process_articles
from llm_integrations import get_llm_summary
from notifications import send_email_summary

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define state schema
class NewsWorkflowState(TypedDict):
    sources: List[Dict[str, str]]
    articles: List[Dict[str, Any]]
    summaries: List[Dict[str, Any]]
    email_sent: bool
    error: str

# Node functions
async def fetch_articles_async(state: NewsWorkflowState) -> NewsWorkflowState:
    """Node to fetch article links from sources asynchronously."""
    try:
        # Validate sources format
        if not state.get("sources"):
            state["error"] = "No sources provided."
            return state
            
        # Convert sources to proper format if they're strings
        sources_list = []
        for source in state["sources"]:
            if isinstance(source, str):
                # Extract domain name for the source name
                domain = source.split('//')[1].split('/')[0]
                if domain.startswith('www.'):
                    domain = domain[4:]  # Remove www. prefix
                sources_list.append({
                    "name": domain,
                    "url": source
                })
            elif isinstance(source, dict) and 'url' in source:
                sources_list.append(source)
            else:
                state["error"] = f"Invalid source format: {source}"
                return state
        
        # Process all sources in parallel
        articles = await batch_process_sources(sources_list, MAX_ARTICLES_PER_SOURCE)
        state["articles"] = articles
        logger.info(f"Fetched {len(articles)} articles from {len(sources_list)} sources")
        
        # Early error detection if no articles found
        if not articles:
            state["error"] = "No articles found. Check source configurations."
        
    except Exception as e:
        state["error"] = f"Error fetching articles: {str(e)}"
        logger.error(state["error"])
        
    return state

async def extract_content_async(state: NewsWorkflowState) -> NewsWorkflowState:
    """Node to extract content from article URLs asynchronously."""
    if not state["articles"]:
        if not state["error"]:
            state["error"] = "No articles to process"
        return state
        
    try:
        # Process all articles in parallel
        articles_with_content = await batch_process_articles(state["articles"])
        
        # Filter out articles with errors
        valid_articles = [article for article in articles_with_content if not article.get('error')]
        logger.info(f"Extracted content from {len(valid_articles)} articles (out of {len(articles_with_content)} total)")
        
        if not valid_articles and articles_with_content:
            logger.warning("All articles had extraction errors, but continuing workflow")
        
        state["articles"] = articles_with_content  # Keep all articles for error tracking
        
    except Exception as e:
        state["error"] = f"Error extracting content: {str(e)}"
        logger.error(state["error"])
        
    return state

async def summarize_articles_async(state: NewsWorkflowState) -> NewsWorkflowState:
    """Node to summarize articles using LLM."""
    if not state["articles"]:
        return state
        
    try:
        summaries = []
        
        for article in state["articles"]:
            # Skip articles with errors
            if article.get('error'):
                continue
                
            # Generate LLM summary
            summary = get_llm_summary(article)
            article['summary'] = summary
            summaries.append(article)
            
        state["summaries"] = summaries
        logger.info(f"Generated summaries for {len(summaries)} articles")
        
    except Exception as e:
        state["error"] = f"Error summarizing articles: {str(e)}"
        logger.error(state["error"])
        
    return state

def send_notifications(state: NewsWorkflowState) -> NewsWorkflowState:
    """Node to send email notifications with summaries."""
    if not state["summaries"]:
        logger.info("No articles to send")
        return state
        
    try:
        email_sent = send_email_summary(state["summaries"], EMAIL_CONFIG)
        state["email_sent"] = email_sent
        
    except Exception as e:
        state["error"] = f"Error sending notifications: {str(e)}"
        logger.error(state["error"])
        
    return state

# Define decision function
def should_send_email(state: NewsWorkflowState) -> str:
    """Decision function to determine if email should be sent."""
    if state["summaries"]:
        return "has_summaries"
    else:
        return "no_summaries"

def build_async_news_workflow():
    """Build an asynchronous workflow for fetching, analyzing, and summarizing news."""
    # Create the workflow graph
    workflow = StateGraph(state_schema=NewsWorkflowState)
    
    # Add nodes
    workflow.add_node("fetch_articles", fetch_articles_async)
    workflow.add_node("extract_content", extract_content_async)
    workflow.add_node("summarize_articles", summarize_articles_async)
    workflow.add_node("send_notifications", send_notifications)
    
    # Add edges
    workflow.add_edge(START, "fetch_articles")
    workflow.add_edge("fetch_articles", "extract_content")
    workflow.add_edge("extract_content", "summarize_articles")
    
    # Add conditional edge based on whether we have summaries
    workflow.add_conditional_edges(
        "summarize_articles",
        should_send_email,
        {
            "has_summaries": "send_notifications",
            "no_summaries": END
        }
    )
    workflow.add_edge("send_notifications", END)
    
    # Compile the workflow
    return workflow.compile()
