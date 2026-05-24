from contextlib import contextmanager

import psycopg2
import psycopg2.extras
import psycopg2.pool
import streamlit as st

RANKS = ["BG", "N-", "N", "N+", "S", "P-", "P", "P+"]
RANK_INDEX = {r: i for i, r in enumerate(RANKS)}


@st.cache_resource
def _get_pool():
    db = st.secrets["database"]
    return psycopg2.pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        host=db["host"],
        port=db["port"],
        user=db["user"],
        password=db["password"],
        dbname=db["dbname"],
    )


@contextmanager
def get_conn():
    pool = _get_pool()
    conn = pool.getconn()
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


@st.cache_resource
def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT NOT NULL,
                rank TEXT NOT NULL,
                team TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(name, team)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS protests (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                player_id UUID NOT NULL REFERENCES players(id),
                session_id TEXT NOT NULL,
                direction INTEGER NOT NULL,
                reason TEXT,
                youtube_url TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS pending_players (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT NOT NULL,
                rank TEXT NOT NULL,
                team TEXT,
                submitted_at TIMESTAMPTZ DEFAULT NOW(),
                status TEXT DEFAULT 'pending'
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        c.execute("""
            INSERT INTO settings (key, value) VALUES ('upload_enabled', '0')
            ON CONFLICT (key) DO NOTHING
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_players_team ON players(team)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_players_rank ON players(rank)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_protests_player_id ON protests(player_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_protests_session ON protests(player_id, session_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_pending_status ON pending_players(status)")


# ── Players ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_all_players():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT p.*,
                COALESCE(SUM(CASE WHEN pr.direction=1  THEN 1 ELSE 0 END), 0) AS up_votes,
                COALESCE(SUM(CASE WHEN pr.direction=-1 THEN 1 ELSE 0 END), 0) AS down_votes
            FROM players p
            LEFT JOIN protests pr ON p.id = pr.player_id
            GROUP BY p.id
            ORDER BY p.team NULLS LAST, array_position(ARRAY['BG','N-','N','N+','S','P-','P','P+'], p.rank) DESC, p.name
        """)
        return [dict(r) for r in c.fetchall()]


def get_players_by_rank():
    players = get_all_players()
    grouped = {r: [] for r in RANKS}
    for p in players:
        grouped.setdefault(p["rank"], []).append(p)
    return grouped


def get_teams():
    players = get_all_players()
    seen = []
    for p in players:
        t = p.get("team")
        if t and t not in seen:
            seen.append(t)
    return sorted(seen)


def get_players_by_team(team: str):
    return [p for p in get_all_players() if p.get("team") == team]


def _clear_player_cache():
    get_all_players.clear()


def add_player(name: str, rank: str, team: str = ""):
    try:
        with get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO players (name, rank, team) VALUES (%s, %s, %s)",
                (name.strip(), rank, team.strip() if team else None)
            )
        _clear_player_cache()
        return True, "เพิ่มสำเร็จ"
    except psycopg2.errors.UniqueViolation:
        return False, f"มีชื่อ '{name}' อยู่แล้ว"


def update_player(player_id: str, name: str = None, rank: str = None, team: str = None):
    with get_conn() as conn:
        c = conn.cursor()
        if name is not None:
            c.execute("UPDATE players SET name=%s, updated_at=NOW() WHERE id=%s", (name.strip(), player_id))
        if rank is not None:
            c.execute("UPDATE players SET rank=%s, updated_at=NOW() WHERE id=%s", (rank, player_id))
        if team is not None:
            c.execute("UPDATE players SET team=%s, updated_at=NOW() WHERE id=%s", (team.strip() or None, player_id))
    _clear_player_cache()


def update_player_rank(player_id: str, new_rank: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE players SET rank=%s, updated_at=NOW() WHERE id=%s", (new_rank, player_id))
    _clear_player_cache()


def delete_player(player_id: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM protests WHERE player_id=%s", (player_id,))
        c.execute("DELETE FROM players WHERE id=%s", (player_id,))
    _clear_player_cache()


def bulk_add_players(players_df):
    added, skipped = 0, []
    for _, row in players_df.iterrows():
        name = str(row.get("nickname", row.get("ชื่อเล่น", ""))).strip()
        rank = str(row.get("rank", row.get("ระดับ", ""))).strip()
        team = str(row.get("team", row.get("ทีม", ""))).strip()
        if not name or not rank:
            continue
        if rank not in RANKS:
            skipped.append(f"{name} (rank ไม่ถูกต้อง: {rank})")
            continue
        try:
            with get_conn() as conn:
                c = conn.cursor()
                c.execute(
                    "INSERT INTO players (name, rank, team) VALUES (%s, %s, %s)",
                    (name, rank, team or None)
                )
            added += 1
        except psycopg2.errors.UniqueViolation:
            skipped.append(f"{name} (มีอยู่แล้ว)")
    return added, skipped


# ── Settings ──────────────────────────────────────────────────────────────────

def get_setting(key: str) -> str:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=%s", (key,))
        row = c.fetchone()
        return row["value"] if row else ""


def set_setting(key: str, value: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value=%s",
            (key, value, value)
        )


# ── Pending uploads ───────────────────────────────────────────────────────────

def submit_pending_players(players_df):
    added, skipped = 0, []
    with get_conn() as conn:
        c = conn.cursor()
        for _, row in players_df.iterrows():
            name = str(row.get("ชื่อเล่น", row.get("nickname", ""))).strip()
            rank = str(row.get("ระดับ", row.get("rank", ""))).strip()
            team = str(row.get("ทีม", row.get("team", ""))).strip()
            if not name or not rank:
                continue
            if rank not in RANKS:
                skipped.append(f"{name} (rank ไม่ถูกต้อง: {rank})")
                continue
            c.execute(
                "INSERT INTO pending_players (name, rank, team) VALUES (%s, %s, %s)",
                (name, rank, team or None)
            )
            added += 1
    return added, skipped


def get_pending_players():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM pending_players WHERE status='pending' ORDER BY submitted_at")
        return [dict(r) for r in c.fetchall()]


def approve_pending(pending_id: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM pending_players WHERE id=%s", (pending_id,))
        row = c.fetchone()
        if not row:
            return False, "ไม่พบข้อมูล"
        try:
            c.execute(
                "INSERT INTO players (name, rank, team) VALUES (%s, %s, %s)",
                (row["name"], row["rank"], row["team"])
            )
            c.execute("UPDATE pending_players SET status='approved' WHERE id=%s", (pending_id,))
            return True, f"อนุมัติ {row['name']} แล้ว"
        except psycopg2.errors.UniqueViolation:
            c.execute("UPDATE pending_players SET status='rejected' WHERE id=%s", (pending_id,))
            return False, f"มีชื่อ '{row['name']}' ในทีม '{row['team']}' อยู่แล้ว"


def reject_pending(pending_id: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE pending_players SET status='rejected' WHERE id=%s", (pending_id,))


# ── Protests ──────────────────────────────────────────────────────────────────

def add_protest(player_id: str, session_id: str, direction: int, reason: str = "", youtube_url: str = ""):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id FROM protests WHERE player_id=%s AND session_id=%s",
            (player_id, session_id)
        )
        if c.fetchone():
            return False, "คุณโหวตไปแล้ว"
        c.execute(
            "INSERT INTO protests (player_id, session_id, direction, reason, youtube_url) VALUES (%s,%s,%s,%s,%s)",
            (player_id, session_id, direction, reason or None, youtube_url or None)
        )
    return True, "บันทึกเสียงโหวตแล้ว"


def get_protest_summary():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT p.id, p.name, p.rank, p.team,
                   COALESCE(SUM(pr.direction), 0) AS net_score,
                   COALESCE(SUM(CASE WHEN pr.direction=1  THEN 1 ELSE 0 END), 0) AS up_votes,
                   COALESCE(SUM(CASE WHEN pr.direction=-1 THEN 1 ELSE 0 END), 0) AS down_votes,
                   COUNT(pr.id) AS total_votes
            FROM players p
            LEFT JOIN protests pr ON p.id = pr.player_id
            GROUP BY p.id
            HAVING COUNT(pr.id) > 0
            ORDER BY ABS(COALESCE(SUM(pr.direction), 0)) DESC, COUNT(pr.id) DESC
        """)
        return [dict(r) for r in c.fetchall()]


def clear_protests_for_player(player_id: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM protests WHERE player_id=%s", (player_id,))


def get_protest_detail(player_id: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM protests WHERE player_id=%s ORDER BY created_at DESC", (player_id,))
        return [dict(r) for r in c.fetchall()]
