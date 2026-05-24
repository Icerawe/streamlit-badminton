import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import uuid
from database import RANKS, RANK_INDEX, get_all_players, get_teams, add_protest, get_protest_detail, get_protest_summary, get_all_pending_protests
from utils.styles import RANK_COLOR, RANK_EMOJI

PROTEST_THRESHOLD = 5

from itertools import groupby
from operator import itemgetter


def _render_pending_protests():
    pending_rows = get_all_pending_protests()
    if not pending_rows:
        return
    st.markdown("---")
    st.markdown("#### 📋 รายการประท้วงที่รอ Admin พิจารณา")
    for player_name, votes in groupby(pending_rows, key=itemgetter("name")):
        votes = list(votes)
        first = votes[0]
        color = RANK_COLOR.get(first["rank"], "#555")
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;padding:8px 14px;"
            f"border-left:4px solid {color};border-radius:6px 6px 0 0;"
            f"background:rgba(128,128,128,0.12);margin-bottom:1px;'>"
            f"  <span style='font-weight:700;'>{first['name']}</span>"
            f"  <span style='background:{color};color:white;font-size:0.72rem;padding:2px 9px;"
            f"border-radius:12px;font-weight:700;text-shadow:0 1px 2px rgba(0,0,0,0.4);'>"
            f"    {RANK_EMOJI.get(first['rank'], '')} {first['rank']}</span>"
            f"  <span style='font-size:0.8rem;opacity:0.6;'>{first.get('team') or '-'}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        for v in votes:
            dir_label = "⬆️ +1" if v["direction"] == 1 else "⬇️ -1"
            reason = v.get("reason") or ""
            yt = v.get("youtube_url") or ""
            date = str(v["created_at"])[:10]
            yt_html = f" <a href='{yt}' target='_blank' style='color:#1976d2;'>🎬 ดูวิดีโอ</a>" if yt else ""
            st.markdown(
                f"<div style='padding:6px 14px 6px 28px;border-left:4px solid {color};"
                f"background:rgba(128,128,128,0.06);margin-bottom:1px;font-size:0.85rem;'>"
                f"  <span style='font-weight:600;'>{dir_label}</span>"
                f"  <span style='opacity:0.5;font-size:0.75rem;margin-left:8px;'>{date}</span>"
                f"  <br/>"
                f"  <span style='opacity:0.85;'>{reason}</span>"
                f"  {yt_html}"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)


def render():
    st.markdown('<div class="big-title">✊ ประท้วง / Protest</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">รายงาน/ขอปรับ Rank พร้อมเหตุผลหรือลิงก์ YouTube</div>', unsafe_allow_html=True)

    all_players = get_all_players()
    teams = get_teams()
    if not all_players:
        st.warning("ยังไม่มีผู้เล่นในระบบ")
        return

    # ── Filter ────────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        selected_team = st.selectbox("ทีม", ["ทั้งหมด"] + teams, key="pt_team")
    with col2:
        pool = [p for p in all_players if selected_team == "ทั้งหมด" or p.get("team") == selected_team]
        options = {f"{p['name']} {p['rank']} ({p.get('team') or '-'})": p for p in pool}
        chosen_label = st.selectbox("ผู้เล่น", [None] + list(options.keys()),
                                    format_func=lambda x: "เลือกผู้เล่น" if x is None else x,
                                    key="pt_player")

    player = options.get(chosen_label)
    if not player:
        _render_pending_protests()
        return

    st.divider()

    # ── Player card ───────────────────────────────────────────────────────────
    pid = player["id"]
    rank = player["rank"]
    color = RANK_COLOR.get(rank, "#555")
    net = player["up_votes"] - player["down_votes"]
    net_str = f"+{net}" if net > 0 else str(net)
    already_voted = pid in st.session_state.voted_players

    st.markdown(
        f"<div class='player-card' style='--rank-color:{color};'>"
        f"  <div>"
        f"    <div style='font-size:1.1rem;font-weight:700;'>{player['name']}</div>"
        f"    <div style='color:#aaa;font-size:0.82rem;'>{player.get('team','')}</div>"
        f"    <div class='protest-meter'>⬆️{player['up_votes']} ⬇️{player['down_votes']} (net {net_str})</div>"
        f"  </div>"
        f"  <span class='rank-badge' style='background:{color};'>{RANK_EMOJI[rank]} {rank}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Vote form ─────────────────────────────────────────────────────────────
    if already_voted:
        st.success("✅ คุณโหวตผู้เล่นนี้ไปแล้ว")
    else:
        st.markdown("#### ส่งเสียงโหวต")
        reason = st.text_area("เหตุผล *", key=f"reason_{pid}",
                              placeholder="อธิบายเหตุผลที่ต้องการปรับ rank...", height=90)
        yt_url = st.text_input("ลิงก์ YouTube *", key=f"yt_{pid}",
                               placeholder="https://youtube.com/...")

        yt_valid = False
        if yt_url:
            if not (yt_url.startswith("https://youtube.com") or
                    yt_url.startswith("https://www.youtube.com") or
                    yt_url.startswith("https://youtu.be")):
                st.error("URL ต้องเป็น YouTube เท่านั้น")
            else:
                yt_valid = True
                st.video(yt_url)
        else:
            st.caption("⚠️ กรุณาแนบลิงก์ YouTube ก่อนส่ง")

        direction = st.radio("ทิศทาง", ["⬆️ ขึ้น 1 ระดับ", "⬇️ ลง 1 ระดับ"],
                             key=f"dir_{pid}", horizontal=True)
        up_blocked = "⬆️" in direction and RANK_INDEX.get(rank, 0) == len(RANKS) - 1
        down_blocked = "⬇️" in direction and RANK_INDEX.get(rank, 0) == 0
        disabled = not reason.strip() or not yt_valid or up_blocked or down_blocked

        if not reason.strip():
            st.caption("⚠️ กรุณาระบุเหตุผลก่อนส่ง")

        if st.button("📩 ส่งเสียงโหวต", disabled=disabled, type="primary", key=f"submit_{pid}"):
            dir_val = +1 if "⬆️" in direction else -1
            ok, msg = add_protest(pid, st.session_state.session_id, dir_val,
                                  reason, yt_url if yt_valid else "")
            if ok:
                st.session_state.voted_players.add(pid)
                st.success(f"✅ โหวต{'ขึ้น' if dir_val == 1 else 'ลง'} 1 ระดับให้ {player['name']} แล้ว")
                st.rerun()
            else:
                st.warning(msg)

    _render_pending_protests()

    # ── Vote history ──────────────────────────────────────────────────────────
    details = get_protest_detail(pid)
    if details:
        st.markdown("---")
        st.markdown("**เสียงโหวตที่ผ่านมา:**")
        for d in details:
            direction_label = "⬆️ +1" if d["direction"] == 1 else "⬇️ -1"
            reason_text = f" — {d['reason']}" if d.get("reason") else ""
            yt_text = f" [🎬]({d['youtube_url']})" if d.get("youtube_url") else ""
            st.markdown(
                f"- {direction_label}{reason_text}{yt_text} "
                f"<span style='color:#555;font-size:0.8rem;'>({str(d['created_at'])[:10]})</span>",
                unsafe_allow_html=True,
            )
