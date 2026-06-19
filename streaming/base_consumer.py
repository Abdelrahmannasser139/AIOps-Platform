"""
Phase 1 / Step 3 - Base Kafka consumer class.

Every agent (Detection, RCA, Deployment, etc.) inherits from BaseAgentConsumer
and implements `handle_message`. This keeps Kafka boilerplate out of agent code.

Example:
    class DetectionAgent(BaseAgentConsumer):
        def handle_message(self, message: dict) -> None:
            if self.is_anomaly(message):
                self.publish("incidents", message)

    DetectionAgent(topic="kpi-stream", group_id="detection-agent").run()
"""
import json
from abc import ABC, abstractmethod

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable


class BaseAgentConsumer(ABC):
    def __init__(
        self,
        topic: str,
        group_id: str,
        bootstrap_servers: str = "localhost:9092",
        auto_offset_reset: str = "earliest",
    ) -> None:
        self.topic = topic
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers

        try:
            self.consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
            )
            self._producer: KafkaProducer | None = None
        except NoBrokersAvailable as exc:
            raise RuntimeError(
                f"Could not connect to Kafka at {bootstrap_servers}. "
                f"Start it with: docker compose -f docker/docker-compose.yml up -d"
            ) from exc

    @property
    def producer(self) -> KafkaProducer:
        """Lazily create a producer only if the agent needs to publish downstream."""
        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
        return self._producer

    def publish(self, topic: str, message: dict, key: str | None = None) -> None:
        self.producer.send(topic, key=key, value=message)
        self.producer.flush()

    @abstractmethod
    def handle_message(self, message: dict) -> None:
        """Override this in each agent subclass."""
        raise NotImplementedError

    def run(self) -> None:
        print(f"[{self.group_id}] listening on topic '{self.topic}'...")
        for record in self.consumer:
            try:
                self.handle_message(record.value)
            except Exception as exc:
                print(f"[{self.group_id}] ERROR handling message: {exc}")
