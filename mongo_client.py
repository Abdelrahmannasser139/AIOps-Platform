"""
Phase 1 / Step 4 - MongoDB connection helper.

Stores raw, unstructured agent outputs: LLM responses, evidence blobs,
log excerpts. PostgreSQL stays clean and structured; Mongo holds the messy stuff.

Usage:
    from db.mongo_client import get_db, save_agent_output

    db = get_db()
    save_agent_output(db, incident_id=42, agent_name="rca_agent", payload={...})
"""
import os
from datetime import datetime, timezone

from pymongo import MongoClient
from pymongo.database import Database

DEFAULT_URI = "mongodb://aiops:aiops_dev_password@localhost:27017/aiops?authSource=admin"


def get_client(uri: str | None = None) -> MongoClient:
    uri = uri or os.getenv("MONGO_URI", DEFAULT_URI)
    return MongoClient(uri)


def get_db(uri: str | None = None) -> Database:
    client = get_client(uri)
    return client["aiops"]


def save_agent_output(db: Database, incident_id: int, agent_name: str, payload: dict) -> str:
    doc = {
        "incident_id": incident_id,
        "agent_name": agent_name,
        "payload": payload,
        "created_at": datetime.now(timezone.utc),
    }
    result = db["agent_outputs"].insert_one(doc)
    return str(result.inserted_id)


def get_agent_outputs(db: Database, incident_id: int) -> list[dict]:
    return list(db["agent_outputs"].find({"incident_id": incident_id}))


if __name__ == "__main__":
    db = get_db()
    print("Connected OK. Collections:", db.list_collection_names())
