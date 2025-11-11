"""
Kafka Reader for Dashboard
Read real-time data from Kafka topic
"""
import json
from kafka import KafkaConsumer, TopicPartition
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime


class KafkaDataReader:
    """Read data from Kafka for dashboard display"""

    def __init__(self,
                 bootstrap_servers='localhost:9092',
                 topic='ai-social-raw',
                 max_messages=100):
        """
        Initialize Kafka consumer

        Args:
            bootstrap_servers: Kafka broker address
            topic: Topic to consume from
            max_messages: Maximum messages to fetch
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.max_messages = max_messages

    def get_recent_messages(self, num_messages=50) -> List[Dict[str, Any]]:
        """
        Fetch recent messages from Kafka

        Args:
            num_messages: Number of recent messages to fetch

        Returns:
            List of message dictionaries
        """
        messages = []

        try:
            # Create consumer
            consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='latest',  # Start from end
                enable_auto_commit=False,
                consumer_timeout_ms=5000,  # 5 second timeout
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )

            # Seek to recent messages
            partitions = consumer.partitions_for_topic(self.topic)
            if partitions:
                for partition in partitions:
                    tp = TopicPartition(self.topic, partition)
                    consumer.assign([tp])

                    # Get offset
                    end_offset = consumer.end_offsets([tp])[tp]
                    start_offset = max(0, end_offset - num_messages)

                    consumer.seek(tp, start_offset)

                    # Read messages
                    for message in consumer:
                        messages.append(message.value)
                        if len(messages) >= num_messages:
                            break

                    if len(messages) >= num_messages:
                        break

            consumer.close()

        except Exception as e:
            print(f"Error reading from Kafka: {e}")
            return []

        return messages[-num_messages:] if messages else []

    def get_all_messages(self) -> List[Dict[str, Any]]:
        """
        Fetch all available messages from Kafka

        Returns:
            List of all message dictionaries
        """
        messages = []

        try:
            consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='earliest',  # Start from beginning
                enable_auto_commit=False,
                consumer_timeout_ms=5000,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )

            # Read all messages
            for message in consumer:
                messages.append(message.value)
                if len(messages) >= self.max_messages:
                    break

            consumer.close()

        except Exception as e:
            print(f"Error reading all messages from Kafka: {e}")
            return []

        return messages

    def parse_to_dataframe(self, messages: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Parse Kafka messages to pandas DataFrame

        Args:
            messages: List of message dictionaries

        Returns:
            DataFrame with parsed data
        """
        if not messages:
            return pd.DataFrame()

        parsed_data = []

        for msg in messages:
            try:
                source = msg.get('source', 'unknown')
                data = msg.get('data', {})
                timestamp = msg.get('timestamp')

                if source == 'twitter':
                    parsed_data.append({
                        'source': 'Twitter',
                        'post_id': data.get('id'),
                        'text': data.get('text', ''),
                        'author': data.get('author_username', 'Unknown'),
                        'created_at': data.get('created_at'),
                        'engagement': (
                            data.get('metrics', {}).get('likes', 0) +
                            data.get('metrics', {}).get('retweets', 0) * 2
                        ),
                        'likes': data.get('metrics', {}).get('likes', 0),
                        'retweets': data.get('metrics', {}).get('retweets', 0),
                        'hashtags': ','.join(data.get('hashtags', [])),
                    })

                elif source == 'reddit':
                    parsed_data.append({
                        'source': 'Reddit',
                        'post_id': data.get('id'),
                        'text': f"{data.get('title', '')} {data.get('text', '')}",
                        'author': data.get('author', 'Unknown'),
                        'created_at': data.get('created_utc'),
                        'engagement': data.get('metrics', {}).get('score', 0),
                        'likes': data.get('metrics', {}).get('score', 0),
                        'retweets': 0,
                        'hashtags': '',
                        'subreddit': data.get('subreddit', ''),
                    })

            except Exception as e:
                print(f"Error parsing message: {e}")
                continue

        return pd.DataFrame(parsed_data)


# Standalone test
if __name__ == '__main__':
    reader = KafkaDataReader()
    messages = reader.get_recent_messages(10)

    print(f"Fetched {len(messages)} messages")

    if messages:
        df = reader.parse_to_dataframe(messages)
        print(df.head())
