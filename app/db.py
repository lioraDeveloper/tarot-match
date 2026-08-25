"""SQLite persistence matching the PostgreSQL blueprint (UUID PKs, JSON fields)."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "tarot_match.db"

_local = threading.local()


def _connect() -> sqlite3.Connection:
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        _local.conn = conn
    return conn


@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db() -> None:
    with tx() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                gender TEXT NOT NULL,
                looking_for_gender TEXT NOT NULL,
                min_age_preference INTEGER NOT NULL,
                max_age_preference INTEGER NOT NULL,
                bio TEXT NOT NULL DEFAULT '',
                energy_signature TEXT,
                last_spread TEXT,
                is_premium INTEGER NOT NULL DEFAULT 0,
                last_redraw_at TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                user_id_1 TEXT NOT NULL,
                user_id_2 TEXT NOT NULL,
                compatibility_score REAL NOT NULL,
                mystical_reasoning TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('active', 'unmatched')),
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id_1) REFERENCES users(id),
                FOREIGN KEY (user_id_2) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                match_id TEXT NOT NULL,
                sender_id TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (match_id) REFERENCES matches(id),
                FOREIGN KEY (sender_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_matches_users ON matches(user_id_1, user_id_2, status);
            CREATE INDEX IF NOT EXISTS idx_messages_match ON messages(match_id, timestamp);
            """
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


def parse_json(value: str | None) -> Any:
    if not value:
        return None
    return json.loads(value)


def age_from_birth(birth_date: str) -> int:
    born = date.fromisoformat(birth_date)
    today = date.today()
    years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return years


def user_from_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    data["looking_for_gender"] = json.loads(data["looking_for_gender"])
    data["energy_signature"] = parse_json(data.get("energy_signature"))
    data["last_spread"] = parse_json(data.get("last_spread"))
    data["is_premium"] = bool(data["is_premium"])
    data["age"] = age_from_birth(data["birth_date"])
    data.pop("password_hash", None)
    return data


def create_user(
    *,
    email: str,
    password_hash: str,
    name: str,
    birth_date: str,
    gender: str,
    looking_for_gender: list[str],
    min_age_preference: int,
    max_age_preference: int,
    bio: str = "",
    is_premium: bool = False,
    energy_signature: dict | None = None,
    last_spread: dict | None = None,
) -> dict[str, Any]:
    uid = new_id()
    created = now_iso()
    with tx() as conn:
        conn.execute(
            """
            INSERT INTO users (
                id, email, password_hash, name, birth_date, gender,
                looking_for_gender, min_age_preference, max_age_preference,
                bio, energy_signature, last_spread, is_premium, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uid,
                email.lower().strip(),
                password_hash,
                name.strip(),
                birth_date,
                gender,
                json.dumps(looking_for_gender),
                min_age_preference,
                max_age_preference,
                bio,
                json.dumps(energy_signature) if energy_signature else None,
                json.dumps(last_spread) if last_spread else None,
                1 if is_premium else 0,
                created,
            ),
        )
    return get_user(uid)


def get_user(user_id: str) -> dict[str, Any] | None:
    conn = _connect()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return user_from_row(row)


def get_user_by_email(email: str) -> sqlite3.Row | None:
    conn = _connect()
    return conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
    ).fetchone()


def update_preferences(
    user_id: str,
    *,
    looking_for_gender: list[str] | None = None,
    min_age_preference: int | None = None,
    max_age_preference: int | None = None,
    bio: str | None = None,
    name: str | None = None,
) -> dict[str, Any] | None:
    user = get_user(user_id)
    if not user:
        return None
    looking = looking_for_gender if looking_for_gender is not None else user["looking_for_gender"]
    min_age = min_age_preference if min_age_preference is not None else user["min_age_preference"]
    max_age = max_age_preference if max_age_preference is not None else user["max_age_preference"]
    bio_val = bio if bio is not None else user["bio"]
    name_val = name if name is not None else user["name"]
    with tx() as conn:
        conn.execute(
            """
            UPDATE users SET looking_for_gender = ?, min_age_preference = ?,
                max_age_preference = ?, bio = ?, name = ?
            WHERE id = ?
            """,
            (json.dumps(looking), min_age, max_age, bio_val, name_val, user_id),
        )
    return get_user(user_id)


def save_spread(user_id: str, energy_signature: dict, last_spread: dict) -> dict[str, Any]:
    with tx() as conn:
        conn.execute(
            """
            UPDATE users SET energy_signature = ?, last_spread = ?, last_redraw_at = ?
            WHERE id = ?
            """,
            (json.dumps(energy_signature), json.dumps(last_spread), now_iso(), user_id),
        )
    return get_user(user_id)


def can_redraw(user: dict[str, Any]) -> tuple[bool, str]:
    if user.get("is_premium"):
        return True, "premium"
    last = user.get("last_redraw_at")
    if not last:
        return True, "first"
    last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
    if last_dt.tzinfo is None:
        last_dt = last_dt.replace(tzinfo=timezone.utc)
    next_ok = last_dt + timedelta(days=7)
    if datetime.now(timezone.utc) >= next_ok:
        return True, "weekly"
    hours = int((next_ok - datetime.now(timezone.utc)).total_seconds() // 3600) + 1
    return False, f"Free seekers may redraw once per week. Next opening in ~{hours}h. Premium unlocks unlimited rituals."


def list_candidates(user: dict[str, Any]) -> list[dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT * FROM users
        WHERE id != ? AND energy_signature IS NOT NULL
        """,
        (user["id"],),
    ).fetchall()
    busy_ids = set()
    active = conn.execute(
        """
        SELECT user_id_1, user_id_2 FROM matches WHERE status = 'active'
        """
    ).fetchall()
    for row in active:
        busy_ids.add(row["user_id_1"])
        busy_ids.add(row["user_id_2"])

    unmatched_pairs = conn.execute(
        """
        SELECT user_id_1, user_id_2 FROM matches
        WHERE status = 'unmatched'
          AND (user_id_1 = ? OR user_id_2 = ?)
        """,
        (user["id"], user["id"]),
    ).fetchall()
    blocked = set()
    for row in unmatched_pairs:
        other = row["user_id_2"] if row["user_id_1"] == user["id"] else row["user_id_1"]
        blocked.add(other)

    out = []
    my_age = user["age"]
    my_looking = set(user["looking_for_gender"])
    for row in rows:
        other = user_from_row(row)
        if not other or not other.get("energy_signature"):
            continue
        if other["id"] in busy_ids:
            continue
        if other["id"] in blocked:
            continue
        if other["age"] < user["min_age_preference"] or other["age"] > user["max_age_preference"]:
            continue
        if my_age < other["min_age_preference"] or my_age > other["max_age_preference"]:
            continue
        their_looking = set(other["looking_for_gender"])
        if "any" not in my_looking and other["gender"] not in my_looking:
            continue
        if "any" not in their_looking and user["gender"] not in their_looking:
            continue
        out.append(other)
    return out


def create_match(user_id_1: str, user_id_2: str, score: float, reasoning: str) -> dict[str, Any]:
    mid = new_id()
    created = now_iso()
    with tx() as conn:
        conn.execute(
            """
            INSERT INTO matches (id, user_id_1, user_id_2, compatibility_score, mystical_reasoning, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?)
            """,
            (mid, user_id_1, user_id_2, score, reasoning, created),
        )
    return get_match(mid)


def get_match(match_id: str) -> dict[str, Any] | None:
    conn = _connect()
    row = conn.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone()
    if not row:
        return None
    return dict(row)


def active_match_for(user_id: str) -> dict[str, Any] | None:
    conn = _connect()
    row = conn.execute(
        """
        SELECT * FROM matches
        WHERE status = 'active' AND (user_id_1 = ? OR user_id_2 = ?)
        ORDER BY created_at DESC LIMIT 1
        """,
        (user_id, user_id),
    ).fetchone()
    return dict(row) if row else None


def unmatch_active(user_id: str) -> int:
    with tx() as conn:
        cur = conn.execute(
            """
            UPDATE matches SET status = 'unmatched'
            WHERE status = 'active' AND (user_id_1 = ? OR user_id_2 = ?)
            """,
            (user_id, user_id),
        )
        return cur.rowcount


def add_message(match_id: str, sender_id: str, content: str) -> dict[str, Any]:
    mid = new_id()
    ts = now_iso()
    with tx() as conn:
        conn.execute(
            """
            INSERT INTO messages (id, match_id, sender_id, content, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (mid, match_id, sender_id, content, ts),
        )
    return {"id": mid, "match_id": match_id, "sender_id": sender_id, "content": content, "timestamp": ts}


def list_messages(match_id: str) -> list[dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM messages WHERE match_id = ? ORDER BY timestamp ASC",
        (match_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def user_count() -> int:
    conn = _connect()
    return conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
