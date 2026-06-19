"""
Phase 1 / Step 5 - Shared LLM wrapper class.

Every agent imports LLMClient instead of calling the Anthropic SDK directly.
This gives you one place to change models, add retry logic, log token usage,
or swap providers later.

Usage:
    from config.llm_client import LLMClient

    llm = LLMClient(agent_name="rca")
    text = llm.complete("Analyze this incident: ...")

    # or for structured JSON output:
    data = llm.complete_json(
        "Return root cause analysis as JSON with keys: root_cause, confidence",
        schema_hint='{"root_cause": "string", "confidence": "number"}'
    )
"""
import json
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


class LLMClient:
    """
    Thin wrapper around langchain-anthropic, configured per-agent from config.yaml.

    agent_name must match a key under `agents:` in config.yaml (e.g. "rca",
    "decision", "rag_summarizer"). Falls back to the "reasoning" model if the
    agent isn't listed.
    """

    def __init__(self, agent_name: str, config: dict | None = None) -> None:
        self.config = config or _load_config()
        self.agent_name = agent_name

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key."
            )

        agent_cfg = self.config.get("agents", {}).get(agent_name, {})
        model_alias = agent_cfg.get("model", "reasoning")
        model_name = self.config["llm"]["models"][model_alias]
        temperature = agent_cfg.get("temperature", self.config["llm"]["default_temperature"])
        max_tokens = self.config["llm"]["default_max_tokens"]

        self.model_name = model_name
        self._llm = ChatAnthropic(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    def complete(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))
        response = self._llm.invoke(messages)
        return response.content

    def complete_json(self, prompt: str, system: str | None = None) -> dict:
        """
        Forces the model to respond with JSON only, then parses it.
        Strips markdown code fences if the model adds them anyway.
        """
        json_system = (
            (system or "")
            + "\n\nRespond with ONLY valid JSON. No preamble, no markdown "
            + "code fences, no explanation before or after the JSON object."
        ).strip()

        raw = self.complete(prompt, system=json_system)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM did not return valid JSON. Raw output:\n{raw}") from exc


if __name__ == "__main__":
    llm = LLMClient(agent_name="rca")
    print(f"Using model: {llm.model_name}")
    result = llm.complete("Say 'connection successful' and nothing else.")
    print("Response:", result)
