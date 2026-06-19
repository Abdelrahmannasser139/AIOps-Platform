"""
Phase 1 / Step 4 - PostgreSQL connection helper.

Usage:
    from db.postgres_client import get_engine, insert_incident

    engine = get_engine()
    incident_id = insert_incident(engine, kpi_id="02e99bd4...", severity="P2", ...)
"""
import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

DEFAULT_DSN = "postgresql+psycopg2://aiops:aiops_dev_password@localhost:5432/aiops"


def get_engine(dsn: str | None = None) -> Engine:
    dsn = dsn or os.getenv("POSTGRES_DSN", DEFAULT_DSN)
    return create_engine(dsn, pool_pre_ping=True)


def insert_incident(
    engine: Engine,
    kpi_id: str,
    severity: str,
    detected_at: datetime | None = None,
) -> int:
    detected_at = detected_at or datetime.now(timezone.utc)
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO incidents (kpi_id, severity, detected_at, status)
                VALUES (:kpi_id, :severity, :detected_at, 'detected')
                RETURNING id
                """
            ),
            {"kpi_id": kpi_id, "severity": severity, "detected_at": detected_at},
        )
        return result.scalar_one()


def update_incident_status(engine: Engine, incident_id: int, status: str, **fields) -> None:
    set_clauses = ["status = :status", "updated_at = now()"]
    params = {"id": incident_id, "status": status}
    for key, value in fields.items():
        set_clauses.append(f"{key} = :{key}")
        params[key] = value

    with engine.begin() as conn:
        conn.execute(
            text(f"UPDATE incidents SET {', '.join(set_clauses)} WHERE id = :id"),
            params,
        )


if __name__ == "__main__":
    engine = get_engine()
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar_one()
        print(f"Connected OK. Postgres version: {version}")
