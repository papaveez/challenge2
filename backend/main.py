import hashlib
import os
import secrets
import sqlite3
import time
import uuid

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "challenge.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DIST_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend", "dist")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MASTER_USERNAME = "vas"
ALLOWED_PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"}
MAX_PHOTO_BYTES = 15 * 1024 * 1024


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_master INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tokens (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                unit TEXT NOT NULL,
                base_amount REAL NOT NULL,
                per_person INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
                amount REAL NOT NULL,
                photo TEXT,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    salt, digest = stored.split("$", 1)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return secrets.compare_digest(candidate, digest)


def get_setting(conn, key):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_setting(conn, key, value):
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def current_user(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    token = authorization.removeprefix("Bearer ").strip()
    with db() as conn:
        row = conn.execute(
            "SELECT u.* FROM tokens t JOIN users u ON u.id = t.user_id WHERE t.token = ?",
            (token,),
        ).fetchone()
    if not row:
        raise HTTPException(401, "Invalid or expired token")
    return dict(row)


def require_master(user):
    if not user["is_master"]:
        raise HTTPException(403, "Only the master user can do that")


app = FastAPI(title="The Challenge")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
init_db()


class Credentials(BaseModel):
    username: str
    password: str


class ChallengeIn(BaseModel):
    name: str
    unit: str
    base_amount: float
    per_person: bool = False


def issue_token(conn, user_id: int) -> str:
    token = secrets.token_hex(32)
    conn.execute(
        "INSERT INTO tokens (token, user_id, created_at) VALUES (?, ?, ?)",
        (token, user_id, time.time()),
    )
    return token


def public_user(row) -> dict:
    return {"id": row["id"], "username": row["username"], "is_master": bool(row["is_master"])}


@app.post("/api/signup")
def signup(creds: Credentials):
    username = creds.username.strip().lower()
    if not username or len(username) > 30 or not username.replace("_", "").isalnum():
        raise HTTPException(400, "Username must be 1-30 letters, numbers or underscores")
    if len(creds.password) < 4:
        raise HTTPException(400, "Password must be at least 4 characters")
    with db() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (username, password, is_master, created_at) VALUES (?, ?, ?, ?)",
                (username, hash_password(creds.password), int(username == MASTER_USERNAME), time.time()),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(409, "Username already taken")
        token = issue_token(conn, cur.lastrowid)
        user = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return {"token": token, "user": public_user(user)}


@app.post("/api/login")
def login(creds: Credentials):
    username = creds.username.strip().lower()
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not user or not verify_password(creds.password, user["password"]):
            raise HTTPException(401, "Wrong username or password")
        token = issue_token(conn, user["id"])
    return {"token": token, "user": public_user(user)}


@app.get("/api/me")
def me(authorization: str | None = Header(None)):
    return public_user(current_user(authorization))


@app.post("/api/challenges")
def create_challenge(challenge: ChallengeIn, authorization: str | None = Header(None)):
    user = current_user(authorization)
    require_master(user)
    if not challenge.name.strip():
        raise HTTPException(400, "Challenge needs a name")
    if challenge.base_amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO challenges (name, unit, base_amount, per_person, created_at) VALUES (?, ?, ?, ?, ?)",
            (challenge.name.strip(), challenge.unit.strip(), challenge.base_amount,
             int(challenge.per_person), time.time()),
        )
    return {"id": cur.lastrowid}


@app.delete("/api/challenges/{challenge_id}")
def delete_challenge(challenge_id: int, authorization: str | None = Header(None)):
    user = current_user(authorization)
    require_master(user)
    with db() as conn:
        conn.execute("DELETE FROM challenges WHERE id = ?", (challenge_id,))
    return {"ok": True}


@app.post("/api/event/start")
def start_event(authorization: str | None = Header(None)):
    user = current_user(authorization)
    require_master(user)
    with db() as conn:
        if get_setting(conn, "started_at"):
            raise HTTPException(400, "Challenge already started")
        set_setting(conn, "started_at", str(time.time()))
        set_setting(conn, "ended_at", None)
    return {"ok": True}


@app.post("/api/event/stop")
def stop_event(authorization: str | None = Header(None)):
    user = current_user(authorization)
    require_master(user)
    with db() as conn:
        if not get_setting(conn, "started_at"):
            raise HTTPException(400, "Challenge has not started")
        set_setting(conn, "ended_at", str(time.time()))
    return {"ok": True}


@app.post("/api/event/reset")
def reset_event(authorization: str | None = Header(None)):
    user = current_user(authorization)
    require_master(user)
    with db() as conn:
        set_setting(conn, "started_at", None)
        set_setting(conn, "ended_at", None)
        conn.execute("DELETE FROM contributions")
    return {"ok": True}


@app.post("/api/contributions")
async def add_contribution(
    challenge_id: int = Form(...),
    amount: float = Form(...),
    photo: UploadFile | None = File(None),
    authorization: str | None = Header(None),
):
    user = current_user(authorization)
    if amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    with db() as conn:
        started = get_setting(conn, "started_at")
        ended = get_setting(conn, "ended_at")
        if not started:
            raise HTTPException(400, "The challenge has not started yet")
        if ended:
            raise HTTPException(400, "The challenge is over")
        challenge = conn.execute(
            "SELECT * FROM challenges WHERE id = ?", (challenge_id,)
        ).fetchone()
        if not challenge:
            raise HTTPException(404, "No such challenge")

        photo_name = None
        if photo is not None and photo.filename:
            ext = os.path.splitext(photo.filename)[1].lower()
            if ext not in ALLOWED_PHOTO_EXTS:
                raise HTTPException(400, f"Photo must be one of: {', '.join(sorted(ALLOWED_PHOTO_EXTS))}")
            data = await photo.read()
            if len(data) > MAX_PHOTO_BYTES:
                raise HTTPException(400, "Photo too large (max 15 MB)")
            photo_name = f"{uuid.uuid4().hex}{ext}"
            with open(os.path.join(UPLOAD_DIR, photo_name), "wb") as f:
                f.write(data)

        conn.execute(
            "INSERT INTO contributions (user_id, challenge_id, amount, photo, created_at) VALUES (?, ?, ?, ?, ?)",
            (user["id"], challenge_id, amount, photo_name, time.time()),
        )
    return {"ok": True}


@app.delete("/api/contributions/{contribution_id}")
def delete_contribution(contribution_id: int, authorization: str | None = Header(None)):
    user = current_user(authorization)
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM contributions WHERE id = ?", (contribution_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "No such contribution")
        if row["user_id"] != user["id"] and not user["is_master"]:
            raise HTTPException(403, "You can only delete your own contributions")
        if row["photo"]:
            try:
                os.remove(os.path.join(UPLOAD_DIR, row["photo"]))
            except OSError:
                pass
        conn.execute("DELETE FROM contributions WHERE id = ?", (contribution_id,))
    return {"ok": True}


@app.get("/api/state")
def state(authorization: str | None = Header(None)):
    current_user(authorization)
    with db() as conn:
        users = [public_user(r) for r in conn.execute(
            "SELECT * FROM users ORDER BY created_at"
        ).fetchall()]
        n_participants = max(len(users), 1)

        started_at = get_setting(conn, "started_at")
        ended_at = get_setting(conn, "ended_at")

        challenge_rows = conn.execute(
            "SELECT * FROM challenges ORDER BY created_at"
        ).fetchall()
        contribution_rows = conn.execute(
            "SELECT c.*, u.username FROM contributions c "
            "JOIN users u ON u.id = c.user_id ORDER BY c.created_at DESC"
        ).fetchall()

        # per-user, per-challenge totals
        totals: dict[tuple[int, int], float] = {}
        for row in contribution_rows:
            key = (row["user_id"], row["challenge_id"])
            totals[key] = totals.get(key, 0) + row["amount"]

        challenges = []
        for ch in challenge_rows:
            target = ch["base_amount"] * n_participants if ch["per_person"] else ch["base_amount"]
            done = sum(v for (uid, cid), v in totals.items() if cid == ch["id"])
            challenges.append({
                "id": ch["id"],
                "name": ch["name"],
                "unit": ch["unit"],
                "base_amount": ch["base_amount"],
                "per_person": bool(ch["per_person"]),
                "target": target,
                "done": done,
                "contributions": [
                    {
                        "id": r["id"],
                        "username": r["username"],
                        "amount": r["amount"],
                        "photo": f"/uploads/{r['photo']}" if r["photo"] else None,
                        "created_at": r["created_at"],
                        "user_id": r["user_id"],
                    }
                    for r in contribution_rows if r["challenge_id"] == ch["id"]
                ],
            })

        # leaderboard: percentage points contributed across all challenges
        leaderboard = []
        for u in users:
            points = 0.0
            per_challenge = {}
            for ch in challenges:
                amount = totals.get((u["id"], ch["id"]), 0)
                per_challenge[str(ch["id"])] = amount
                if ch["target"] > 0:
                    points += amount / ch["target"] * 100
            leaderboard.append({
                "user_id": u["id"],
                "username": u["username"],
                "points": round(points, 1),
                "per_challenge": per_challenge,
            })
        leaderboard.sort(key=lambda e: -e["points"])

    return {
        "event": {
            "started_at": float(started_at) if started_at else None,
            "ended_at": float(ended_at) if ended_at else None,
            "server_time": time.time(),
        },
        "users": users,
        "n_participants": len(users),
        "challenges": challenges,
        "leaderboard": leaderboard,
    }


# Serve the built frontend. Mounted last so /api and /uploads keep priority.
if os.path.isdir(DIST_DIR):
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="frontend")
