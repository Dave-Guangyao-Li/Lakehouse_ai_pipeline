"""
Bluesky Data Collector
Collects posts from Bluesky (AT Protocol) and sends to Kafka
"""
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from loguru import logger
import schedule
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from kafka_producer import SocialMediaProducer

try:
    from atproto import Client
    ATPROTO_AVAILABLE = True
except ImportError:
    ATPROTO_AVAILABLE = False
    logger.warning("⚠️  atproto library not installed. Run: pip install atproto")


class BlueskyCollector:
    """Collect posts from Bluesky about AI topics"""

    def __init__(self):
        """Initialize Bluesky AT Protocol client"""
        if not ATPROTO_AVAILABLE:
            raise ImportError("atproto library is required. Install with: pip install atproto")

        self.client = None
        self.producer = SocialMediaProducer()
        self.last_cursor = None  # For pagination
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Bluesky AT Protocol"""
        try:
            self.client = Client()

            # Login with handle and app password
            handle = os.getenv('BLUESKY_HANDLE')
            password = os.getenv('BLUESKY_APP_PASSWORD')

            if not handle or not password:
                raise ValueError("BLUESKY_HANDLE and BLUESKY_APP_PASSWORD must be set in environment")

            self.client.login(handle, password)
            logger.info(f"✅ Bluesky authenticated successfully as @{handle}")

        except Exception as e:
            logger.error(f"❌ Bluesky authentication failed: {e}")
            raise

    def collect_posts(self, max_results: int = 50) -> int:
        """
        Collect recent posts about AI topics from Bluesky

        Args:
            max_results: Maximum number of posts to collect

        Returns:
            Number of posts collected
        """
        # AI-related search terms
        search_terms = [
            'AI', 'artificial intelligence', 'machine learning', 'deep learning',
            'GPT', 'LLM', 'neural network', 'ChatGPT', 'Claude', 'OpenAI',
            'generative AI', 'AGI', 'transformer', 'diffusion model'
        ]

        logger.info(f"🔍 Searching Bluesky for AI-related posts")

        try:
            all_posts = []

            # Search using multiple terms
            for term in search_terms[:3]:  # Limit to top 3 terms to avoid rate limits
                try:
                    # Use app.bsky.feed.searchPosts
                    response = self.client.app.bsky.feed.search_posts(
                        {'q': term, 'limit': min(max_results // 3, 25)}
                    )

                    if response and hasattr(response, 'posts'):
                        all_posts.extend(response.posts)
                        logger.debug(f"Found {len(response.posts)} posts for term '{term}'")

                    time.sleep(0.5)  # Rate limiting

                except Exception as e:
                    logger.warning(f"Error searching for '{term}': {e}")
                    continue

            if not all_posts:
                logger.info("ℹ️  No new posts found")
                return 0

            # Remove duplicates by post URI
            seen_uris = set()
            unique_posts = []
            for post in all_posts:
                if post.uri not in seen_uris:
                    seen_uris.add(post.uri)
                    unique_posts.append(post)

            count = 0
            for post in unique_posts[:max_results]:
                try:
                    # Extract post data
                    record = post.record

                    post_data = {
                        'id': post.uri.split('/')[-1],  # Extract post ID from URI
                        'uri': post.uri,
                        'text': record.text if hasattr(record, 'text') else '',
                        'created_at': record.created_at if hasattr(record, 'created_at') else datetime.now().isoformat(),
                        'author_did': post.author.did,
                        'author_handle': post.author.handle,
                        'author_display_name': post.author.display_name if hasattr(post.author, 'display_name') else post.author.handle,
                        'language': getattr(record, 'langs', ['en'])[0] if hasattr(record, 'langs') else 'en',
                        'metrics': {
                            'likes': post.like_count if hasattr(post, 'like_count') else 0,
                            'reposts': post.repost_count if hasattr(post, 'repost_count') else 0,
                            'replies': post.reply_count if hasattr(post, 'reply_count') else 0,
                            'quotes': getattr(post, 'quote_count', 0)
                        },
                        'hashtags': self._extract_hashtags(record.text if hasattr(record, 'text') else ''),
                        'mentions': self._extract_mentions(record.text if hasattr(record, 'text') else '')
                    }

                    # Send to Kafka
                    if self.producer.send_bluesky_post(post_data):
                        count += 1
                        logger.debug(f"✅ Sent Bluesky post to Kafka")

                except Exception as e:
                    logger.warning(f"Error processing post: {e}")
                    continue

            logger.info(f"📊 Collected and sent {count} Bluesky posts to Kafka")
            return count

        except Exception as e:
            logger.error(f"❌ Bluesky API error: {e}")
            return 0

    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        import re
        return re.findall(r'#(\w+)', text)

    def _extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from text"""
        import re
        return re.findall(r'@([\w.]+)', text)

    def run_scheduled(self):
        """Run collection on a schedule"""
        interval = int(os.getenv('BLUESKY_COLLECTION_INTERVAL', Config.COLLECTION_INTERVAL_SECONDS))
        logger.info(f"🕐 Starting scheduled Bluesky collection every {interval} seconds")

        # Run immediately on start
        self.collect_posts()

        # Schedule periodic collection
        schedule.every(interval).seconds.do(self.collect_posts)

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
        logger.info("🛑 Shutting down Bluesky collector...")
        self.producer.flush()
        self.producer.close()
        logger.info("👋 Bluesky collector stopped")


def main():
    """Main entry point"""
    # Setup logging
    logger.add(
        "logs/bluesky_collector.log",
        rotation="1 day",
        retention="7 days",
        level=os.getenv('LOG_LEVEL', 'INFO')
    )

    logger.info("🚀 Starting Bluesky Collector")

    # Check if credentials are set
    if not os.getenv('BLUESKY_HANDLE') or not os.getenv('BLUESKY_APP_PASSWORD'):
        logger.error("❌ BLUESKY_HANDLE and BLUESKY_APP_PASSWORD must be set")
        logger.info("💡 Set them in config/.env file")
        return

    # Create and run collector
    try:
        collector = BlueskyCollector()
        collector.run_scheduled()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")


if __name__ == '__main__':
    main()
