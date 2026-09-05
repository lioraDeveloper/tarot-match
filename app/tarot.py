"""22 Major Arcana, local interpretation engine, optional OpenAI enrichment."""

from __future__ import annotations

import hashlib
import json
import os
import random
import urllib.error
import urllib.request
from typing import Any

from app.content_loader import merge_published

# Public skeleton only. Secret / editorial copy lives in content/vault/published
# (source + drafts are for study; app never auto-loads them).
MAJOR_ARCANA: list[dict[str, Any]] = [
    {
        "id": 0,
        "name": "The Fool",
        "element": "Air",
        "keywords": ["beginnings", "leap", "trust"],
        "traits": ["adventurous", "open-hearted", "unburdened"],
        "love": "An open beginning.",
    },
    {
        "id": 1,
        "name": "The Magician",
        "element": "Air",
        "keywords": ["will", "manifestation", "skill"],
        "traits": ["charismatic", "focused", "creative"],
        "love": "Chemistry you can shape.",
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
        "love": "A love that wants to be tended — held, fed, and grown.",
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
    "en": {
        "past": "Past",
        "present": "Present",
        "future": "Future",
    },
    "he": {
        "past": "עבר",
        "present": "הווה",
        "future": "עתיד",
    },
}

UNION_POSITIONS = ("bond", "lesson", "path")
UNION_POSITION_LABELS = {
    "en": {
        "bond": "Our bond",
        "lesson": "What we learn together",
        "path": "Where this leads",
    },
    "he": {
        "bond": "החיבור שלנו",
        "lesson": "מה נלמד יחד",
        "path": "לאן זה מוביל",
    },
}

ARCHETYPE_BY_ELEMENT = {
    "en": {
        "Fire": "Fire · Passion",
        "Water": "Water · Depth",
        "Air": "Air · Choice",
        "Earth": "Earth · Devotion",
        "weaver": "The Weaver",
        "phoenix": "The Phoenix",
        "oracle": "The Oracle",
    },
    "he": {
        "Fire": "אש · תשוקה",
        "Water": "מים · עומק",
        "Air": "אוויר · בחירה",
        "Earth": "אדמה · מסירות",
        "weaver": "האורג",
        "phoenix": "עוף החול",
        "oracle": "האורקל",
    },
}

ELEMENT_HE = {"Fire": "אש", "Water": "מים", "Air": "אוויר", "Earth": "אדמה"}

# Public Hebrew skeleton only. Editorial copy (love / green_path / long) loads from vault published.
# Public Hebrew skeleton only. Editorial copy loads from content/vault/published.
HE_CARDS = {
    0: {"name": "השוטה", "love": "התחלה פתוחה.", "traits": ["לב פתוח", "ספונטני", "מחפש חופש"]},
    1: {"name": "הקוסם", "love": "כימיה שאפשר לעצב.", "traits": ["כריזמטי", "ממוקד", "יוצר"]},
    2: {"name": "הכהנת הגדולה", "love": "משיכה שחיה במבטים, בחלומות ובתזמון.", "traits": ["אינטואיטיבי", "שמור", "מגנטי"]},
    3: {"name": "הקיסרית", "love": "אהבה שרוצה מגע, חום, ומי שמשקיע.", "traits": ["חמים", "חושני", "יצירתי"]},
    4: {"name": "הקיסר", "love": "ביטחון כשפת אהבה — עמוד שדרה לתשוקה.", "traits": ["יציב", "מגן", "החלטי"]},
    5: {"name": "הכהן הגדול", "love": "קשר שרוצה טקס, ערכים משותפים וצורה שנשארת.", "traits": ["נאמן", "עקרוני", "מסור"]},
    6: {"name": "המאהבים", "love": "צומת בדרך: בחרו בלב, לא בהמון.", "traits": ["רומנטי", "מבחין", "מסור"]},
    7: {"name": "המרכבה", "love": "תנופה — שני רצונות לומדים לנוע כאחד.", "traits": ["נחוש", "שאפתן", "בעל נוכחות"]},
    8: {"name": "העוצמה", "love": "תשוקה שמרוסנת בחסד, לא בריחוק.", "traits": ["עדין", "אמיץ", "רחום"]},
    9: {"name": "הנזיר", "love": "חיבור אחרי היכרות עצמית — איכות מעל רעש.", "traits": ["מהורהר", "עצמאי", "כן"]},
    10: {"name": "גלגל המזל", "love": "מפגש שמרגיש מתואם על ידי משהו גדול יותר.", "traits": ["גמיש", "אופטימי", "ייעודי"]},
    11: {"name": "הצדק", "love": "שווים ליד השולחן — בלי משחקים, רק אמת.", "traits": ["הוגן", "צלול", "ישר"]},
    12: {"name": "התלוי", "love": "לשחרר את התסריט הישן כדי שחדש יוכל להגיע.", "traits": ["סבלני", "פילוסופי", "לא שגרתי"]},
    13: {"name": "המוות", "love": "מה שחייב להסתיים כדי שאינטימיות אמיתית יותר תתחיל.", "traits": ["משנה צורה", "כן", "מחדש"]},
    14: {"name": "המתינות", "love": "שתי כימיות שמתערבבות עד שנוצר משהו חדש.", "traits": ["מאוזן", "מרפא", "משלב"]},
    15: {"name": "השטן", "love": "משיכה גולמית — מגנטיות שמבקשת להפוך למודעת.", "traits": ["עז", "חושני", "מעורר"]},
    16: {"name": "המגדל", "love": "מכת כנות שמפנה קרקע לאש אמיתית.", "traits": ["מזרז", "דובר אמת", "משחרר"]},
    17: {"name": "הכוכב", "love": "אור רך אחרי סערה — אהבה שמחזירה אמון.", "traits": ["מלא תקווה", "אותנטי", "מעורר השראה"]},
    18: {"name": "הירח", "love": "כימיה לילית — רגשות שמדברים בסמלים.", "traits": ["דמיוני", "רגשי", "חידתי"]},
    19: {"name": "השמש", "love": "חום בלי הסתרה — שמחה כנקודת האיחוד.", "traits": ["זוהר", "שובב", "נדיב"]},
    20: {"name": "המשפט", "love": "הזדמנות שנייה שמרגישה כמו תשובה של גורל.", "traits": ["ער", "תכליתי", "סולח"]},
    21: {"name": "העולם", "love": "תחושת הגעה — שני חיים שנכנסים למפה גדולה יותר.", "traits": ["שלם", "קוסמופוליטי", "ממומש"]},
}


def normalize_lang(raw: str | None) -> str:
    if raw and str(raw).lower().startswith("he"):
        return "he"
    return "en"


def card_payload(card_id: int, lang: str = "en") -> dict[str, Any]:
    card = CARD_BY_ID[card_id]
    he = HE_CARDS[card_id]
    if lang == "he":
        payload = {
            "id": card["id"],
            "name": he["name"],
            "element": ELEMENT_HE[card["element"]],
            "element_key": card["element"],
            "keywords": card["keywords"],
            "traits": he["traits"],
            "love": he["love"],
        }
        src = he
    else:
        payload = {
            "id": card["id"],
            "name": card["name"],
            "element": card["element"],
            "element_key": card["element"],
            "keywords": card["keywords"],
            "traits": card["traits"],
            "love": card["love"],
        }
        src = card
    # Editorial copy (short message, green path, long source) from vault published layer.
    return merge_published(payload, card_id, lang)


def dominant_element(cards: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for card in cards:
        key = card.get("element_key") or card["element"]
        counts[key] = counts.get(key, 0) + 1
    return max(counts, key=counts.get)


def interpret_spread(card_ids: list[int], lang: str = "en") -> dict[str, Any]:
    lang = normalize_lang(lang)
    if len(card_ids) != 3 or len(set(card_ids)) != 3:
        raise ValueError(
            "יש לבחור בדיוק שלושה קלפי ארקנה ראשית שונים."
            if lang == "he"
            else "Select exactly three distinct Major Arcana cards."
        )
    for cid in card_ids:
        if cid not in CARD_BY_ID:
            raise ValueError(f"Unknown card id: {cid}")

    drawn = [card_payload(cid, lang) for cid in card_ids]
    element_key = dominant_element(drawn)
    traits = []
    for card in drawn:
        for trait in card["traits"]:
            if trait not in traits:
                traits.append(trait)

    names = ARCHETYPE_BY_ELEMENT[lang]
    archetype = names[element_key]
    if drawn[2]["id"] in (6, 14, 21):
        archetype = names["weaver"]
    elif drawn[0]["id"] in (13, 16, 15):
        archetype = names["phoenix"]
    elif drawn[1]["id"] in (2, 18, 9):
        archetype = names["oracle"]

    labels = POSITION_LABELS[lang]
    spread = []
    for pos, card in zip(POSITIONS, drawn):
        spread.append({"position": pos, "label": labels[pos], "card": card})

    past, present, future = drawn
    if lang == "he":
        interpretation = (
            f"{labels['past']}: {past['name']} — {past['love']} "
            f"{labels['present']}: {present['name']} — {present['love']} "
            f"{labels['future']}: {future['name']} — {future['love']}"
        )
        el_word = ELEMENT_HE[element_key]
        profile = (
            f"הקריאה: {archetype}. יסוד {el_word}, מתוך "
            f"{past['name']}, {present['name']} ו{future['name']}. "
            f"התאמה טובה תרגיש כמו {traits[0]} שנפגש עם {traits[1]} — "
            f"כימיה שמעדיפה כנות על הצגה."
        )
        element_out = el_word
    else:
        interpretation = (
            f"{labels['past']}: {past['name']} — {past['love']} "
            f"{labels['present']}: {present['name']} — {present['love']} "
            f"{labels['future']}: {future['name']} — {future['love']}"
        )
        profile = (
            f"Your reading: {archetype}. An {element_key.lower()} signature from "
            f"{past['name']}, {present['name']}, and {future['name']}. "
            f"A good match will feel {traits[0]} meeting {traits[1]} — "
            f"chemistry that prefers honesty over performance."
        )
        element_out = element_key

    energy_signature = {
        "archetype": archetype,
        "element": element_out,
        "element_key": element_key,
        "traits": traits[:6],
        "card_ids": card_ids,
        "card_names": [c["name"] for c in drawn],
    }
    last_spread = {
        "cards": spread,
        "interpretation": interpretation,
        "profile": profile,
        "source": "local-oracle",
        "lang": lang,
    }

    enriched = _maybe_llm_interpret(energy_signature, last_spread, lang)
    return enriched


def localize_user(user: dict[str, Any], lang: str = "en") -> dict[str, Any]:
    ids = (user.get("energy_signature") or {}).get("card_ids")
    if not ids:
        return user
    reading = interpret_spread(ids, lang=lang)
    out = dict(user)
    out["energy_signature"] = reading["energy_signature"]
    out["last_spread"] = reading["last_spread"]
    return out

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


def _maybe_llm_interpret(signature: dict[str, Any], spread: dict[str, Any], lang: str = "en") -> dict[str, Any]:
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
                    "You are a tarot interpreter for a dating app. "
                    "Reply JSON only with keys: archetype, profile, interpretation. "
                    "Keep profile under 80 words. Tone: mystical but readable, like a real dating product. "
                    "Avoid theatrical words like veil, seekers, or bound. "
                    f"Write in {'Hebrew' if lang == 'he' else 'English'}."
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


def pick_union_card_ids(sig_a: dict[str, Any] | None, sig_b: dict[str, Any] | None, pair_key: str) -> list[int]:
    """Deterministic three-card draw for a pair — same cards for both people."""
    seed = int(hashlib.sha256(pair_key.encode("utf-8")).hexdigest()[:12], 16)
    rng = random.Random(seed)
    a_cards = list((sig_a or {}).get("card_ids") or [])
    b_cards = list((sig_b or {}).get("card_ids") or [])
    chosen: list[int] = []
    if a_cards:
        chosen.append(a_cards[rng.randrange(len(a_cards))])
    if b_cards:
        pool_b = [c for c in b_cards if c not in chosen] or b_cards
        pick = pool_b[rng.randrange(len(pool_b))]
        if pick not in chosen:
            chosen.append(pick)
    bridges = [6, 14, 17, 19, 21, 8, 10, 3]
    while len(chosen) < 3:
        pool = [c for c in bridges if c not in chosen] or [i for i in range(22) if i not in chosen]
        chosen.append(pool[rng.randrange(len(pool))])
    return chosen[:3]


def interpret_union_spread(
    card_ids: list[int],
    name_a: str,
    name_b: str,
    score: float,
    lang: str = "en",
) -> dict[str, Any]:
    """Shared three-card reading both people learn together on a match."""
    lang = normalize_lang(lang)
    if len(card_ids) != 3 or len(set(card_ids)) != 3:
        raise ValueError("Union spread needs three distinct cards.")
    drawn = [card_payload(cid, lang) for cid in card_ids]
    labels = UNION_POSITION_LABELS[lang]
    cards = []
    for pos, card in zip(UNION_POSITIONS, drawn):
        entry = {
            "position": pos,
            "label": labels[pos],
            "card": card,
            "teach": card["love"],
        }
        if card.get("love_long"):
            entry["teach_long"] = card["love_long"]
        if card.get("questions"):
            entry["questions"] = card["questions"]
        if card.get("balanced"):
            entry["balanced"] = card["balanced"]
        if card.get("unbalanced"):
            entry["unbalanced"] = card["unbalanced"]
        if card.get("green_path"):
            entry["green_path"] = card["green_path"]
        cards.append(entry)
    bond, lesson, path = drawn
    # Product v1: short clear message + chemistry % (green path paused).
    if lang == "he":
        message = f"{bond['love']} {lesson['love']} {path['love']}"
        headline = f"{int(round(score))}% כימיה"
        subtitle = "מסר קצר על החיבור שלכם"
    else:
        message = f"{bond['love']} {lesson['love']} {path['love']}"
        headline = f"{int(round(score))}% chemistry"
        subtitle = "A short read on your connection"
    return {
        "card_ids": card_ids,
        "cards": cards,
        "headline": headline,
        "subtitle": subtitle,
        "message": message,
        "score": float(score),
        "lang": lang,
    }


def localize_union_spread(stored: dict[str, Any] | None, name_a: str, name_b: str, score: float, lang: str) -> dict[str, Any] | None:
    if not stored:
        return None
    ids = stored.get("card_ids")
    if not ids or len(ids) != 3:
        return None
    return interpret_union_spread(ids, name_a, name_b, score, lang=lang)


def compatibility(a: dict[str, Any], b: dict[str, Any], lang: str = "en") -> tuple[float, str]:
    lang = normalize_lang(lang)
    el_a = a.get("element_key") or a.get("element", "Air")
    el_b = b.get("element_key") or b.get("element", "Air")
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
    if lang == "he":
        reason = (
            f"החיבור בין {a.get('archetype', 'הקריאה שלך')} "
            f"({ELEMENT_HE.get(el_a, el_a)}) ל{b.get('archetype', 'הקריאה שלהם')} "
            f"({ELEMENT_HE.get(el_b, el_b)}). "
            f"הקלפים לא מעתיקים אחד את השני — הם משלימים. מכאן המשיכה."
        )
    else:
        reason = (
            f"{a.get('archetype', 'Your reading')} ({el_a}) meets "
            f"{b.get('archetype', 'their reading')} ({el_b}). "
            f"The cards don't copy each other — they complement. That's the spark."
        )
    llm_reason = _maybe_llm_compat(a, b, score, lang)
    return score, llm_reason or reason


def _maybe_llm_compat(a: dict[str, Any], b: dict[str, Any], score: float, lang: str = "en") -> str | None:
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
                    "Write exactly two sentences explaining why these two tarot readings match. "
                    "Mystical but readable, specific to the cards, no hashtags, not theatrical. "
                    f"Write in {'Hebrew' if lang == 'he' else 'English'}."
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
