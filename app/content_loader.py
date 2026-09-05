"""Load published card copy from the content vault (or samples for contractors)."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VAULT_PUBLISHED = ROOT / "content" / "vault" / "published"
SAMPLES = ROOT / "content" / "samples"

SECRET_KEYS = ("love_long", "balanced", "unbalanced", "questions", "green_path")


def _content_dir() -> Path:
    override = os.getenv("AETHER_CONTENT_PATH")
    if override:
        return Path(override)
    if (VAULT_PUBLISHED / "cards.he.json").exists():
        return VAULT_PUBLISHED
    return SAMPLES


@lru_cache(maxsize=4)
def _load_lang(lang: str) -> dict[str, Any]:
    lang = "he" if str(lang).lower().startswith("he") else "en"
    base = _content_dir()
    # published uses cards.he.json; samples may use cards.sample.json
    candidates = [
        base / f"cards.{lang}.json",
        base / "cards.sample.json",
        base / f"cards_{lang}.json",
    ]
    for path in candidates:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            cards = data.get("cards") or {}
            # sample file is a list
            if isinstance(cards, list):
                return {str(c["id"]): c for c in cards}
            if isinstance(data, list):
                return {str(c["id"]): c for c in data}
            return {str(k): v for k, v in cards.items()}
    return {}


def published_card(card_id: int, lang: str = "en") -> dict[str, Any]:
    """Return published editorial fields for one card (may be empty)."""
    return dict(_load_lang(lang).get(str(card_id) or card_id, {}) or {})


def merge_published(payload: dict[str, Any], card_id: int, lang: str) -> dict[str, Any]:
    """Overlay published vault fields onto a public card payload."""
    pub = published_card(card_id, lang)
    if not pub:
        return payload
    if pub.get("love"):
        payload["love"] = pub["love"]
    if pub.get("traits"):
        payload["traits"] = list(pub["traits"])
    for key in SECRET_KEYS:
        if pub.get(key):
            payload[key] = pub[key]
    return payload


def clear_content_cache() -> None:
    _load_lang.cache_clear()
