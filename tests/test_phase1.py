"""
Phase 1 tests - run with: pytest tests/test_phase1.py -v
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


def test_config_loads():
    from config.llm_client import _load_config
    cfg = _load_config()
    assert "llm" in cfg
    assert "reasoning" in cfg["llm"]["models"]
    assert "fast" in cfg["llm"]["models"]


def test_llm_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from config.llm_client import LLMClient
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        LLMClient(agent_name="rca")


def test_llm_client_routes_to_correct_model(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-test-key")
    from config.llm_client import LLMClient

    rca = LLMClient(agent_name="rca")
    assert rca.model_name == "claude-sonnet-4-6"

    summarizer = LLMClient(agent_name="rag_summarizer")
    assert summarizer.model_name == "claude-haiku-4-5-20251001"


def test_llm_client_unknown_agent_falls_back_to_reasoning(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-test-key")
    from config.llm_client import LLMClient

    unknown = LLMClient(agent_name="some_future_agent")
    assert unknown.model_name == "claude-sonnet-4-6"


def test_complete_json_strips_markdown_fences(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-test-key")
    from config.llm_client import LLMClient

    llm = LLMClient(agent_name="rca")
    llm.complete = lambda prompt, system=None: '```json\n{"root_cause": "deploy", "confidence": 91}\n```'

    result = llm.complete_json("dummy prompt")
    assert result == {"root_cause": "deploy", "confidence": 91}


def test_postgres_client_default_dsn_format():
    from db.postgres_client import DEFAULT_DSN
    assert DEFAULT_DSN.startswith("postgresql+psycopg2://")


def test_mongo_client_default_uri_format():
    from db.mongo_client import DEFAULT_URI
    assert DEFAULT_URI.startswith("mongodb://")


def test_dataset_parquet_files_exist_if_explored():
    data_dir = Path(__file__).resolve().parent.parent / "data"
    train_parquet = data_dir / "train.parquet"
    if train_parquet.exists():
        import pandas as pd
        df = pd.read_parquet(train_parquet)
        assert "KPI ID" in df.columns
        assert "label" in df.columns
        assert df["label"].isin([0, 1]).all()
    else:
        pytest.skip("Run scripts/explore_dataset.py first to generate parquet files")
