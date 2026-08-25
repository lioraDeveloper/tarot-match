"""Tarot Matchmaker API + static SPA."""

from __future__ import annotations

import asyncio
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import Cookie, FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import db
from app.auth import hash_password, read_session, sign_session, verify_password
from app.matching import enrich_match, find_best_match
from app.seed import seed_if_empty
from app.tarot import MAJOR_ARCANA, interpret_spread

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

app = FastAPI(title="Tarot Matchmaker", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

COOKIE = "tarot_session"


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
    unmatch_previous: bool = True


class SendBody(BaseModel):
    match_id: str
    content: str = Field(min_length=1, max_length=2000)


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
    seed_if_empty()


def current_user(session: str | None) -> dict[str, Any]:
    user_id = read_session(session)
    if not user_id:
        raise HTTPException(status_code=401, detail="Sign in to enter the chamber.")
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired.")
    return user


def assert_adult(birth_date: str) -> None:
    try:
        born = date.fromisoformat(birth_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Birth date must be YYYY-MM-DD.") from exc
    age = db.age_from_birth(birth_date)
    if age < 18:
        raise HTTPException(status_code=400, detail="You must be 18 or older to join.")
    if born > date.today():
        raise HTTPException(status_code=400, detail="Birth date cannot be in the future.")


def set_session(response: Response, user_id: str) -> None:
    response.set_cookie(
        COOKIE,
        sign_session(user_id),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 14,
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/tarot/deck")
def deck() -> dict[str, Any]:
    return {"cards": [{"id": c["id"], "name": c["name"], "element": c["element"]} for c in MAJOR_ARCANA]}


@app.post("/api/auth/register")
def register(body: RegisterBody, response: Response) -> dict[str, Any]:
    assert_adult(body.birth_date)
    if body.min_age_preference > body.max_age_preference:
        raise HTTPException(status_code=400, detail="Age range is inverted.")
    if db.get_user_by_email(body.email):
        raise HTTPException(status_code=409, detail="That email already has a profile.")
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
    return {"user": user}


@app.post("/api/auth/login")
def login(body: LoginBody, response: Response) -> dict[str, Any]:
    row = db.get_user_by_email(str(body.email))
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password did not match.")
    user = db.user_from_row(row)
    set_session(response, user["id"])
    return {"user": user}


@app.post("/api/auth/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(COOKIE)
    return {"ok": "signed out"}


@app.get("/api/me")
def me(tarot_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    user = current_user(tarot_session)
    match = db.active_match_for(user["id"])
    return {
        "user": user,
        "active_match": enrich_match(match, user["id"]) if match else None,
        "monetization": {
            "is_premium": user["is_premium"],
            "locked": {
                "unlimited_redraws": not user["is_premium"],
                "who_drew_for_you": True,
                "global_filters": True,
            },
        },
    }


@app.put("/api/users/preferences")
def preferences(body: PreferencesBody, tarot_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    user = current_user(tarot_session)
    min_age = body.min_age_preference if body.min_age_preference is not None else user["min_age_preference"]
    max_age = body.max_age_preference if body.max_age_preference is not None else user["max_age_preference"]
    if min_age > max_age:
        raise HTTPException(status_code=400, detail="Age range is inverted.")
    updated = db.update_preferences(
        user["id"],
        looking_for_gender=body.looking_for_gender,
        min_age_preference=body.min_age_preference,
        max_age_preference=body.max_age_preference,
        bio=body.bio,
        name=body.name,
    )
    return {"user": updated}


@app.post("/api/tarot/draw")
def draw(body: DrawBody, tarot_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    user = current_user(tarot_session)
    allowed, reason = db.can_redraw(user)
    if user.get("energy_signature") and not allowed:
        raise HTTPException(status_code=402, detail=reason)
    try:
        reading = interpret_spread(body.card_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if body.unmatch_previous:
        db.unmatch_active(user["id"])
    user = db.save_spread(user["id"], reading["energy_signature"], reading["last_spread"])
    match = find_best_match(user)
    return {"user": user, "reading": reading, "match": match}


@app.get("/api/match/find")
def match_find(tarot_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    user = current_user(tarot_session)
    match = find_best_match(user)
    if not match:
        return {"match": None, "detail": "No reciprocal energetic match is available yet. Try widening your age range, or wait for new seekers."}
    return {"match": match}


@app.get("/api/chat/{match_id}")
def chat_history(match_id: str, tarot_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    user = current_user(tarot_session)
    match = db.get_match(match_id)
    if not match or user["id"] not in (match["user_id_1"], match["user_id_2"]):
        raise HTTPException(status_code=404, detail="Thread not found.")
    return {
        "match": enrich_match(match, user["id"]),
        "messages": db.list_messages(match_id),
    }


@app.post("/api/chat/send")
async def chat_send(body: SendBody, tarot_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    user = current_user(tarot_session)
    match = db.get_match(body.match_id)
    if not match or match["status"] != "active":
        raise HTTPException(status_code=404, detail="This connection is closed.")
    if user["id"] not in (match["user_id_1"], match["user_id_2"]):
        raise HTTPException(status_code=403, detail="Not your thread.")
    message = db.add_message(body.match_id, user["id"], body.content.strip())
    await hub.broadcast(body.match_id, {"type": "message", "message": message})
    return {"message": message}


@app.post("/api/match/unmatch")
def unmatch(tarot_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    user = current_user(tarot_session)
    count = db.unmatch_active(user["id"])
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
