import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Maximum articles to process per source
MAX_ARTICLES_PER_SOURCE = int(os.getenv("MAX_ARTICLES_PER_SOURCE", "2"))

EMAIL_SENDER=os.getenv("EMAIL_SENDER", "your-email@gmail.com")
EMAIL_PASSWORD= os.getenv("EMAIL_PASSWORD", "your-app-password")
EMAIL_RECEIVER=os.getenv("EMAIL_RECEIVER", "recipient@example.com")
EMAIL_SMTP_SERVER=os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT=int(os.getenv("EMAIL_SMTP_PORT", "587"))

# Email configuration from environment variables
EMAIL_CONFIG = {
    "smtp_server": EMAIL_SMTP_SERVER,
    "smtp_port": EMAIL_SMTP_PORT,
    "smtp_username": EMAIL_SENDER,
    "smtp_password":EMAIL_PASSWORD,
    "from_email": EMAIL_SENDER,
    "to_email": EMAIL_RECEIVER,
    "subject_template": os.getenv("EMAIL_SUBJECT", "Daily News Summary - {date}")
}

# News sources configuration
NEWS_SOURCES = [
    "https://www.theverge.com",
    "https://techcrunch.com",
    "https://news.ycombinator.com",
    "https://www.wired.com"
]

# LLM Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free")

# Browser Configuration
HEADLESS = os.getenv("HEADLESS", "True").lower() == "true"
