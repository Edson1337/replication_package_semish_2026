"""Centralized configuration loader.

Loads structural config from config.yaml and resolves ${VAR} placeholders from .env.
"""
import os
import re
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_config = None


def _resolve_env_vars(value):
    """Resolve ${VAR} placeholders with values from .env / environment."""
    if isinstance(value, str):
        return re.sub(r'\$\{(\w+)\}', lambda m: os.getenv(m.group(1), ''), value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


def _load_yaml() -> dict:
    """Load config.yaml and resolve all ${VAR} placeholders."""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        return {}
    with open(config_path, 'r', encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    return _resolve_env_vars(raw)


def get_config() -> dict:
    """Get the full config (cached after first load)."""
    global _config
    if _config is None:
        _config = _load_yaml()
    return _config


# --- Story Source ---
def get_story_source() -> str:
    return get_config().get("story_source", "json")


# --- Qdrant ---
def get_qdrant_url() -> str:
    return get_config().get("qdrant", {}).get("url", "http://localhost:6333")


def get_qdrant_api_key() -> str | None:
    val = get_config().get("qdrant", {}).get("api_key", "")
    return val or None


def get_collection_names() -> dict:
    defaults = {
        "user_stories": "user_stories",
        "nfrs": "non_functional_requirements",
        "test_scenarios": "test_scenarios",
    }
    return get_config().get("qdrant", {}).get("collections", defaults)


# --- LLM ---
def get_llm_config() -> dict:
    cfg = get_config().get("llm", {})
    base_url = cfg.get("base_url", "")
    return {
        "model": cfg.get("model", "gemini-1.5-flash"),
        "temperature": cfg.get("temperature", 0.7),
        "api_key": cfg.get("api_key", ""),
        "base_url": base_url if base_url else None,
    }


# --- Embedding ---
def get_embedding_model() -> str:
    return get_config().get("embedding", {}).get("model", "all-MiniLM-L6-v2")


# --- Providers ---
def get_jira_config() -> dict:
    cfg = get_config().get("providers", {}).get("jira", {})
    return {
        "url": cfg.get("url", ""),
        "email": cfg.get("email", ""),
        "api_token": cfg.get("api_token", ""),
        "project_key": cfg.get("project_key", ""),
        "issue_type": cfg.get("issue_type", "Story"),
    }
