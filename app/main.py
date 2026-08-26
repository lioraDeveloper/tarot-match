"""Tarot Matchmaker API + static SPA."""

from __future__ import annotations

import asyncio
import random
import uuid
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import (
    Cookie,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import db
from app.auth import hash_password, read_session, sign_session, verify_password
from app.bot import bot_reply_text, ensure_bot_conversation, ensure_bot_user
from app.matching import discover_people, enrich_match, find_best_match, list_inbox, open_match
from app.seed import seed_demo_users
from app.tarot import HE_CARDS, MAJOR_ARCANA, interpret_spread, localize_user, normalize_lang

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
UPLOADS = STATIC / "uploads"
COOKIE = "tarot_session"
MAX_UPLOAD = 5 * 1024 * 1024

app = FastAPI(title="Tarot Matchmaker", version="0.2.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class RegisterBody(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=80)
    birth_date: str
    gender: str
    looking_for_gender: list[str]
    min_age_preference: int = Field(ge=18, le=99)
    max_age_preference: int = Field(ge=18, le=99)
    bio: str = ""


class LoginBody(BaseModel):
    email: str
    password: str


class PreferencesBody(BaseModel):
    looking_for_gender: list[str] | None = None
    min_age_preference: int | None = Field(default=None, ge=18, le=99)
    max_age_preference: int | None = Field(default=None, ge=18, le=99)
    bio: str | None = None
    name: str | None = None


class DrawBody(BaseModel):
    card_ids: list[int]
    unmatch_previous: bool = False


class SendBody(BaseModel):
    match_id: str
    content: str = Field(min_length=1, max_length=2000)


class OpenBody(BaseModel):
    user_id: str


class UnmatchBody(BaseModel):
    match_id: str


class Hub:
    def __init__(self) -> None:
        self.rooms: dict[str, set[WebSocket]] = {}

    async def join(self, match_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self.rooms.setdefault(match_id, set()).add(ws)

    def leave(self, match_id: str, ws: WebSocket) -> None:
        peers = self.rooms.get(match_id)
        if not peers:
            return
        peers.discard(ws)
        if not peers:
            self.rooms.pop(match_id, None)

    async def broadcast(self, match_id: str, payload: dict[str, Any]) -> None:
        dead = []
        for ws in list(self.rooms.get(match_id, set())):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.leave(match_id, ws)


hub = Hub()


@app.on_event("startup")
def startup() -> None:
    db.init_db()
    UPLOADS.mkdir(parents=True, exist_ok=True)
    seed_demo_users()
    ensure_bot_user()


def lang_of(request: Request, x_lang: str | None = None) -> str:
    return normalize_lang(x_lang or request.headers.get("x-lang"))


ERR = {
    "auth": {"en": "Sign in to continue.", "he": "צריך להתחבר כדי להמשיך."},
    "expired": {"en": "Session expired. Sign in again.", "he": "פג תוקף החיבור. צריך להיכנס שוב."},
    "birth": {"en": "Birth date must be YYYY-MM-DD.", "he": "תאריך לידה בפורמט YYYY-MM-DD."},
    "adult": {"en": "You must be 18 or older to join.", "he": "ההרשמה מותרת מגיל 18 ומעלה."},
    "future": {"en": "Birth date cannot be in the future.", "he": "תאריך לידה לא יכול להיות בעתיד."},
    "range": {"en": "The age range is backwards.", "he": "טווח הגילים הפוך."},
    "email": {"en": "That email already has a profile.", "he": "לאימייל הזה כבר יש פרופיל."},
    "login": {"en": "Email or password did not match.", "he": "אימייל או סיסמה לא נכונים."},
    "thread": {"en": "Chat not found.", "he": "השיחה לא נמצאה."},
    "closed": {"en": "This chat is closed.", "he": "השיחה הזאת נסגרה."},
    "notyours": {"en": "That's not your chat.", "he": "זאת לא השיחה שלך."},
    "nomatch": {
        "en": "No one in your filters right now. Try a wider age range, or check Discover later.",
        "he": "אין כרגע מישהו בפילטרים שלך. אפשר להרחיב את טווח הגילים, או לחזור לגילוי אחר כך.",
    },
    "nophoto": {"en": "Please choose a photo (JPG, PNG, WEBP, or GIF).", "he": "צריך קובץ תמונה (JPG, PNG, WEBP או GIF)."},
    "toobig": {"en": "Photo must be under 5 MB.", "he": "התמונה חייבת להיות עד 5 MB."},
    "noimage": {"en": "Add a message or a photo.", "he": "צריך הודעה או תמונה."},
    "nobody": {"en": "That profile isn't available.", "he": "הפרופיל הזה לא זמין."},
    "needdraw": {"en": "Draw your cards first — then you can browse people.", "he": "קודם מושכים קלפים — ואז אפשר לגלות אנשים."},
}


def fail(code: str, lang: str, status: int) -> None:
    raise HTTPException(status_code=status, detail=ERR[code][lang if lang in ("en", "he") else "en"])


def current_user(session: str | None, lang: str = "en") -> dict[str, Any]:
    user_id = read_session(session)
    if not user_id:
        fail("auth", lang, 401)
    user = db.get_user(user_id)
    if not user:
        fail("expired", lang, 401)
    return user


def assert_adult(birth_date: str, lang: str = "en") -> None:
    try:
        born = date.fromisoformat(birth_date)
    except ValueError as exc:
        fail("birth", lang, 400)
        raise exc
    age = db.age_from_birth(birth_date)
    if age < 18:
        fail("adult", lang, 400)
    if born > date.today():
        fail("future", lang, 400)


def set_session(response: Response, user_id: str) -> None:
    response.set_cookie(
        COOKIE,
        sign_session(user_id),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 14,
    )


def me_payload(user: dict[str, Any], lang: str) -> dict[str, Any]:
    ensure_bot_conversation(user, lang)
    user = localize_user(user, lang)
    inbox = list_inbox(user, lang)
    unread = sum(int(item.get("unread") or 0) for item in inbox)
    latest = inbox[0] if inbox else None
    return {
        "user": user,
        "active_match": latest,
        "conversations": inbox,
        "unread_total": unread,
        "monetization": {
            "is_premium": user["is_premium"],
            "locked": {
                "unlimited_redraws": not user["is_premium"],
                "who_drew_for_you": True,
                "global_filters": True,
            },
        },
    }


def sniff_ext(raw: bytes) -> str | None:
    if raw[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if raw[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return ".webp"
    return None


async def save_image(upload: UploadFile, lang: str) -> str:
    raw = await upload.read()
    if len(raw) > MAX_UPLOAD:
        fail("toobig", lang, 400)
    ext = sniff_ext(raw)
    if not ext:
        fail("nophoto", lang, 400)
    name = f"{uuid.uuid4().hex}{ext}"
    path = UPLOADS / name
    path.write_bytes(raw)
    return f"/static/uploads/{name}"


def assert_chat_access(user: dict[str, Any], match: dict[str, Any] | None, lang: str, *, require_active: bool = False) -> None:
    if not match or user["id"] not in (match["user_id_1"], match["user_id_2"]):
        fail("thread", lang, 404)
    if require_active and match["status"] != "active":
        fail("closed", lang, 404)


async def maybe_bot_reply(match: dict[str, Any], sender_id: str, lang: str, *, has_image: bool, content: str) -> dict[str, Any] | None:
    other_id = match["user_id_2"] if match["user_id_1"] == sender_id else match["user_id_1"]
    other = db.get_user(other_id)
    if not other or not other.get("is_bot"):
        return None
    bot = ensure_bot_user()
    await asyncio.sleep(0.65)
    text = bot_reply_text(lang, has_image=has_image, content=content)
    message = db.add_message(match["id"], bot["id"], text)
    await hub.broadcast(match["id"], {"type": "message", "message": message})
    return message


@app.get("/")
def index() -> FileResponse:
    return FileResponse(
        STATIC / "index.html",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/tarot/deck")
def deck(request: Request, x_lang: str | None = Header(default=None, alias="X-Lang")) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    cards = []
    for c in MAJOR_ARCANA:
        name = HE_CARDS[c["id"]]["name"] if lang == "he" else c["name"]
        cards.append({"id": c["id"], "name": name, "element": c["element"]})
    random.shuffle(cards)
    return {"cards": cards}


@app.post("/api/auth/register")
def register(body: RegisterBody, request: Request, response: Response, x_lang: str | None = Header(default=None, alias="X-Lang")) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    assert_adult(body.birth_date, lang)
    if body.min_age_preference > body.max_age_preference:
        fail("range", lang, 400)
    if db.get_user_by_email(body.email):
        fail("email", lang, 409)
    genders = body.looking_for_gender or ["any"]
    user = db.create_user(
        email=str(body.email),
        password_hash=hash_password(body.password),
        name=body.name,
        birth_date=body.birth_date,
        gender=body.gender,
        looking_for_gender=genders,
        min_age_preference=body.min_age_preference,
        max_age_preference=body.max_age_preference,
        bio=body.bio,
    )
    set_session(response, user["id"])
    ensure_bot_conversation(user, lang)
    return {"user": localize_user(user, lang)}


@app.post("/api/auth/login")
def login(body: LoginBody, request: Request, response: Response, x_lang: str | None = Header(default=None, alias="X-Lang")) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    row = db.get_user_by_email(str(body.email))
    if not row or not verify_password(body.password, row["password_hash"]):
        fail("login", lang, 401)
    user = db.user_from_row(row)
    set_session(response, user["id"])
    ensure_bot_conversation(user, lang)
    return {"user": localize_user(user, lang)}


@app.post("/api/auth/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(COOKIE)
    return {"ok": "signed out"}


@app.get("/api/me")
def me(request: Request, tarot_session: str | None = Cookie(default=None), x_lang: str | None = Header(default=None, alias="X-Lang")) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    user = current_user(tarot_session, lang)
    return me_payload(user, lang)


@app.put("/api/users/preferences")
def preferences(body: PreferencesBody, request: Request, tarot_session: str | None = Cookie(default=None), x_lang: str | None = Header(default=None, alias="X-Lang")) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    user = current_user(tarot_session, lang)
    min_age = body.min_age_preference if body.min_age_preference is not None else user["min_age_preference"]
    max_age = body.max_age_preference if body.max_age_preference is not None else user["max_age_preference"]
    if min_age > max_age:
        fail("range", lang, 400)
    updated = db.update_preferences(
        user["id"],
        looking_for_gender=body.looking_for_gender,
        min_age_preference=body.min_age_preference,
        max_age_preference=body.max_age_preference,
        bio=body.bio,
        name=body.name,
    )
    return {"user": localize_user(updated, lang)}


@app.post("/api/users/photo")
async def upload_photo(
    request: Request,
    tarot_session: str | None = Cookie(default=None),
    x_lang: str | None = Header(default=None, alias="X-Lang"),
    photo: UploadFile = File(...),
) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    user = current_user(tarot_session, lang)
    url = await save_image(photo, lang)
    updated = db.set_user_photo(user["id"], url)
    return {"user": localize_user(updated, lang), "photo_url": url}


@app.post("/api/tarot/draw")
def draw(body: DrawBody, request: Request, tarot_session: str | None = Cookie(default=None), x_lang: str | None = Header(default=None, alias="X-Lang")) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    user = current_user(tarot_session, lang)
    allowed, reason = db.can_redraw(user, lang)
    if user.get("energy_signature") and not allowed:
        raise HTTPException(status_code=402, detail=reason)
    try:
        stored = interpret_spread(body.card_ids, lang="en")
        reading = interpret_spread(body.card_ids, lang=lang)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if body.unmatch_previous:
        db.unmatch_active(user["id"])
    user = db.save_spread(user["id"], stored["energy_signature"], stored["last_spread"])
    ensure_bot_conversation(user, lang)
    match = find_best_match(user, lang)
    return {
        "user": localize_user(user, lang),
        "reading": reading,
        "match": match,
        "conversations": list_inbox(user, lang),
    }


@app.get("/api/match/find")
def match_find(request: Request, tarot_session: str | None = Cookie(default=None), x_lang: str | None = Header(default=None, alias="X-Lang")) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    user = current_user(tarot_session, lang)
    match = find_best_match(user, lang)
    if not match:
        return {"match": None, "detail": ERR["nomatch"][lang]}
    return {"match": match}


@app.get("/api/discover")
def discover(request: Request, tarot_session: str | None = Cookie(default=None), x_lang: str | None = Header(default=None, alias="X-Lang")) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    user = current_user(tarot_session, lang)
    people = discover_people(user, lang)
    return {"people": people}


@app.post("/api/match/open")
def match_open(body: OpenBody, request: Request, tarot_session: str | None = Cookie(default=None), x_lang: str | None = Header(default=None, alias="X-Lang")) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    user = current_user(tarot_session, lang)
    match = open_match(user, body.user_id, lang)
    if not match:
        fail("nobody", lang, 404)
    return {"match": match}


@app.get("/api/conversations")
def conversations(request: Request, tarot_session: str | None = Cookie(default=None), x_lang: str | None = Header(default=None, alias="X-Lang")) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    user = current_user(tarot_session, lang)
    ensure_bot_conversation(user, lang)
    inbox = list_inbox(user, lang)
    return {"conversations": inbox, "unread_total": sum(int(i.get("unread") or 0) for i in inbox)}


@app.get("/api/chat/{match_id}")
def chat_history(match_id: str, request: Request, tarot_session: str | None = Cookie(default=None), x_lang: str | None = Header(default=None, alias="X-Lang")) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    user = current_user(tarot_session, lang)
    match = db.get_match(match_id)
    assert_chat_access(user, match, lang)
    db.mark_read(match_id, user["id"])
    return {
        "match": enrich_match(match, user["id"], lang),
        "messages": db.list_messages(match_id),
    }


@app.post("/api/chat/send")
async def chat_send(body: SendBody, request: Request, tarot_session: str | None = Cookie(default=None), x_lang: str | None = Header(default=None, alias="X-Lang")) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    user = current_user(tarot_session, lang)
    match = db.get_match(body.match_id)
    assert_chat_access(user, match, lang, require_active=True)
    message = db.add_message(body.match_id, user["id"], body.content.strip())
    await hub.broadcast(body.match_id, {"type": "message", "message": message})
    bot_msg = await maybe_bot_reply(match, user["id"], lang, has_image=False, content=body.content.strip())
    db.mark_read(body.match_id, user["id"])
    return {"message": message, "bot_message": bot_msg}


@app.post("/api/chat/image")
async def chat_image(
    request: Request,
    tarot_session: str | None = Cookie(default=None),
    x_lang: str | None = Header(default=None, alias="X-Lang"),
    match_id: str = Form(...),
    content: str = Form(default=""),
    image: UploadFile = File(...),
) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    user = current_user(tarot_session, lang)
    match = db.get_match(match_id)
    assert_chat_access(user, match, lang, require_active=True)
    url = await save_image(image, lang)
    text = (content or "").strip()[:2000]
    message = db.add_message(match_id, user["id"], text, image_url=url)
    await hub.broadcast(match_id, {"type": "message", "message": message})
    bot_msg = await maybe_bot_reply(match, user["id"], lang, has_image=True, content=text)
    db.mark_read(match_id, user["id"])
    return {"message": message, "bot_message": bot_msg}


@app.post("/api/match/unmatch")
def unmatch(body: UnmatchBody, request: Request, tarot_session: str | None = Cookie(default=None), x_lang: str | None = Header(default=None, alias="X-Lang")) -> dict[str, Any]:
    lang = lang_of(request, x_lang)
    user = current_user(tarot_session, lang)
    match = db.get_match(body.match_id)
    assert_chat_access(user, match, lang)
    count = db.unmatch_by_id(body.match_id, user["id"])
    return {"unmatched": count}


@app.websocket("/ws/chat/{match_id}")
async def chat_ws(websocket: WebSocket, match_id: str) -> None:
    token = websocket.cookies.get(COOKIE)
    try:
        user = current_user(token)
    except HTTPException:
        await websocket.close(code=4401)
        return
    match = db.get_match(match_id)
    if not match or user["id"] not in (match["user_id_1"], match["user_id_2"]):
        await websocket.close(code=4403)
        return
    await hub.join(match_id, websocket)
    try:
        while True:
            await websocket.receive_text()
            await asyncio.sleep(0)
    except WebSocketDisconnect:
        hub.leave(match_id, websocket)
