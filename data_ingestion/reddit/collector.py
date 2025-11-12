"""
Reddit Data Collector
Collects posts from AI-related subreddits and sends to Kafka
"""
import time
from datetime import datetime
from typing import List, Dict, Any, Set
import praw
from praw.exceptions import RedditAPIException
from loguru import logger
import schedule
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from kafka_producer import SocialMediaProducer


class RedditCollector:
    """Collect Reddit posts from AI-related subreddits"""

    # Target subreddits for AI content
    TARGET_SUBREDDITS = [
        'MachineLearning',
        'artificial',
        'LocalLLaMA',
        'OpenAI',
        'ChatGPT',
        # 'ArtificialIntelligence',  # 暂时禁用：返回404错误（可能被禁用或私有化）
        'deeplearning',
        'LanguageTechnology',
        'learnmachinelearning',  # 替代subreddit
        'agi'  # 添加AGI相关内容
    ]

    def __init__(self):
        """Initialize Reddit API client"""
        self.reddit = None
        self.producer = SocialMediaProducer()
        self.seen_posts: Set[str] = set()  # Track already collected posts
        self.rate_limit_wait = 60  # Initial wait time for rate limiting (seconds)
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Reddit API"""
        try:
            self.reddit = praw.Reddit(
                client_id=Config.REDDIT_CLIENT_ID,
                client_secret=Config.REDDIT_CLIENT_SECRET,
                user_agent=Config.REDDIT_USER_AGENT
            )
            # Test authentication
            logger.info(f"✅ Reddit API authenticated as: {self.reddit.read_only}")
        except Exception as e:
            logger.error(f"❌ Reddit authentication failed: {e}")
            raise

    def _handle_rate_limit(self, error_msg: str = ""):
        """
        Handle rate limiting with exponential backoff

        Args:
            error_msg: Error message from API
        """
        logger.warning(f"⚠️  Rate limited by Reddit API: {error_msg}")
        logger.info(f"⏳ Waiting {self.rate_limit_wait} seconds before retry...")
        time.sleep(self.rate_limit_wait)

        # Exponential backoff: double wait time, max 10 minutes
        self.rate_limit_wait = min(self.rate_limit_wait * 2, 600)

    def _reset_rate_limit_wait(self):
        """Reset rate limit wait time after successful request"""
        self.rate_limit_wait = 60

    def extract_post_data(self, submission) -> Dict[str, Any]:
        """
        Extract relevant data from Reddit submission

        Args:
            submission: PRAW submission object

        Returns:
            Dictionary with post data
        """
        return {
            'id': submission.id,
            'title': submission.title,
            'text': submission.selftext if hasattr(submission, 'selftext') else '',
            'author': str(submission.author) if submission.author else '[deleted]',
            'subreddit': str(submission.subreddit),
            'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
            'url': submission.url,
            'permalink': f"https://reddit.com{submission.permalink}",
            'metrics': {
                'score': submission.score,
                'upvote_ratio': submission.upvote_ratio,
                'num_comments': submission.num_comments
            },
            'is_self': submission.is_self,
            'flair': submission.link_flair_text,
            'domain': submission.domain,
            'gilded': submission.gilded,
            'stickied': submission.stickied
        }

    def collect_from_subreddit(self, subreddit_name: str, limit: int = None, retry_count: int = 0) -> int:
        """
        Collect posts from a specific subreddit with retry logic

        Args:
            subreddit_name: Name of subreddit
            limit: Max number of posts to collect
            retry_count: Current retry attempt (for internal use)

        Returns:
            Number of posts collected
        """
        if limit is None:
            limit = Config.MAX_REDDIT_POSTS_PER_SUBREDDIT

        logger.info(f"🔍 Collecting from r/{subreddit_name} (limit={limit})")

        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            count = 0

            # Get hot posts (most engaging right now)
            for submission in subreddit.hot(limit=limit):
                post_id = submission.id

                # Skip if already collected
                if post_id in self.seen_posts:
                    continue

                # Extract post data
                post_data = self.extract_post_data(submission)

                # Send to Kafka
                if self.producer.send_reddit_post(post_data):
                    count += 1
                    self.seen_posts.add(post_id)
                    logger.debug(f"✅ Sent Reddit post {post_id} to Kafka")

            # Success - reset rate limit wait time
            self._reset_rate_limit_wait()

            logger.info(f"📊 Collected {count} new posts from r/{subreddit_name}")
            return count

        except RedditAPIException as e:
            # Check if it's a rate limit error
            if 'RATELIMIT' in str(e).upper() or '429' in str(e):
                if retry_count < 3:  # Max 3 retries
                    self._handle_rate_limit(str(e))
                    return self.collect_from_subreddit(subreddit_name, limit, retry_count + 1)
                else:
                    logger.error(f"❌ Max retries exceeded for r/{subreddit_name}")
                    return 0
            else:
                logger.error(f"❌ Reddit API error for r/{subreddit_name}: {e}")
                return 0

        except Exception as e:
            logger.error(f"❌ Error collecting from r/{subreddit_name}: {e}")
            return 0

    def collect_all_subreddits(self) -> int:
        """
        Collect posts from all target subreddits

        Returns:
            Total number of posts collected
        """
        total_count = 0
        successful_subreddits = 0

        for i, subreddit_name in enumerate(self.TARGET_SUBREDDITS):
            try:
                count = self.collect_from_subreddit(subreddit_name)
                total_count += count
                successful_subreddits += 1

                # Rate limiting - be nice to Reddit API
                # Increased delay between subreddits to reduce rate limiting
                if i < len(self.TARGET_SUBREDDITS) - 1:  # Don't sleep after last subreddit
                    time.sleep(3)  # Increased from 2 to 3 seconds

            except Exception as e:
                logger.error(f"❌ Failed to collect from r/{subreddit_name}: {e}")
                continue

        logger.info(f"📊 Total collected: {total_count} posts from {successful_subreddits}/{len(self.TARGET_SUBREDDITS)} subreddits")
        self.producer.flush()

        return total_count

    def search_ai_keywords(self, limit: int = 50) -> int:
        """
        Search Reddit for AI-related keywords across all subreddits

        Args:
            limit: Max results per keyword

        Returns:
            Number of posts collected
        """
        count = 0

        # Use a subset of keywords to avoid rate limiting
        keywords = ['GPT', 'Claude AI', 'LLM', 'ChatGPT', 'AI model']

        for keyword in keywords:
            try:
                logger.info(f"🔍 Searching Reddit for: {keyword}")

                for submission in self.reddit.subreddit('all').search(
                    keyword,
                    sort='new',
                    time_filter='day',
                    limit=limit
                ):
                    post_id = submission.id

                    if post_id in self.seen_posts:
                        continue

                    post_data = self.extract_post_data(submission)

                    if self.producer.send_reddit_post(post_data):
                        count += 1
                        self.seen_posts.add(post_id)

                time.sleep(2)  # Rate limiting

            except Exception as e:
                logger.error(f"❌ Search error for '{keyword}': {e}")
                continue

        logger.info(f"📊 Search collected {count} posts")
        return count

    def run_scheduled(self):
        """Run collection on a schedule"""
        logger.info(f"🕐 Starting scheduled Reddit collection every {Config.COLLECTION_INTERVAL_SECONDS} seconds")

        # Run immediately on start
        self.collect_all_subreddits()

        # Schedule periodic collection
        schedule.every(Config.COLLECTION_INTERVAL_SECONDS).seconds.do(self.collect_all_subreddits)

        # Keep running
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)

                # Clean up seen_posts set if it gets too large (keep last 10k)
                if len(self.seen_posts) > 10000:
                    self.seen_posts = set(list(self.seen_posts)[-5000:])

            except KeyboardInterrupt:
                logger.info("⏹️  Collection stopped by user")
                self.shutdown()
                break
            except Exception as e:
                logger.error(f"❌ Error in scheduled run: {e}")
                time.sleep(60)

    def shutdown(self):
        """Clean shutdown"""
        logger.info("🛑 Shutting down Reddit collector...")
        self.producer.flush()
        self.producer.close()
        logger.info("👋 Reddit collector stopped")


def main():
    """Main entry point"""
    # Setup logging
    logger.add(
        "logs/reddit_collector.log",
        rotation="1 day",
        retention="7 days",
        level=Config.LOG_LEVEL
    )

    logger.info("🚀 Starting Reddit Collector")

    # Validate Reddit-specific configuration
    if not Config.REDDIT_CLIENT_ID or not Config.REDDIT_CLIENT_SECRET:
        logger.error("❌ Reddit API credentials not configured")
        logger.info("💡 Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in config/.env")
        return

    # Create and run collector
    collector = RedditCollector()

    try:
        collector.run_scheduled()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        collector.shutdown()


if __name__ == '__main__':
    main()
