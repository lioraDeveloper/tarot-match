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
UPLOADS = ROOT / "static" / "uploads"

_local = threading.local()

BOT_EMAIL = "oracle@aether.local"


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


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _migrate(conn: sqlite3.Connection) -> None:
    users = _column_names(conn, "users")
    if "photo_url" not in users:
        conn.execute("ALTER TABLE users ADD COLUMN photo_url TEXT")
    if "is_bot" not in users:
        conn.execute("ALTER TABLE users ADD COLUMN is_bot INTEGER NOT NULL DEFAULT 0")
    messages = _column_names(conn, "messages")
    if "image_url" not in messages:
        conn.execute("ALTER TABLE messages ADD COLUMN image_url TEXT")
    matches = _column_names(conn, "matches")
    if "shared_spread" not in matches:
        conn.execute("ALTER TABLE matches ADD COLUMN shared_spread TEXT")


def init_db() -> None:
    UPLOADS.mkdir(parents=True, exist_ok=True)
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
                created_at TEXT NOT NULL,
                photo_url TEXT,
                is_bot INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                user_id_1 TEXT NOT NULL,
                user_id_2 TEXT NOT NULL,
                compatibility_score REAL NOT NULL,
                mystical_reasoning TEXT NOT NULL,
                shared_spread TEXT,
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
                image_url TEXT,
                FOREIGN KEY (match_id) REFERENCES matches(id),
                FOREIGN KEY (sender_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS conversation_reads (
                match_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                last_read_at TEXT NOT NULL,
                PRIMARY KEY (match_id, user_id),
                FOREIGN KEY (match_id) REFERENCES matches(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_matches_users ON matches(user_id_1, user_id_2, status);
            CREATE INDEX IF NOT EXISTS idx_messages_match ON messages(match_id, timestamp);
            """
        )
        _migrate(conn)


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
    data["is_bot"] = bool(data.get("is_bot"))
    data["photo_url"] = data.get("photo_url")
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
    photo_url: str | None = None,
    is_bot: bool = False,
) -> dict[str, Any]:
    uid = new_id()
    created = now_iso()
    with tx() as conn:
        conn.execute(
            """
            INSERT INTO users (
                id, email, password_hash, name, birth_date, gender,
                looking_for_gender, min_age_preference, max_age_preference,
                bio, energy_signature, last_spread, is_premium, created_at,
                photo_url, is_bot
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                photo_url,
                1 if is_bot else 0,
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


def get_bot_user() -> dict[str, Any] | None:
    row = get_user_by_email(BOT_EMAIL)
    return user_from_row(row) if row else None


def set_user_photo(user_id: str, photo_url: str) -> dict[str, Any] | None:
    with tx() as conn:
        conn.execute("UPDATE users SET photo_url = ? WHERE id = ?", (photo_url, user_id))
    return get_user(user_id)


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


def can_redraw(user: dict[str, Any], lang: str = "en") -> tuple[bool, str]:
    if user.get("is_premium"):
        return True, "premium"
    last = user.get("last_redraw_at")
    if not last:
        return True, "first"
    last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
    if last_dt.tzinfo is None:
        last_dt = last_dt.replace(tzinfo=timezone.utc)
    next_ok = last_dt + timedelta(minutes=5)
    if datetime.now(timezone.utc) >= next_ok:
        return True, "cooldown"
    minutes = max(1, int((next_ok - datetime.now(timezone.utc)).total_seconds() // 60) + 1)
    if lang == "he":
        return False, f"בחשבון חינמי אפשר לקרוא מחדש כל 5 דקות. הפתיחה הבאה בעוד כ־{minutes} דקות. בפרימיום אין המתנה."
    return False, f"Free accounts can redraw every 5 minutes. Next draw in about {minutes} min. Premium removes the wait."


def passes_filters(user: dict[str, Any], other: dict[str, Any]) -> bool:
    if other.get("is_bot"):
        return True
    demo = str(other.get("email") or "").endswith("@demo.local")
    if other["age"] < user["min_age_preference"] or other["age"] > user["max_age_preference"]:
        return False
    if not demo:
        if user["age"] < other["min_age_preference"] or user["age"] > other["max_age_preference"]:
            return False
    my_looking = set(user["looking_for_gender"])
    their_looking = set(other["looking_for_gender"])
    if "any" not in my_looking and other["gender"] not in my_looking:
        return False
    if not demo and "any" not in their_looking and user["gender"] not in their_looking:
        return False
    return True


def unmatched_partner_ids(user_id: str) -> set[str]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT user_id_1, user_id_2 FROM matches
        WHERE status = 'unmatched' AND (user_id_1 = ? OR user_id_2 = ?)
        """,
        (user_id, user_id),
    ).fetchall()
    blocked: set[str] = set()
    for row in rows:
        other = row["user_id_2"] if row["user_id_1"] == user_id else row["user_id_1"]
        blocked.add(other)
    return blocked


def active_partner_ids(user_id: str) -> set[str]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT user_id_1, user_id_2 FROM matches
        WHERE status = 'active' AND (user_id_1 = ? OR user_id_2 = ?)
        """,
        (user_id, user_id),
    ).fetchall()
    out: set[str] = set()
    for row in rows:
        other = row["user_id_2"] if row["user_id_1"] == user_id else row["user_id_1"]
        out.add(other)
    return out


def list_candidates(user: dict[str, Any], *, exclude_existing: bool = True) -> list[dict[str, Any]]:
    """Eligible profiles. Multiple chats are allowed; we no longer lock people to one match."""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM users WHERE id != ? AND energy_signature IS NOT NULL",
        (user["id"],),
    ).fetchall()
    blocked = unmatched_partner_ids(user["id"])
    already = active_partner_ids(user["id"]) if exclude_existing else set()
    out = []
    for row in rows:
        other = user_from_row(row)
        if not other or not other.get("energy_signature"):
            continue
        if other["id"] in blocked:
            continue
        if other["id"] in already:
            continue
        if not passes_filters(user, other):
            continue
        out.append(other)
    return out


def list_discoverable(user: dict[str, Any]) -> list[dict[str, Any]]:
    return list_candidates(user, exclude_existing=False)


def create_match(
    user_id_1: str,
    user_id_2: str,
    score: float,
    reasoning: str,
    shared_spread: dict[str, Any] | None = None,
) -> dict[str, Any]:
    mid = new_id()
    created = now_iso()
    payload = json.dumps(shared_spread) if shared_spread is not None else None
    with tx() as conn:
        conn.execute(
            """
            INSERT INTO matches (id, user_id_1, user_id_2, compatibility_score, mystical_reasoning, shared_spread, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
            """,
            (mid, user_id_1, user_id_2, score, reasoning, payload, created),
        )
    return get_match(mid)


def get_match(match_id: str) -> dict[str, Any] | None:
    conn = _connect()
    row = conn.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone()
    if not row:
        return None
    return _decode_match(dict(row))


def _decode_match(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("shared_spread")
    if isinstance(raw, str) and raw:
        try:
            row["shared_spread"] = json.loads(raw)
        except json.JSONDecodeError:
            row["shared_spread"] = None
    elif not raw:
        row["shared_spread"] = None
    return row


def find_match_between(user_id_a: str, user_id_b: str) -> dict[str, Any] | None:
    conn = _connect()
    row = conn.execute(
        """
        SELECT * FROM matches
        WHERE (user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?)
        ORDER BY created_at DESC LIMIT 1
        """,
        (user_id_a, user_id_b, user_id_b, user_id_a),
    ).fetchone()
    return _decode_match(dict(row)) if row else None


def get_or_create_match(
    user_id_1: str,
    user_id_2: str,
    score: float,
    reasoning: str,
    shared_spread: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing = find_match_between(user_id_1, user_id_2)
    if existing:
        if existing["status"] != "active":
            payload = json.dumps(shared_spread) if shared_spread is not None else None
            with tx() as conn:
                conn.execute(
                    """
                    UPDATE matches SET status = 'active', compatibility_score = ?, mystical_reasoning = ?,
                      shared_spread = COALESCE(?, shared_spread)
                    WHERE id = ?
                    """,
                    (score, reasoning, payload, existing["id"]),
                )
            return get_match(existing["id"])
        if shared_spread is not None and not existing.get("shared_spread"):
            with tx() as conn:
                conn.execute(
                    "UPDATE matches SET shared_spread = ?, compatibility_score = ?, mystical_reasoning = ? WHERE id = ?",
                    (json.dumps(shared_spread), score, reasoning, existing["id"]),
                )
            return get_match(existing["id"])
        return existing
    return create_match(user_id_1, user_id_2, score, reasoning, shared_spread)


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
    return _decode_match(dict(row)) if row else None


def list_active_matches(user_id: str) -> list[dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT * FROM matches
        WHERE status = 'active' AND (user_id_1 = ? OR user_id_2 = ?)
        """,
        (user_id, user_id),
    ).fetchall()
    return [_decode_match(dict(r)) for r in rows]


def unmatch_active(user_id: str) -> int:
    """Legacy helper — prefer unmatch_by_id so other chats stay open."""
    with tx() as conn:
        cur = conn.execute(
            """
            UPDATE matches SET status = 'unmatched'
            WHERE status = 'active' AND (user_id_1 = ? OR user_id_2 = ?)
            """,
            (user_id, user_id),
        )
        return cur.rowcount


def unmatch_by_id(match_id: str, user_id: str) -> int:
    with tx() as conn:
        cur = conn.execute(
            """
            UPDATE matches SET status = 'unmatched'
            WHERE id = ? AND status = 'active' AND (user_id_1 = ? OR user_id_2 = ?)
            """,
            (match_id, user_id, user_id),
        )
        return cur.rowcount


def add_message(
    match_id: str,
    sender_id: str,
    content: str,
    image_url: str | None = None,
) -> dict[str, Any]:
    mid = new_id()
    ts = now_iso()
    text = content or ""
    with tx() as conn:
        conn.execute(
            """
            INSERT INTO messages (id, match_id, sender_id, content, timestamp, image_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (mid, match_id, sender_id, text, ts, image_url),
        )
    return {
        "id": mid,
        "match_id": match_id,
        "sender_id": sender_id,
        "content": text,
        "image_url": image_url,
        "timestamp": ts,
    }


def list_messages(match_id: str) -> list[dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM messages WHERE match_id = ? ORDER BY timestamp ASC",
        (match_id,),
    ).fetchall()
    out = []
    for r in rows:
        item = dict(r)
        item.setdefault("image_url", None)
        out.append(item)
    return out


def last_message(match_id: str) -> dict[str, Any] | None:
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM messages WHERE match_id = ? ORDER BY timestamp DESC LIMIT 1",
        (match_id,),
    ).fetchone()
    return dict(row) if row else None


def unread_count(match_id: str, user_id: str) -> int:
    conn = _connect()
    read_row = conn.execute(
        "SELECT last_read_at FROM conversation_reads WHERE match_id = ? AND user_id = ?",
        (match_id, user_id),
    ).fetchone()
    last_read = read_row["last_read_at"] if read_row else ""
    row = conn.execute(
        """
        SELECT COUNT(*) AS c FROM messages
        WHERE match_id = ? AND sender_id != ? AND timestamp > ?
        """,
        (match_id, user_id, last_read),
    ).fetchone()
    return int(row["c"] if row else 0)


def mark_read(match_id: str, user_id: str) -> None:
    ts = now_iso()
    with tx() as conn:
        conn.execute(
            """
            INSERT INTO conversation_reads (match_id, user_id, last_read_at)
            VALUES (?, ?, ?)
            ON CONFLICT(match_id, user_id) DO UPDATE SET last_read_at = excluded.last_read_at
            """,
            (match_id, user_id, ts),
        )


def user_count() -> int:
    conn = _connect()
    return conn.execute(
        "SELECT COUNT(*) AS c FROM users WHERE is_bot = 0"
    ).fetchone()["c"]
