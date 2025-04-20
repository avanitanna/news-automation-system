"""Run the asynchronous news workflow."""

import asyncio
from news_workflow import build_async_news_workflow
from config import NEWS_SOURCES, EMAIL_RECEIVER
from notifications import send_email
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main_async():
    """Run the async news workflow."""
    print("Starting Asynchronous News Workflow")
    
    # Initialize state
    initial_state = {
        "sources": NEWS_SOURCES,
        "articles": [],
        "summaries": [],
        "email_sent": False,
        "error": ""
    }
    
    # Build workflow
    workflow = build_async_news_workflow()
    
    # Execute workflow
    print("Executing workflow...")
    result = await workflow.ainvoke(initial_state)
    
    # Check results
    print("\nWorkflow completed!")
    print(f"Articles processed: {len(result['articles'])}")
    print(f"Important summaries: {len(result['summaries'])}")
    
    if result["error"]:
        print(f"Error: {result['error']}")
    else:
        print("Workflow completed successfully.")
    
    # Display summaries
    if result["summaries"]:
        print("\n=== ARTICLE SUMMARIES ===")
        for i, article in enumerate(result["summaries"], 1):
            source = article.get('source', 'Unknown Source')
            title = article.get('title', 'No Title')
            print(f"\n{i}. {title} ({source})")
            print(f"   URL: {article.get('url', 'No URL')}")
            print(f"\n   Summary: {article.get('summary', 'No summary available')}")
    else:
        print("\nNo important articles found for summarization.")
    
    # Email status from workflow result
    if result["email_sent"]:
        print("\nEmail was sent by the workflow.")
    elif result["summaries"]:
        print("\nWarning: Workflow has summaries but email wasn't sent.")

    return result

if __name__ == "__main__":
    asyncio.run(main_async())
