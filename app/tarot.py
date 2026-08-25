"""22 Major Arcana, local interpretation engine, optional OpenAI enrichment."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

MAJOR_ARCANA: list[dict[str, Any]] = [
    {
        "id": 0,
        "name": "The Fool",
        "element": "Air",
        "keywords": ["beginnings", "leap", "trust"],
        "traits": ["adventurous", "open-hearted", "unburdened"],
        "love": "A first spark that asks for courage more than certainty.",
    },
    {
        "id": 1,
        "name": "The Magician",
        "element": "Air",
        "keywords": ["will", "manifestation", "skill"],
        "traits": ["charismatic", "focused", "resourceful"],
        "love": "Chemistry you can actually shape into something real.",
    },
    {
        "id": 2,
        "name": "The High Priestess",
        "element": "Water",
        "keywords": ["intuition", "mystery", "inner knowing"],
        "traits": ["intuitive", "private", "magnetic"],
        "love": "Attraction that lives in glances, dreams, and timing.",
    },
    {
        "id": 3,
        "name": "The Empress",
        "element": "Earth",
        "keywords": ["nurture", "sensuality", "abundance"],
        "traits": ["warm", "sensual", "creative"],
        "love": "A love that wants to be fed, held, and grown.",
    },
    {
        "id": 4,
        "name": "The Emperor",
        "element": "Fire",
        "keywords": ["structure", "protection", "authority"],
        "traits": ["steady", "protective", "decisive"],
        "love": "Safety as a love language — a backbone for passion.",
    },
    {
        "id": 5,
        "name": "The Hierophant",
        "element": "Earth",
        "keywords": ["tradition", "vows", "shared meaning"],
        "traits": ["loyal", "principled", "devotional"],
        "love": "A bond that wants ritual, shared values, and lasting form.",
    },
    {
        "id": 6,
        "name": "The Lovers",
        "element": "Air",
        "keywords": ["choice", "union", "alignment"],
        "traits": ["romantic", "discerning", "devoted"],
        "love": "A fork in the path: choose with the heart, not the crowd.",
    },
    {
        "id": 7,
        "name": "The Chariot",
        "element": "Water",
        "keywords": ["drive", "victory", "direction"],
        "traits": ["determined", "ambitious", "self-possessed"],
        "love": "Momentum — two wills learning to move as one.",
    },
    {
        "id": 8,
        "name": "Strength",
        "element": "Fire",
        "keywords": ["soft power", "patience", "heart"],
        "traits": ["gentle", "brave", "compassionate"],
        "love": "Passion tamed by kindness, not by distance.",
    },
    {
        "id": 9,
        "name": "The Hermit",
        "element": "Earth",
        "keywords": ["solitude", "wisdom", "inner light"],
        "traits": ["reflective", "independent", "sincere"],
        "love": "Connection after self-knowledge — quality over noise.",
    },
    {
        "id": 10,
        "name": "Wheel of Fortune",
        "element": "Fire",
        "keywords": ["fate", "cycles", "turning point"],
        "traits": ["adaptable", "optimistic", "destined"],
        "love": "A meeting that feels timed by something larger.",
    },
    {
        "id": 11,
        "name": "Justice",
        "element": "Air",
        "keywords": ["truth", "balance", "accountability"],
        "traits": ["fair", "clear", "honest"],
        "love": "Equals at the table — no games, only truth.",
    },
    {
        "id": 12,
        "name": "The Hanged Man",
        "element": "Water",
        "keywords": ["pause", "surrender", "new angle"],
        "traits": ["patient", "philosophical", "unconventional"],
        "love": "Letting go of the old script so a new one can arrive.",
    },
    {
        "id": 13,
        "name": "Death",
        "element": "Water",
        "keywords": ["ending", "rebirth", "shedding"],
        "traits": ["transformative", "honest", "renewing"],
        "love": "What must end so a truer intimacy can begin.",
    },
    {
        "id": 14,
        "name": "Temperance",
        "element": "Fire",
        "keywords": ["alchemy", "blend", "healing"],
        "traits": ["balanced", "healing", "integrative"],
        "love": "Two chemistries mixed until they become a third thing.",
    },
    {
        "id": 15,
        "name": "The Devil",
        "element": "Earth",
        "keywords": ["desire", "shadow", "attachment"],
        "traits": ["intense", "sensual", "provocative"],
        "love": "Raw pull — magnetism that asks to be made conscious.",
    },
    {
        "id": 16,
        "name": "The Tower",
        "element": "Fire",
        "keywords": ["rupture", "revelation", "liberation"],
        "traits": ["catalytic", "truth-telling", "liberating"],
        "love": "A strike of honesty that clears the ground for real fire.",
    },
    {
        "id": 17,
        "name": "The Star",
        "element": "Air",
        "keywords": ["hope", "healing", "guidance"],
        "traits": ["hopeful", "authentic", "inspiring"],
        "love": "Soft light after storm — a love that restores faith.",
    },
    {
        "id": 18,
        "name": "The Moon",
        "element": "Water",
        "keywords": ["dreams", "illusion", "depth"],
        "traits": ["imaginative", "emotional", "enigmatic"],
        "love": "Night-time chemistry — feelings that speak in symbols.",
    },
    {
        "id": 19,
        "name": "The Sun",
        "element": "Fire",
        "keywords": ["joy", "clarity", "vitality"],
        "traits": ["radiant", "playful", "generous"],
        "love": "Warmth without hiding — joy as the point of the union.",
    },
    {
        "id": 20,
        "name": "Judgement",
        "element": "Fire",
        "keywords": ["calling", "awakening", "absolution"],
        "traits": ["awakened", "purposeful", "forgiving"],
        "love": "A second chance that feels like destiny answering.",
    },
    {
        "id": 21,
        "name": "The World",
        "element": "Earth",
        "keywords": ["completion", "wholeness", "belonging"],
        "traits": ["complete", "cosmopolitan", "fulfilled"],
        "love": "A sense of arrival — two lives clicking into a larger map.",
    },
]

CARD_BY_ID = {c["id"]: c for c in MAJOR_ARCANA}

POSITIONS = ("past", "present", "future")
POSITION_LABELS = {
    "past": "Past Energy / Block",
    "present": "Present Vibe",
    "future": "Future Love Potential",
}

ARCHETYPE_BY_ELEMENT = {
    "Fire": "The Alchemist of Passion",
    "Water": "The Seeker of Depth",
    "Air": "The Messenger of Choice",
    "Earth": "The Keeper of Devotion",
}

ELEMENT_SCORE = {
    ("Fire", "Fire"): 88,
    ("Fire", "Air"): 92,
    ("Fire", "Earth"): 74,
    ("Fire", "Water"): 70,
    ("Water", "Water"): 90,
    ("Water", "Earth"): 91,
    ("Water", "Air"): 76,
    ("Air", "Air"): 86,
    ("Air", "Earth"): 72,
    ("Earth", "Earth"): 89,
}


def card_payload(card_id: int) -> dict[str, Any]:
    card = CARD_BY_ID[card_id]
    return {
        "id": card["id"],
        "name": card["name"],
        "element": card["element"],
        "keywords": card["keywords"],
        "traits": card["traits"],
        "love": card["love"],
    }


def dominant_element(cards: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for card in cards:
        counts[card["element"]] = counts.get(card["element"], 0) + 1
    return max(counts, key=counts.get)


def interpret_spread(card_ids: list[int]) -> dict[str, Any]:
    if len(card_ids) != 3 or len(set(card_ids)) != 3:
        raise ValueError("Select exactly three distinct Major Arcana cards.")
    for cid in card_ids:
        if cid not in CARD_BY_ID:
            raise ValueError(f"Unknown card id: {cid}")

    drawn = [card_payload(cid) for cid in card_ids]
    element = dominant_element(drawn)
    traits = []
    for card in drawn:
        for trait in card["traits"]:
            if trait not in traits:
                traits.append(trait)

    archetype = ARCHETYPE_BY_ELEMENT[element]
    if drawn[2]["id"] in (6, 14, 21):
        archetype = "The Weaver of Destined Bonds"
    elif drawn[0]["id"] in (13, 16, 15):
        archetype = "The Phoenix of Desire"
    elif drawn[1]["id"] in (2, 18, 9):
        archetype = "The Oracle of Intimacy"

    spread = []
    for pos, card in zip(POSITIONS, drawn):
        spread.append(
            {
                "position": pos,
                "label": POSITION_LABELS[pos],
                "card": card,
            }
        )

    past, present, future = drawn
    interpretation = (
        f"Your {POSITION_LABELS['past'].lower()} is {past['name']} — {past['love']} "
        f"In the present, {present['name']} colors your field: {present['love']} "
        f"Ahead, {future['name']} opens the path: {future['love']}"
    )
    profile = (
        f"You arrive as {archetype}, an {element.lower()} signature woven from "
        f"{past['name']}, {present['name']}, and {future['name']}. "
        f"Those who match you will feel {traits[0]} heat meeting {traits[1]} grace — "
        f"a romance that prefers truth over performance."
    )

    energy_signature = {
        "archetype": archetype,
        "element": element,
        "traits": traits[:6],
        "card_ids": card_ids,
        "card_names": [c["name"] for c in drawn],
    }
    last_spread = {
        "cards": spread,
        "interpretation": interpretation,
        "profile": profile,
        "source": "local-oracle",
    }

    enriched = _maybe_llm_interpret(energy_signature, last_spread)
    return enriched


def _maybe_llm_interpret(signature: dict[str, Any], spread: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return {"energy_signature": signature, "last_spread": spread}

    prompt = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "temperature": 0.8,
        "max_tokens": 400,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a romantic-mystical tarot interpreter for a dating app. "
                    "Reply JSON only with keys: archetype, profile, interpretation. "
                    "Keep profile under 80 words. Tone: sleek, intimate, never cheesy."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "spread": spread["cards"],
                        "fallback_archetype": signature["archetype"],
                        "element": signature["element"],
                    }
                ),
            },
        ],
    }
    try:
        body = json.dumps(prompt).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        parsed = json.loads(text)
        signature["archetype"] = parsed.get("archetype", signature["archetype"])
        spread["profile"] = parsed.get("profile", spread["profile"])
        spread["interpretation"] = parsed.get("interpretation", spread["interpretation"])
        spread["source"] = "openai"
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError, ValueError):
        pass
    return {"energy_signature": signature, "last_spread": spread}


def compatibility(a: dict[str, Any], b: dict[str, Any]) -> tuple[float, str]:
    el_a = a.get("element", "Air")
    el_b = b.get("element", "Air")
    key = tuple(sorted((el_a, el_b)))
    base = float(ELEMENT_SCORE.get(key, 75))

    cards_a = set(a.get("card_ids") or [])
    cards_b = set(b.get("card_ids") or [])
    overlap = len(cards_a & cards_b)
    if overlap:
        base -= overlap * 4
    else:
        base += 6

    lovers = {6, 14, 21}
    if cards_a & lovers and cards_b & lovers:
        base += 5
    shadow = {13, 15, 16, 18}
    if cards_a & shadow and cards_b & {17, 19, 8, 14}:
        base += 4

    score = max(62.0, min(99.0, round(base, 1)))
    reason = (
        f"{a.get('archetype', 'Your field')} ( {el_a} ) meets "
        f"{b.get('archetype', 'their field')} ( {el_b} ). "
        f"Their cards do not copy yours — they complete the missing polarity, "
        f"so the pull feels fated rather than familiar."
    )
    llm_reason = _maybe_llm_compat(a, b, score)
    return score, llm_reason or reason


def _maybe_llm_compat(a: dict[str, Any], b: dict[str, Any], score: float) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    prompt = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "temperature": 0.7,
        "max_tokens": 160,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Write exactly two sentences of Cosmic Connection Insight for a dating match. "
                    "Romantic-mystical, specific to the cards, no hashtags."
                ),
            },
            {
                "role": "user",
                "content": json.dumps({"a": a, "b": b, "score": score}),
            },
        ],
    }
    try:
        body = json.dumps(prompt).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError, ValueError):
        return None
