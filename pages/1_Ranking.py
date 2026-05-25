import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from database import RANKS, RANK_INDEX, get_all_players, get_teams
from utils.styles import RANK_COLOR, RANK_EMOJI

PROTEST_THRESHOLD = 5


def player_card(p, show_rank=True, show_team=True):
    color = RANK_COLOR.get(p["rank"], "#555")
    net = p["up_votes"] - p["down_votes"]
    net_str = f"+{net}" if net > 0 else str(net)
    flag = " 🚩" if abs(net) >= PROTEST_THRESHOLD else ""
    team_label = f"<div style='color:#aaa;font-size:0.78rem;'>{p.get('team','')}</div>" if show_team and p.get("team") else ""
    rank_badge = f"<span class='rank-badge' style='background:{color};font-size:0.8rem;'>{p['rank']}</span>" if show_rank else ""
    st.markdown(
        f"<div class='player-card' style='--rank-color:{color};'>"
        f"  <div>"
        f"    <div style='font-size:1rem;font-weight:600;'>{p['name']}{flag}</div>"
        f"    {team_label}"
        f"    <div class='protest-meter'>⬆️{p['up_votes']} ⬇️{p['down_votes']} (net {net_str})</div>"
        f"  </div>"
        f"  {rank_badge}"
        f"</div>",
        unsafe_allow_html=True,
    )


def render():
    st.markdown('<div class="big-title">🔥 อันดับ / Ranking</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">อันดับแบดมินตันเชียงใหม่ — Ranking Board</div>', unsafe_allow_html=True)

    col_group, col_team = st.columns([1, 2])
    with col_group:
        group_by = st.radio("จัดกลุ่มตาม", ["Rank", "Team"], horizontal=True, index=1)
    with col_team:
        teams = get_teams()
        selected_team = st.selectbox("กรองตามทีม", ["ทั้งหมด"] + teams)

    st.divider()

    all_players = get_all_players()
    if selected_team != "ทั้งหมด":
        all_players = [p for p in all_players if p.get("team") == selected_team]

    def sort_key(p):
        return (p.get("team") or "", -RANK_INDEX.get(p["rank"], 0), p["name"])

    if group_by == "Rank":
        grouped = {}
        for p in sorted(all_players, key=sort_key):
            grouped.setdefault(p["rank"], []).append(p)
        found_any = False
        for rank in reversed(RANKS):
            players = grouped.get(rank, [])
            if not players:
                continue
            found_any = True
            color = RANK_COLOR[rank]
            emoji = RANK_EMOJI[rank]
            label = f"{emoji} {rank}  —  {len(players)} คน"
            with st.expander(label, expanded=False):
                cols_per_row = 3
                for i in range(0, len(players), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, p in enumerate(players[i:i+cols_per_row]):
                        with cols[j]:
                            player_card(p, show_rank=True, show_team=True)
        if not found_any:
            st.info("ไม่พบผู้เล่น")
    else:
        grouped = {}
        for p in sorted(all_players, key=sort_key):
            team = p.get("team") or "ไม่มีทีม"
            grouped.setdefault(team, []).append(p)
        if not grouped:
            st.info("ไม่พบผู้เล่น")
        for team, players in sorted(grouped.items()):
            with st.expander(f"🏸 {team}  —  {len(players)} คน", expanded=False):
                cols_per_row = 3
                for i in range(0, len(players), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, p in enumerate(players[i:i+cols_per_row]):
                        with cols[j]:
                            player_card(p, show_rank=True, show_team=False)
