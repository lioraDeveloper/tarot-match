"""Matchmaking: preference filters + energetic compatibility scoring."""

from __future__ import annotations

from typing import Any

from app import db
from app.bot import localize_bot
from app.tarot import compatibility, localize_user


def _public_partner(other: dict[str, Any], lang: str) -> dict[str, Any]:
    other = localize_bot(other, lang)
    other_l = localize_user(other, lang) if other else other
    return {
        "id": other_l["id"],
        "name": other_l["name"],
        "age": other_l["age"],
        "gender": other_l["gender"],
        "bio": other_l["bio"],
        "photo_url": other_l.get("photo_url"),
        "is_bot": bool(other_l.get("is_bot")),
        "energy_signature": other_l.get("energy_signature"),
    }


def find_best_match(user: dict[str, Any], lang: str = "en") -> dict[str, Any] | None:
    """Create a chat with the strongest unused candidate. Existing chats stay open."""
    if not user.get("energy_signature"):
        return None

    candidates = db.list_candidates(user, exclude_existing=True)
    humans = [c for c in candidates if not c.get("is_bot")]
    pool = humans or candidates
    if not pool:
        return None

    scored: list[tuple[float, str, dict[str, Any]]] = []
    for other in pool:
        score, reason = compatibility(user["energy_signature"], other["energy_signature"], lang="en")
        scored.append((score, reason, other))
    scored.sort(key=lambda item: item[0], reverse=True)
    score, reason, other = scored[0]
    row = db.get_or_create_match(user["id"], other["id"], score, reason)
    return enrich_match(row, user["id"], lang)


def open_match(user: dict[str, Any], other_id: str, lang: str = "en") -> dict[str, Any] | None:
    if other_id == user["id"]:
        return None
    other = db.get_user(other_id)
    if not other or not other.get("energy_signature"):
        return None
    blocked = db.unmatched_partner_ids(user["id"])
    if other_id in blocked and not other.get("is_bot"):
        return None
    if not other.get("is_bot") and not db.passes_filters(user, other):
        return None
    score, reason = (80.0, "")
    if user.get("energy_signature") and other.get("energy_signature"):
        score, reason = compatibility(user["energy_signature"], other["energy_signature"], lang="en")
    row = db.get_or_create_match(user["id"], other["id"], score, reason)
    if other.get("is_bot"):
        from app.bot import ensure_bot_conversation

        ensure_bot_conversation(user, lang)
        row = db.find_match_between(user["id"], other["id"]) or row
    return enrich_match(row, user["id"], lang)


def discover_people(user: dict[str, Any], lang: str = "en") -> list[dict[str, Any]]:
    active_ids = db.active_partner_ids(user["id"])
    people: list[dict[str, Any]] = []
    for other in db.list_discoverable(user):
        if user.get("energy_signature") and other.get("energy_signature"):
            score, reason = compatibility(user["energy_signature"], other["energy_signature"], lang=lang)
        else:
            score, reason = 72.0, ""
        existing = db.find_match_between(user["id"], other["id"])
        match_id = existing["id"] if existing and existing.get("status") == "active" else None
        people.append(
            {
                "user": _public_partner(other, lang),
                "compatibility_score": score,
                "mystical_reasoning": reason,
                "match_id": match_id,
                "already_chatting": other["id"] in active_ids,
            }
        )
    people.sort(key=lambda item: (0 if item["user"].get("is_bot") else 1, -item["compatibility_score"]))
    return people


def enrich_match(row: dict[str, Any], viewer_id: str, lang: str = "en") -> dict[str, Any]:
    other_id = row["user_id_2"] if row["user_id_1"] == viewer_id else row["user_id_1"]
    other = db.get_user(other_id)
    viewer = db.get_user(viewer_id)
    other = localize_bot(other, lang) if other else other
    viewer_l = localize_user(viewer, lang) if viewer else viewer
    other_l = localize_user(other, lang) if other else other
    reasoning = row["mystical_reasoning"]
    score = row["compatibility_score"]
    if viewer_l and other_l and viewer_l.get("energy_signature") and other_l.get("energy_signature"):
        score, reasoning = compatibility(viewer_l["energy_signature"], other_l["energy_signature"], lang=lang)
    last = db.last_message(row["id"])
    preview = ""
    if last:
        preview = last.get("content") or ("📷" if last.get("image_url") else "")
    return {
        "id": row["id"],
        "compatibility_score": score,
        "mystical_reasoning": reasoning,
        "status": row["status"],
        "created_at": row["created_at"],
        "unread": db.unread_count(row["id"], viewer_id),
        "last_message": last,
        "last_preview": preview,
        "partner": _public_partner(other_l, lang) if other_l else None,
    }


def list_inbox(user: dict[str, Any], lang: str = "en") -> list[dict[str, Any]]:
    rows = db.list_active_matches(user["id"])
    items = [enrich_match(row, user["id"], lang) for row in rows]
    items.sort(
        key=lambda item: (item.get("last_message") or {}).get("timestamp") or item.get("created_at") or "",
        reverse=True,
    )
    return items
