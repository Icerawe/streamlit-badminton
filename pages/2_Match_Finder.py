import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from database import RANK_INDEX, get_all_players, get_teams, get_players_by_team
from utils.styles import RANK_COLOR, RANK_EMOJI
from utils.match_rules import MATCH_CATEGORIES, find_matching_categories, find_nearest_categories, check_team_categories


def player_label(p):
    team = p.get("team") or "-"
    return f"{p['name']} {p['rank']} ({team})"


def valid_ranks_for_category(cat_key):
    if cat_key == "ทั้งหมด":
        return None
    ranks = set()
    for r1, r2 in MATCH_CATEGORIES[cat_key]["pairs"].values():
        ranks.add(r1); ranks.add(r2)
    return ranks


def filtered_options(all_players, team_filter, rank_filter=None):
    players = [
        p for p in all_players
        if (team_filter == "ทั้งหมด" or p.get("team") == team_filter)
        and (rank_filter is None or p["rank"] in rank_filter)
    ]
    return [player_label(p) for p in players], {player_label(p): p for p in players}


def render():
    st.markdown('<div class="big-title">🔍 จับคู่แข่งขัน / Match Finder</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">ค้นหาประเภทการแข่งขันที่เหมาะสม</div>', unsafe_allow_html=True)

    all_players = get_all_players()
    if not all_players:
        st.warning("ยังไม่มีผู้เล่นในระบบ")
        return

    teams = get_teams()
    mode = st.radio("โหมดค้นหา", ["🎯 จับคู่", "👥 จับคู่ภายในทีม"], horizontal=True)
    st.markdown("---")

    if mode == "🎯 จับคู่":
        col1, col2 = st.columns(2)
        with col1:
            team_filter_a = st.selectbox("ทีมคนที่ 1", ["ทั้งหมด"] + teams, key="mf_tf_a")
            options_a, map_a = filtered_options(all_players, team_filter_a, None)
            label_a = st.selectbox("ผู้เล่นคนที่ 1", options_a, key="mf_pa")
        with col2:
            team_filter_b = st.selectbox("ทีมคนที่ 2", ["ทั้งหมด"] + teams, key="mf_tf_b")
            options_b, map_b = filtered_options(all_players, team_filter_b, None)
            label_b = st.selectbox("ผู้เล่นคนที่ 2", options_b, key="mf_pb")

        pa = map_a.get(label_a) or {}
        pb = map_b.get(label_b) or {}
        if not pa or not pb:
            st.warning("ไม่พบผู้เล่น")
            return

        if pa["id"] == pb["id"]:
            st.warning("กรุณาเลือกผู้เล่น 2 คนที่ต่างกัน")
        else:
            c1, c2 = st.columns(2)
            for col, p in zip([c1, c2], [pa, pb]):
                with col:
                    color = RANK_COLOR[p["rank"]]
                    st.markdown(
                        f"<div class='player-card' style='--rank-color:{color};'>"
                        f"  <div>"
                        f"    <div style='font-size:1rem;font-weight:600;'>{p['name']}</div>"
                        f"    <div style='color:#aaa;font-size:0.8rem;'>{p.get('team','')}</div>"
                        f"  </div>"
                        f"  <span class='rank-badge' style='background:{color};font-size:0.85rem;'>{RANK_EMOJI[p['rank']]} {p['rank']}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

            matches = find_matching_categories(pa["rank"], pb["rank"])

            st.markdown("### แนะนำการแข่งที่เหมาะสม")
            if matches:
                for cat in dict.fromkeys(m["category"] for m in matches):
                    cat_data = MATCH_CATEGORIES[cat]
                    slots_html = " &nbsp;|&nbsp; ".join(
                        f"จับคู่แบบที่ {slot}: {lo}–{hi}"
                        for slot, (lo, hi) in cat_data["pairs"].items()
                    )
                    st.markdown(
                        f"<div class='match-category-card valid'>"
                        f"<b>✅ ประเภท {cat}</b><br>"
                        f"<span style='color:#aaa;font-size:0.85rem;'>{slots_html}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            else:
                gap = abs(RANK_INDEX.get(pa["rank"], 0) - RANK_INDEX.get(pb["rank"], 0))
                if gap > 3:
                    st.warning("❌ ไม่มีประเภทแข่งขันที่เหมาะสม — มือห่างกันเกินไป")
                else:
                    nearest = find_nearest_categories(pa["rank"], pb["rank"])
                    if nearest:
                        shown = dict.fromkeys(n["category"] for n in nearest)
                        for cat in shown:
                            cat_data = MATCH_CATEGORIES[cat]
                            slots_html = " &nbsp;|&nbsp; ".join(
                                f"{lo}–{hi}"
                                for slot, (lo, hi) in cat_data["pairs"].items()
                            )
                            st.markdown(
                                f"<div class='match-category-card valid'>"
                                f"<b>⚠️ ประเภทใกล้เคียง {cat}</b><br>"
                                f"<span style='color:#aaa;font-size:0.85rem;'>{slots_html}</span>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                    else:
                        st.warning("❌ ไม่มีประเภทแข่งขันที่เหมาะสม")

    else:
        if not teams:
            st.info("ยังไม่มีข้อมูลทีม")
            return

        selected_team = st.selectbox("เลือกทีม", teams, key="mf_team")
        team_players = sorted(get_players_by_team(selected_team), key=lambda p: -RANK_INDEX.get(p["rank"], 0))

        if len(team_players) < 2:
            st.warning("ทีมนี้มีผู้เล่นน้อยกว่า 2 คน")
            return

        results = check_team_categories(team_players)
        st.markdown("### ประเภทการแข่งขันที่ทีมสามารถลงแข่งได้")
        if results:
            for cat, pairings in results.items():
                st.markdown(
                    f"<div class='match-category-card valid'>"
                    f"<b>✅ ประเภท {cat}</b> — {len(pairings)} คู่ที่เป็นไปได้"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                rows = [
                    {"ผู้เล่น A": f"{pair['player_a']} ({pair['rank_a']})",
                     "ผู้เล่น B": f"{pair['player_b']} ({pair['rank_b']})"}
                    for pair in pairings
                ]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.error("❌ ไม่มีประเภทแข่งขันที่เหมาะสมสำหรับทีมนี้")
