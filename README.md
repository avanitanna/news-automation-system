### News Automation System
A LangGraph and Deepseek powered application that automatically fetches news from configured sources, extracts content, summarizes articles using AI, and delivers concise summaries to your email inbox. 

### 📋 Overview
This project creates an autonomous workflow that:

- Browses multiple news sources in parallel
- Extracts article content
- Generates concise summaries using Deepseek LLM via OpenRouter
- Delivers a formatted digest to your email

The system is built with asynchronous processing (see `async` LangGraph nodes) to efficiently handle multiple sources and articles, making it suitable for daily news briefings. Fetching and processing multiple news sources simultaneously contributes to speed and resource improvements as well as adds resilience to failures/ timeouts. 

Note that this is not a strictly "agentic" system where an LLM makes autonomous decisions about the workflow path -- it is rather a directed workflow with a predetermined decision logic where we have an orchestrated pipeline using LangGraph and Deepseek LLM via OpenRouter for summarization. For example, if we were to let the LLM decide what to do next based on the current state or have the LLM reflect on its performance to improve future runs, we could transform this into an agent. 

### 🚀 Features
- Fetches and processes multiple news sources simultaneously (thanks to LangGraph `async` nodes)
- Uses BeautifulSoup to extract meaningful content from articles
- Leverages Deepseek LLM via OpenRouter to create high-quality summaries
- Formatted HTML email with article summaries and source links
- Runs in a Docker container for easy deployment (note that this is also a more secure way to run such workflows)
- Easily customize news sources and email settings

### 🛠️ Installation
- Docker 
- Python
- OpenRouter API key
- Email account for sending summaries

#### Steps
- Clone the repository
- Create a `.env` files with your configuration
- Build and run the docker container. For example,
```
docker build -t news-agent .
docker run -it --rm news-agent
```

### Workflow architecture 
The application uses LangGraph to define a directed workflow:

- `fetch_articles_async`: Fetches article links from configured news sources
- `extract_content_async`: Extracts and processes article content
- `summarize_articles_async`: Generates AI summaries using OpenRouter
- `send_notifications`: Sends email with formatted summaries

The workflow makes decisions based on the state (e.g., only send email if summaries exist). 

### Schedule your news summmary 
You can schedule a news summary to be sent daily!

### Some useful tips
- Keep your `.env` file secure and do not commit it
- Use docker 