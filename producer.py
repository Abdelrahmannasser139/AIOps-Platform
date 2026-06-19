"""
Phase 1 / Step 3 - Kafka producer that replays the KPI CSV as a simulated
live telemetry stream.

Each row becomes one Kafka message on the 'kpi-stream' topic:
    {
        "timestamp": 1493568000,
        "value": 1.90163934,
        "label": 0,
        "kpi_id": "02e99bd4f6cfb33f"
    }

Run (after Kafka is up via docker-compose):
    python streaming/producer.py --speed 1000 --limit 5000
"""
import argparse
import json
import time
from pathlib import Path

import pandas as pd
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

TOPIC = "kpi-stream"
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "train.parquet"


def make_producer(bootstrap_servers: str = "localhost:9092") -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )


def replay(
    producer: KafkaProducer,
    df: pd.DataFrame,
    speed: float = 1000.0,
    limit: int | None = None,
) -> None:
    """
    Replay rows in timestamp order. `speed` is a multiplier: 1000 means
    1000x faster than real time (a 60s gap becomes 0.06s). Use a very high
    speed for fast local testing, lower it to feel like a "live" demo.
    """
    df = df.sort_values("timestamp").reset_index(drop=True)
    if limit:
        df = df.head(limit)

    prev_ts = None
    sent = 0
    for _, row in df.iterrows():
        if prev_ts is not None:
            gap = (row["timestamp"] - prev_ts) / speed
            if gap > 0:
                time.sleep(min(gap, 2.0))  # cap sleep so demo doesn't stall
        prev_ts = row["timestamp"]

        message = {
            "timestamp": int(row["timestamp"]),
            "value": float(row["value"]),
            "label": int(row["label"]) if "label" in row and pd.notna(row["label"]) else None,
            "kpi_id": row["KPI ID"],
        }

        producer.send(TOPIC, key=message["kpi_id"], value=message)
        sent += 1
        if sent % 500 == 0:
            print(f"  sent {sent:,} messages...")

    producer.flush()
    print(f"Done. Sent {sent:,} total messages to topic '{TOPIC}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-servers", default="localhost:9092")
    parser.add_argument("--speed", type=float, default=1000.0, help="replay speed multiplier")
    parser.add_argument("--limit", type=int, default=None, help="max rows to send")
    args = parser.parse_args()

    print(f"Loading {DATA_PATH} ...")
    df = pd.read_parquet(DATA_PATH)
    print(f"Loaded {len(df):,} rows.")

    try:
        producer = make_producer(args.bootstrap_servers)
    except NoBrokersAvailable:
        print(f"ERROR: could not reach Kafka at {args.bootstrap_servers}.")
        print("Start it first with: docker compose -f docker/docker-compose.yml up -d")
        raise SystemExit(1)

    print(f"Replaying to topic '{TOPIC}' at {args.speed}x speed...")
    replay(producer, df, speed=args.speed, limit=args.limit)
