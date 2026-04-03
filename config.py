import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "intelligence.db")

# Search provider: "mock", "serp", "news"
SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "mock")

# SerpAPI
SERP_API_KEY = os.getenv("SERP_API_KEY", "")

# NewsAPI
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# Search settings
SEARCH_RESULTS_PER_QUERY = int(os.getenv("SEARCH_RESULTS_PER_QUERY", "10"))
SEARCH_DELAY_SECONDS = float(os.getenv("SEARCH_DELAY_SECONDS", "1.0"))

# Upload settings
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")

# Flask
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
