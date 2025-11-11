"""
Configuration management for data ingestion modules
"""
import os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv('config/.env')


class Config:
    """Configuration class for data ingestion"""

    # Twitter Configuration
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', '')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET', '')
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN', '')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', '')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', '')

    # Reddit Configuration
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID', '')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET', '')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'AI_Trend_Monitor/1.0')

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC_RAW = os.getenv('KAFKA_TOPIC_RAW', 'ai-social-raw')

    # Collection Configuration
    COLLECTION_INTERVAL_SECONDS = int(os.getenv('COLLECTION_INTERVAL_SECONDS', '300'))
    MAX_TWEETS_PER_QUERY = int(os.getenv('MAX_TWEETS_PER_QUERY', '100'))
    MAX_REDDIT_POSTS_PER_SUBREDDIT = int(os.getenv('MAX_REDDIT_POSTS_PER_SUBREDDIT', '50'))

    # AI Keywords
    AI_KEYWORDS = os.getenv('AI_KEYWORDS', 'GPT,Claude,LLM,Machine Learning,Deep Learning,AI,OpenAI,Anthropic').split(',')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present"""
        required_vars = {
            'Twitter': [cls.TWITTER_BEARER_TOKEN],
            'Reddit': [cls.REDDIT_CLIENT_ID, cls.REDDIT_CLIENT_SECRET],
            'Kafka': [cls.KAFKA_BOOTSTRAP_SERVERS]
        }

        missing = {}
        for service, vars in required_vars.items():
            missing_vars = [var for var in vars if not var]
            if missing_vars:
                missing[service] = missing_vars

        if missing:
            print(f"❌ Missing configuration for: {missing}")
            return False

        print("✅ Configuration validated successfully")
        return True

    @classmethod
    def get_search_query(cls) -> str:
        """Build search query from AI keywords"""
        return ' OR '.join(cls.AI_KEYWORDS)


if __name__ == '__main__':
    # Test configuration
    print("Testing configuration...")
    Config.validate()
    print(f"Search query: {Config.get_search_query()}")
    print(f"Collection interval: {Config.COLLECTION_INTERVAL_SECONDS}s")
