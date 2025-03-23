"""
Redpanda Client Module
--------------------
Handles interactions with Redpanda/Kafka
"""

import json
import logging
import time
from typing import Dict, Any, Optional, Callable
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError, KafkaConnectionError

logger = logging.getLogger(__name__)

class RedpandaClient:
    """
    A client for interacting with Redpanda/Kafka.
    Handles message production and consumption.
    """
    
    def __init__(self):
        """Initialize the Redpanda client."""
        self.producer = None
        self.consumer = None
        self.connected = False
        self.config = None  # Store config for reconnection
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.reconnect_delay = 2  # seconds
    
    def connect_producer(self, config: Dict[str, Any]) -> bool:
        """
        Connect to Redpanda as a producer.
        
        Args:
            config: Configuration dictionary for Redpanda connection
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if not config:
            logger.warning("No Redpanda configuration provided")
            return False
        
        # Store config for reconnection
        self.config = config.copy()
            
        try:
            logger.debug("Starting the Kafka producer")
            self.producer = KafkaProducer(
                bootstrap_servers=config.get("bootstrap_servers", "localhost:9092"),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                reconnect_backoff_ms=1000,  # 1 second backoff for reconnections
                reconnect_backoff_max_ms=10000,  # 10 seconds max backoff
                request_timeout_ms=30000,  # 30 seconds request timeout
                retry_backoff_ms=500,  # 0.5 seconds retry backoff
                **{k: v for k, v in config.items() if k not in ["bootstrap_servers"]}
            )
            self.connected = True
            self.reconnect_attempts = 0  # Reset reconnect attempts on successful connection
            logger.info(f"Connected to Redpanda at {config.get('bootstrap_servers')}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redpanda: {e}")
            self.producer = None
            self.connected = False
            return False
    
    def reconnect_producer(self) -> bool:
        """
        Attempt to reconnect the producer.
        
        Returns:
            bool: True if reconnection was successful, False otherwise
        """
        if not self.config:
            logger.error("Cannot reconnect, no configuration available")
            return False
            
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached")
            return False
            
        logger.info(f"Attempting to reconnect to Redpanda (attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
        
        # Close existing connection if any
        if self.producer:
            try:
                self.producer.close(timeout=5)
            except:
                pass
            self.producer = None
            
        # Wait before reconnecting
        time.sleep(self.reconnect_delay * (self.reconnect_attempts + 1))
        
        # Increment attempt counter
        self.reconnect_attempts += 1
        
        # Try to reconnect
        return self.connect_producer(self.config)
    
    def connect_consumer(self, config: Dict[str, Any], topic: str, group_id: str = "bsky-monitor") -> bool:
        """
        Connect to Redpanda as a consumer.
        
        Args:
            config: Configuration dictionary for Redpanda connection
            topic: Topic to consume from
            group_id: Consumer group ID
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if not config:
            logger.warning("No Redpanda configuration provided")
            return False
            
        # Add consumer-specific configurations
        consumer_config = config.copy()
        consumer_config.update({
            "group_id": group_id,
            "auto_offset_reset": "earliest",
            "enable_auto_commit": True,
            "value_deserializer": lambda m: json.loads(m.decode('utf-8')),
            "key_deserializer": lambda m: m.decode('utf-8') if m else None,
            "reconnect_backoff_ms": 1000,  # 1 second backoff for reconnections
            "reconnect_backoff_max_ms": 10000,  # 10 seconds max backoff
            "request_timeout_ms": 30000,  # 30 seconds request timeout
            "retry_backoff_ms": 500,  # 0.5 seconds retry backoff
        })
        
        try:
            self.consumer = KafkaConsumer(
                topic,
                **consumer_config
            )
            logger.info(f"Connected consumer to Redpanda at {config.get('bootstrap_servers')}")
            logger.info(f"Subscribed to topic: {topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect consumer to Redpanda: {e}")
            self.consumer = None
            return False
    
    def send_message(self, topic: str, key: str, value: Dict[str, Any]) -> bool:
        """
        Send a message to Redpanda.
        
        Args:
            topic: Topic to send message to
            key: Message key
            value: Message value (will be serialized to JSON)
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self._check_producer():
            if self.config:
                # Try to reconnect if we have a configuration
                if not self.reconnect_producer():
                    return False
            else:
                return False
            
        try:
            future = self.producer.send(topic, key=key, value=value)
            
            # Wait for the result to ensure delivery
            result = future.get(timeout=10)
            logger.info(f"Message sent to Redpanda: topic={topic}, partition={result.partition}, offset={result.offset}")
            return True
        except KafkaConnectionError as ke:
            logger.error(f"Connection error when sending to Redpanda: {ke}")
            # Try to reconnect and send again
            if self.reconnect_producer():
                try:
                    future = self.producer.send(topic, key=key, value=value)
                    result = future.get(timeout=10)
                    logger.info(f"Message sent to Redpanda after reconnection: topic={topic}, partition={result.partition}, offset={result.offset}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to send message after reconnection: {e}")
                    return False
            return False
        except Exception as e:
            logger.error(f"Failed to send message to Redpanda: {e}")
            return False
    
    def consume_messages(self, callback: Callable[[str, Dict[str, Any]], None], timeout_ms: int = 1000):
        """
        Consume messages from Redpanda and process them with the callback.
        
        Args:
            callback: Function to call with each message (key, value)
            timeout_ms: Timeout for polling in milliseconds
        """
        if not self._check_consumer():
            return
            
        try:
            # Poll for messages
            message_batch = self.consumer.poll(timeout_ms=timeout_ms)
            
            for topic_partition, messages in message_batch.items():
                for message in messages:
                    logger.debug(f"Received message: {message.key} = {message.value}")
                    callback(message.key, message.value)
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
    
    def close(self):
        """Close connections to Redpanda."""
        if self.producer:
            try:
                self.producer.flush()
                self.producer.close()
                logger.info("Redpanda producer closed")
            except Exception as e:
                logger.warning(f"Error closing producer: {e}")
            
        if self.consumer:
            try:
                self.consumer.close()
                logger.info("Redpanda consumer closed")
            except Exception as e:
                logger.warning(f"Error closing consumer: {e}")
            
        self.connected = False
    
    def _check_producer(self) -> bool:
        """Check if the producer is connected."""
        if not self.producer or not self.connected:
            logger.error("Redpanda producer not connected")
            return False
        return True
    
    def _check_consumer(self) -> bool:
        """Check if the consumer is connected."""
        if not self.consumer:
            logger.error("Redpanda consumer not connected")
            return False
        return True 