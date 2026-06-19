-- Phase 1 / Step 4 - PostgreSQL schema for structured incident records.
-- Auto-runs on first container start via docker-entrypoint-initdb.d.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS incidents (
    id              SERIAL PRIMARY KEY,
    incident_uuid   UUID DEFAULT gen_random_uuid() UNIQUE,
    kpi_id          TEXT NOT NULL,
    detected_at     TIMESTAMPTZ NOT NULL,
    severity        TEXT CHECK (severity IN ('P1', 'P2', 'P3')) NOT NULL,
    status          TEXT CHECK (status IN (
                        'detected', 'investigating', 'awaiting_approval',
                        'remediating', 'verifying', 'resolved', 'failed'
                    )) NOT NULL DEFAULT 'detected',
    root_cause      TEXT,
    confidence_score NUMERIC(5,2),
    recommended_action TEXT,
    approval_tier   TEXT CHECK (approval_tier IN ('auto', 'manual', 'report_only')),
    resolved_at     TIMESTAMPTZ,
    mttd_seconds    INTEGER,
    mttr_seconds    INTEGER,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_incidents_kpi_id ON incidents (kpi_id);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents (status);
CREATE INDEX IF NOT EXISTS idx_incidents_detected_at ON incidents (detected_at);

CREATE TABLE IF NOT EXISTS remediation_actions (
    id              SERIAL PRIMARY KEY,
    incident_id     INTEGER REFERENCES incidents(id) ON DELETE CASCADE,
    action_type     TEXT CHECK (action_type IN ('rollback', 'restart', 'scale', 'config_patch')) NOT NULL,
    executed_at     TIMESTAMPTZ DEFAULT now(),
    success         BOOLEAN,
    details         JSONB
);
