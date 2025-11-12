"""
Kafka Producer for sending social media data to Kafka topics
"""
import json
from typing import Dict, Any
from kafka import KafkaProducer
from kafka.errors import KafkaError
from loguru import logger
from config import Config


class SocialMediaProducer:
    """Kafka producer for social media data"""

    def __init__(self):
        """Initialize Kafka producer"""
        self.producer = None
        self._connect()

    def _connect(self):
        """Connect to Kafka broker"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,
                max_in_flight_requests_per_connection=1,  # Ensure ordering
                compression_type='gzip'
            )
            logger.info(f"✅ Connected to Kafka broker: {Config.KAFKA_BOOTSTRAP_SERVERS}")
        except KafkaError as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            raise

    def send_message(self, topic: str, message: Dict[str, Any], key: str = None):
        """
        Send a message to Kafka topic

        Args:
            topic: Kafka topic name
            message: Message payload (dict)
            key: Optional message key for partitioning
        """
        try:
            future = self.producer.send(topic, value=message, key=key)
            # Block until message is sent or timeout
            record_metadata = future.get(timeout=10)

            logger.debug(
                f"Message sent to {record_metadata.topic} "
                f"partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
            return True

        except KafkaError as e:
            logger.error(f"❌ Failed to send message to Kafka: {e}")
            return False

    def send_tweet(self, tweet_data: Dict[str, Any]):
        """Send tweet data to Kafka"""
        message = {
            'source': 'twitter',
            'data': tweet_data,
            'timestamp': tweet_data.get('created_at')
        }
        tweet_id = tweet_data.get('id')
        return self.send_message(Config.KAFKA_TOPIC_RAW, message, key=str(tweet_id))

    def send_reddit_post(self, post_data: Dict[str, Any]):
        """Send Reddit post data to Kafka"""
        message = {
            'source': 'reddit',
            'data': post_data,
            'timestamp': post_data.get('created_utc')
        }
        post_id = post_data.get('id')
        return self.send_message(Config.KAFKA_TOPIC_RAW, message, key=str(post_id))

    def send_bluesky_post(self, post_data: Dict[str, Any]):
        """Send Bluesky post data to Kafka"""
        message = {
            'source': 'bluesky',
            'data': post_data,
            'timestamp': post_data.get('created_at')
        }
        post_id = post_data.get('id')
        return self.send_message(Config.KAFKA_TOPIC_RAW, message, key=str(post_id))

    def flush(self):
        """Flush any pending messages"""
        if self.producer:
            self.producer.flush()
            logger.info("📤 Flushed all pending messages")

    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("🔌 Kafka producer closed")


# Example usage
if __name__ == '__main__':
    logger.add("logs/kafka_producer.log", rotation="1 day")

    # Test producer
    producer = SocialMediaProducer()

    # Test tweet
    test_tweet = {
        'id': '123456789',
        'text': 'Testing Kafka producer with AI content',
        'author': 'test_user',
        'created_at': '2025-11-11T00:00:00Z',
        'likes': 10,
        'retweets': 5
    }

    success = producer.send_tweet(test_tweet)
    print(f"Tweet sent: {success}")

    producer.close()
