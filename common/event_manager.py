"""
Event Manager Module

This module centralizes the application's asynchronous, event-driven approach.
It handles connections, subscriptions, and publishes to the message broker
(Kafka in this example). Microservices and the monolith can import this module
to send and receive events in a decoupled way.

Usage:
    - from common.event_manager import EventManager
    - event_manager = EventManager(config)
    - event_manager.start_consumer()
    - event_manager.send_event("topic_name", payload)
"""

import asyncio
from confluent_kafka import Consumer, Producer, KafkaError

class EventManager:
    """
    The EventManager class encapsulates Kafka connections for publishing and consuming events.

    Args:
        config (dict): A dictionary of Kafka configuration parameters.
    """
    def __init__(self, config):
        self.config = config
        self.consumer = None
        self.producer = None
        self.running = False

    def start_consumer(self, topic, group_id="default-group"):
        """
        Initialize and start a Kafka consumer for the given topic.

        Args:
            topic (str): The Kafka topic to subscribe to.
            group_id (str): Consumer group ID for Kafka partition assignment.
        """
        consumer_opts = {
            'bootstrap.servers': self.config.get('bootstrap.servers', 'localhost:9092'),
            'group.id': group_id,
            'auto.offset.reset': 'earliest'
        }
        self.consumer = Consumer(consumer_opts)
        self.consumer.subscribe([topic])
        self.running = True

        while self.running:
            msg = self.consumer.poll(1.0)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    # Robust error handling: log/raise for troubleshooting
                    print(f"[Consumer Error]: {msg.error()}")
                    break

            # Process the message asynchronously
            asyncio.run(self._handle_message(msg))

        self.consumer.close()

    def stop_consumer(self):
        """
        Gracefully stop the consumer loop.
        """
        self.running = False

    async def _handle_message(self, msg):
        """
        Internal async method to process a consumed message from Kafka.

        Args:
            msg: Kafka message object.
        """
        payload = msg.value().decode('utf-8')
        print(f"[EventManager] Received: {payload}")
        # TODO: Implement actual business logic (AI tasks, etc.)

    def send_event(self, topic, payload):
        """
        Publish an event to the specified Kafka topic.

        Args:
            topic (str): Name of the Kafka topic to publish to.
            payload (str): Event payload to send.

        Returns:
            None
        """
        if not self.producer:
            self.producer = Producer({'bootstrap.servers': self.config.get('bootstrap.servers', 'localhost:9092')})

        def delivery_report(err, _msg):
            if err:
                # Robust error handling
                print(f"[Producer Error]: {err}")

        # Asynchronous send
        self.producer.produce(topic, value=payload.encode('utf-8'), callback=delivery_report)
        self.producer.poll(0)  # Trigger delivery callbacks 