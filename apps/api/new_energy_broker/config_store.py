from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .schemas import ApiProviderConfig


ROOT_DIR = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT_DIR / ".runtime" / "model_api_settings.json"


def load_api_config() -> ApiProviderConfig:
    if not CONFIG_PATH.exists():
        return ApiProviderConfig()
    try:
        return ApiProviderConfig.model_validate_json(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ApiProviderConfig()


def save_api_config(config: ApiProviderConfig) -> ApiProviderConfig:
    next_config = config.model_copy(
        update={
            "configured": bool(config.apiKey and config.model),
            "demoMode": False,
            "savedAt": datetime.now(timezone.utc).isoformat(),
        }
    )
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(next_config.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    return next_config


def save_demo_mode(config: ApiProviderConfig | None = None) -> ApiProviderConfig:
    base = config or load_api_config()
    next_config = base.model_copy(
        update={
            "configured": False,
            "demoMode": True,
            "savedAt": datetime.now(timezone.utc).isoformat(),
        }
    )
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(next_config.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    return next_config
