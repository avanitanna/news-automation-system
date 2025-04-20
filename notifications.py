import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any
from config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_email_body(summaries: List[Dict[str, Any]]) -> str:
    """Format email content with article summaries."""
    body = """
    <html>
    <head>
        <style>
            .article {
                margin-bottom: 20px;
                padding: 10px;
                border-bottom: 1px solid #ccc;
            }
            .title {
                font-weight: bold;
                font-size: 16px;
                color: #222;
            }
            .source {
                color: #666;
                font-style: italic;
            }
            .summary {
                margin-top: 8px;
                line-height: 1.4;
            }
        </style>
    </head>
    <body>
        <h2>Today's News Summaries</h2>
        <p>Here are the news stories from today:</p>
    """
    
    for article in summaries:
        body += f"""
        <div class="article">
            <div class="title">{article.get('title', 'Untitled')}</div>
            <div class="source">Source: {article.get('source_name', 'Unknown')}</div>
            <div class="summary">{article.get('summary', 'No summary available')}</div>
            <a href="{article.get('url', '#')}" target="_blank">Read more</a>
        </div>
        """
    
    body += """
    </body>
    </html>
    """
    
    return body

def send_email(recipient, subject, body, sender=None, password=None, smtp_server=None, smtp_port=None):
    """
    Send an email with the summarized articles
    
    Args:
        recipient: Email recipient
        subject: Email subject
        body: Email body (HTML)
        sender: Sender email (defaults to config)
        password: Sender password (defaults to config)
        smtp_server: SMTP server (defaults to config)
        smtp_port: SMTP port (defaults to config)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Use configuration defaults if not specified
    sender = sender or EMAIL_SENDER
    password = password or EMAIL_PASSWORD
    smtp_server = smtp_server or EMAIL_SMTP_SERVER
    smtp_port = smtp_port or EMAIL_SMTP_PORT
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        # Uncomment for debugging - log instead of sending
        # logging.info(f"Would send email with subject: {subject} to {recipient}")
        # return True
        
        # Actual email sending code
        if smtp_port == 465:
            # SSL connection
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(sender, password)
                server.sendmail(sender, recipient, msg.as_string())
        else:
            # TLS connection
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender, password)
                server.sendmail(sender, recipient, msg.as_string())
        
        logging.info(f"Email sent successfully to {recipient}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

def send_email_summary(summaries: List[Dict[str, Any]], config: Dict[str, Any]) -> bool:
    """Send email with formatted article summaries."""
    try:
        recipient = config['to_email']
        subject = config['subject_template'].format(date=datetime.now().strftime('%Y-%m-%d'))
        body = format_email_body(summaries)
        
        return send_email(recipient, subject, body)
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False
