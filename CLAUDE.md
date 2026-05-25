# CLAUDE.md — Chiang Mai Badminton Ranking System

อ่านไฟล์นี้ก่อนทำงานทุกครั้ง

---

## ภาพรวมโปรเจกต์

ระบบจัดการ Rank แบดมินตันเชียงใหม่ สร้างด้วย Streamlit + PostgreSQL (Supabase)
Deploy บน Streamlit Community Cloud: https://cnx-bad-ranking.streamlit.app

---

## โครงสร้างไฟล์

```
badminton/
├── app.py                    # Entry point + sidebar navigation
├── database.py               # PostgreSQL CRUD ทั้งหมด
├── pages/
│   ├── 0_information.py      # สถิติรวม + ตารางประเภทการแข่งขัน
│   ├── 1_Ranking.py          # แสดง Rank จัดกลุ่มตาม Rank/Team
│   ├── 2_Match_Finder.py     # จับคู่แข่งขัน
│   ├── 3_Protest.py          # โหวตประท้วง
│   └── 4_Admin.py            # Admin panel (ต้อง login)
├── utils/
│   ├── styles.py             # apply_styles(), RANK_COLOR, RANK_EMOJI
│   └── match_rules.py        # MATCH_CATEGORIES, find_matching_categories()
├── data/
│   └── upload_template.xlsx  # Template สำหรับ upload รายชื่อ
└── .streamlit/
    └── secrets.toml          # DB credentials + ADMIN_PASSWORD (ไม่ commit)
```

---

## Rank System

เรียงจากต่ำ → สูง (index 0–7):

| Index | Rank | Emoji | สี | คำอธิบาย |
|-------|------|-------|-----|-----------|
| 0 | BG1 | ⬜️ | #BDBDBD เทา     | Beginner 1 — เริ่มเล่นแบดได้ ยังคุมทิศทางไม่สม่ำเสมอ |
| 1 | BG2 | 🟪 | #AB47BC ม่วง    | Beginner 2 — ตีโต้ต่อเนื่องได้ clear มีระยะ เริ่มจับจังหวะ |
| 2 | N   | 🟦 | #2196F3 น้ำเงิน | Novice — ลูกพื้นฐานครบ เล่นต่อเนื่องได้ ยืนตำแหน่งดีขึ้น |
| 3 | N+  | 🟩 | #4CAF50 เขียว   | Novice+ — คุมทิศทางได้ มีรูปเกม วางแผนได้ |
| 4 | S   | 🟨 | #FFC107 เหลือง  | Standard — เกมนิ่ง วางลูกแม่น ใช้ tactics |
| 5 | P-  | 🟧 | #FF9800 ส้ม     | Semi Pro- — เกมเร็ว ลูกหนัก วางคม คุมจังหวะ |
| 6 | P   | 🟥 | #F44336 แดง     | Pro — เทคนิคครบ คุมเกมทั้งแมตช์ |
| 7 | P+  | 🔴 | #B71C1C แดงเข้ม | Pro+ — ระดับแข่งขันจริง เกมเร็วมาก tactics สูง |

```python
RANKS = ["BG1", "BG2", "N", "N+", "S", "P-", "P", "P+"]
RANK_INDEX = {r: i for i, r in enumerate(RANKS)}
```

---

## Database Schema

```sql
players:
  id UUID PK, name TEXT, rank TEXT, team TEXT,
  created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ

protests:
  id UUID PK, player_id UUID FK→players.id,
  session_id TEXT, direction INT (+1/-1),
  reason TEXT, youtube_url TEXT, image_url TEXT, created_at TIMESTAMPTZ

pending_players:
  id UUID PK, name TEXT, rank TEXT, team TEXT,
  status TEXT DEFAULT 'pending', submitted_at TIMESTAMPTZ

settings:
  key TEXT PK, value TEXT
```

---

## Secrets (.streamlit/secrets.toml)

```toml
ADMIN_PASSWORD = "..."

[database]
host = "aws-1-ap-southeast-1.pooler.supabase.com"
port = 5432
user = "postgres.<project-ref>"
password = "..."
dbname = "postgres"

[s3]
access_key = "..."
secret_key = "..."
endpoint_url = "https://<project-ref>.supabase.co/storage/v1/s3"
bucket = "protest-images"
region = "ap-southeast-1"
```

> **สำคัญ:** ใช้ **Session Pooler** เท่านั้น (ไม่ใช่ direct connection)  
> เพราะ Streamlit Cloud resolve direct host เป็น IPv6 ซึ่ง connect ไม่ได้

---

## Pattern สำคัญ

### DB Connection

```python
# ใช้ get_conn() context manager เสมอ — ห้าม connect ตรง
with get_conn() as conn:
    c = conn.cursor()
    c.execute(...)
```

### Cache

- `@st.cache_resource` — pool, init_db (สร้างครั้งเดียว)
- `@st.cache_data(ttl=300)` — get_all_players (5 นาที)
- ต้อง call `_clear_player_cache()` หลังเปลี่ยนข้อมูล players

### Session State

```python
st.session_state.session_id   # UUID ต่อ browser session (ใช้ lock protest 1 vote/คน)
st.session_state.admin_logged_in  # bool
st.session_state.voted_players    # set of player_id
```

### Navigation

- ไม่ใช้ Streamlit multi-page built-in
- `app.py` โหลด page module ด้วย `importlib` และเรียก `mod.render()`
- แต่ละ page ต้องมี `def render():` เสมอ

---

## Business Rules

- **Protest threshold:** `PROTEST_THRESHOLD = 5` — net votes ≥ 5 → แสดง 🚩
- **Vote lock:** 1 คน/1 ผู้เล่น ต่อ session (ตรวจจาก `session_id` ใน DB)
- **Rank boundary:** ห้ามโหวตขึ้นเกิน P+ หรือลงต่ำกว่า BG1
- **Match warning:** rank ห่างกันเกิน 3 ระดับ = "ไม่มีประเภทที่เหมาะสม"
- **Upload flow:** ผู้ใช้ทั่วไป submit → `pending_players` → Admin อนุมัติ/ปฏิเสธ

---

## Tech Stack

- Python 3.11+
- Streamlit
- psycopg2-binary (PostgreSQL)
- pandas, openpyxl (Excel upload)
- Supabase (hosting DB)
