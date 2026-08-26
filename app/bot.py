"""Trial Oracle bot — always-on practice chat."""

from __future__ import annotations

import random
from typing import Any

from app import db
from app.auth import hash_password
from app.tarot import interpret_spread

BOT_EMAIL = db.BOT_EMAIL
BOT_PHOTO = "/static/uploads/oracle.svg"
BOT_CARDS = [2, 18, 17]  # High Priestess, Moon, Star

BOT_NAME = {"en": "Oracle", "he": "אורקל"}
BOT_BIO = {
    "en": "A practice chat so you can see how messaging feels. Mystical, a little nosy, always available.",
    "he": "צ׳אט לניסיון — כדי לראות איך זה נראה. קצת מיסטי, קצת סקרן, תמיד פה.",
}

WELCOME = {
    "en": "Hey — I'm Oracle. Think of this as a practice chat while you meet people. What's on your mind?",
    "he": "היי, כאן אורקל. זה צ׳אט לניסיון בזמן שמכירים אנשים אמיתיים. מה עובר לך בראש?",
}

REPLIES_EN = [
    "I felt that. Tell me more.",
    "That's a strong opener. What are you hoping to find here?",
    "The cards like honesty. Keep going.",
    "Noted. And what would a good match actually change in your week?",
    "Soft, but clear. That's attractive.",
    "Mmm. Are you more midnight talks or Sunday markets?",
    "Say the thing you usually edit out.",
    "I'm here. No performance required.",
    "That pull is real. Who do you become around someone you like?",
    "Short and true beats clever. You did fine.",
]

REPLIES_HE = [
    "הרגשתי את זה. אפשר להרחיב?",
    "פתיחה חזקה. מה בעצם מחפשים פה?",
    "כנות כזאת עובדת. ממשיכים.",
    "אוקיי. ומה שידוך טוב היה משנה בשבוע שלך?",
    "עדין, אבל ברור. זה מושך.",
    "שיחות אחרי חצות, או שוק בבוקר?",
    "לכתוב את מה שבדרך כלל מוחקים לפני השליחה.",
    "אני פה. בלי הצגה.",
    "יש פה משיכה אמיתית. איך זה ליד מישהו שמושך אותך?",
    "קצר ואמיתי עדיף על חכם. היה בסדר.",
]

# Last HE reply still has masculine "אתה". Let me use a more neutral one:
# "איך זה ליד מישהו שמושך אותך?"

IMAGE_REPLIES = {
    "en": [
        "Good photo. The lighting does you a favor.",
        "I see you. Want to add a line with it?",
        "That image has a mood. Tell me the story behind it.",
    ],
    "he": [
        "תמונה טובה. האור עובד לטובתך.",
        "ראיתי. רוצה להוסיף משפט ליד?",
        "יש לתמונה מצב רוח. מה הסיפור מאחוריה?",
    ],
}


def localize_bot(user: dict[str, Any], lang: str) -> dict[str, Any]:
    if not user or not user.get("is_bot"):
        return user
    out = dict(user)
    out["name"] = BOT_NAME.get(lang, BOT_NAME["en"])
    out["bio"] = BOT_BIO.get(lang, BOT_BIO["en"])
    if not out.get("photo_url"):
        out["photo_url"] = BOT_PHOTO
    return out


def ensure_bot_user() -> dict[str, Any]:
    existing = db.get_bot_user()
    if existing:
        if not existing.get("photo_url"):
            db.set_user_photo(existing["id"], BOT_PHOTO)
            existing = db.get_bot_user()
        return existing
    reading = interpret_spread(BOT_CARDS, lang="en")
    return db.create_user(
        email=BOT_EMAIL,
        password_hash=hash_password("oracle-not-for-login"),
        name="Oracle",
        birth_date="1996-06-21",
        gender="nonbinary",
        looking_for_gender=["any"],
        min_age_preference=18,
        max_age_preference=99,
        bio=BOT_BIO["en"],
        is_premium=True,
        energy_signature=reading["energy_signature"],
        last_spread=reading["last_spread"],
        photo_url=BOT_PHOTO,
        is_bot=True,
    )


def bot_reply_text(lang: str, *, has_image: bool = False, content: str = "") -> str:
    if has_image:
        return random.choice(IMAGE_REPLIES["he" if lang == "he" else "en"])
    pool = REPLIES_HE if lang == "he" else REPLIES_EN
    if content:
        idx = sum(ord(c) for c in content) % len(pool)
        return pool[idx]
    return random.choice(pool)


def ensure_bot_conversation(user: dict[str, Any], lang: str = "en") -> dict[str, Any] | None:
    if not user or user.get("is_bot"):
        return None
    bot = ensure_bot_user()
    from app.tarot import compatibility

    score, reason = (88.0, "")
    if user.get("energy_signature") and bot.get("energy_signature"):
        score, reason = compatibility(user["energy_signature"], bot["energy_signature"], lang="en")
    else:
        reason = "Practice chat with Oracle."
    match = db.get_or_create_match(user["id"], bot["id"], score, reason)
    if not db.list_messages(match["id"]):
        db.add_message(match["id"], bot["id"], WELCOME["he" if lang == "he" else "en"])
    return match
