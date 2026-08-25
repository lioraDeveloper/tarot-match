"""Matchmaking: preference filters + energetic compatibility scoring."""

from __future__ import annotations

from typing import Any

from app import db
from app.tarot import compatibility


def find_best_match(user: dict[str, Any]) -> dict[str, Any] | None:
    existing = db.active_match_for(user["id"])
    if existing:
        return enrich_match(existing, user["id"])

    if not user.get("energy_signature"):
        return None

    candidates = db.list_candidates(user)
    if not candidates:
        return None

    scored: list[tuple[float, str, dict[str, Any]]] = []
    for other in candidates:
        score, reason = compatibility(user["energy_signature"], other["energy_signature"])
        scored.append((score, reason, other))
    scored.sort(key=lambda item: item[0], reverse=True)
    score, reason, other = scored[0]
    row = db.create_match(user["id"], other["id"], score, reason)
    return enrich_match(row, user["id"])


def enrich_match(row: dict[str, Any], viewer_id: str) -> dict[str, Any]:
    other_id = row["user_id_2"] if row["user_id_1"] == viewer_id else row["user_id_1"]
    other = db.get_user(other_id)
    return {
        "id": row["id"],
        "compatibility_score": row["compatibility_score"],
        "mystical_reasoning": row["mystical_reasoning"],
        "status": row["status"],
        "created_at": row["created_at"],
        "partner": {
            "id": other["id"],
            "name": other["name"],
            "age": other["age"],
            "gender": other["gender"],
            "bio": other["bio"],
            "energy_signature": other["energy_signature"],
        },
    }
