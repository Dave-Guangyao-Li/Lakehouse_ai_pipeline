"""
Twitter Data Collector
Collects tweets related to AI topics and sends to Kafka
"""
import time
from datetime import datetime
from typing import List, Dict, Any
import tweepy
from loguru import logger
import schedule
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from kafka_producer import SocialMediaProducer


class TwitterCollector:
    """Collect tweets about AI topics"""

    def __init__(self):
        """Initialize Twitter API client"""
        self.client = None
        self.producer = SocialMediaProducer()
        self.last_tweet_id = None  # For pagination
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Twitter API"""
        try:
            self.client = tweepy.Client(
                bearer_token=Config.TWITTER_BEARER_TOKEN,
                wait_on_rate_limit=True
            )
            logger.info("✅ Twitter API authenticated successfully")
        except Exception as e:
            logger.error(f"❌ Twitter authentication failed: {e}")
            raise

    def collect_tweets(self, max_results: int = None) -> int:
        """
        Collect recent tweets about AI topics

        Args:
            max_results: Maximum number of tweets to collect (default from config)

        Returns:
            Number of tweets collected
        """
        if max_results is None:
            max_results = Config.MAX_TWEETS_PER_QUERY

        query = Config.get_search_query()
        logger.info(f"🔍 Searching for tweets with query: {query}")

        try:
            # Use Twitter API v2 to search recent tweets
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'lang', 'entities'],
                expansions=['author_id'],
                user_fields=['username', 'name', 'verified'],
                since_id=self.last_tweet_id  # Only get new tweets
            )

            if not tweets.data:
                logger.info("ℹ️  No new tweets found")
                return 0

            # Build user lookup dict
            users = {user.id: user for user in tweets.includes.get('users', [])} if tweets.includes else {}

            count = 0
            for tweet in tweets.data:
                # Extract tweet data
                author = users.get(tweet.author_id)

                tweet_data = {
                    'id': str(tweet.id),
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                    'author_id': str(tweet.author_id),
                    'author_username': author.username if author else None,
                    'author_name': author.name if author else None,
                    'author_verified': author.verified if author else False,
                    'language': tweet.lang,
                    'metrics': {
                        'likes': tweet.public_metrics.get('like_count', 0),
                        'retweets': tweet.public_metrics.get('retweet_count', 0),
                        'replies': tweet.public_metrics.get('reply_count', 0),
                        'quotes': tweet.public_metrics.get('quote_count', 0)
                    },
                    'hashtags': [tag['tag'] for tag in tweet.entities.get('hashtags', [])] if tweet.entities else [],
                    'mentions': [mention['username'] for mention in tweet.entities.get('mentions', [])] if tweet.entities else []
                }

                # Send to Kafka
                if self.producer.send_tweet(tweet_data):
                    count += 1
                    logger.debug(f"✅ Sent tweet {tweet.id} to Kafka")

            # Update last tweet ID for next collection
            if tweets.data:
                self.last_tweet_id = tweets.data[0].id

            logger.info(f"📊 Collected and sent {count} tweets to Kafka")
            return count

        except tweepy.TweepyException as e:
            logger.error(f"❌ Twitter API error: {e}")
            return 0
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return 0

    def run_scheduled(self):
        """Run collection on a schedule"""
        logger.info(f"🕐 Starting scheduled collection every {Config.COLLECTION_INTERVAL_SECONDS} seconds")

        # Run immediately on start
        self.collect_tweets()

        # Schedule periodic collection
        schedule.every(Config.COLLECTION_INTERVAL_SECONDS).seconds.do(self.collect_tweets)

        # Keep running
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("⏹️  Collection stopped by user")
                self.shutdown()
                break
            except Exception as e:
                logger.error(f"❌ Error in scheduled run: {e}")
                time.sleep(60)  # Wait a minute before retrying

    def shutdown(self):
        """Clean shutdown"""
        logger.info("🛑 Shutting down Twitter collector...")
        self.producer.flush()
        self.producer.close()
        logger.info("👋 Twitter collector stopped")


def main():
    """Main entry point"""
    # Setup logging
    logger.add(
        "logs/twitter_collector.log",
        rotation="1 day",
        retention="7 days",
        level=Config.LOG_LEVEL
    )

    logger.info("🚀 Starting Twitter Collector")

    # Validate configuration
    if not Config.validate():
        logger.error("❌ Configuration validation failed")
        return

    # Create and run collector
    collector = TwitterCollector()

    try:
        collector.run_scheduled()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        collector.shutdown()


if __name__ == '__main__':
    main()
