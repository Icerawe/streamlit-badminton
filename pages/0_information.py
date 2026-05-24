import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from database import RANKS
from utils.styles import RANK_COLOR, RANK_EMOJI, RANK_DESC
from utils.match_rules import MATCH_CATEGORIES


def render():
    st.markdown('<div class="big-title">🏸 ข้อมูลทั่วไป / Information</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">ระบบจัดอันดับมือแบด — Chiang Mai Badminton Ranking</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    st.subheader("ระดับ Rank ทั้งหมด")
    st.markdown("ระบบแบ่งผู้เล่นออกเป็น 8 ระดับ ตั้งแต่ BG (เริ่มต้น) ถึง P+ (สูงสุด):")

    ranks_ordered = list(reversed(RANKS))
    for i in range(0, len(ranks_ordered), 2):
        cols = st.columns(2)
        for j, rank in enumerate(ranks_ordered[i:i+2]):
            color = RANK_COLOR[rank]
            emoji = RANK_EMOJI[rank]
            desc = RANK_DESC.get(rank, "")
            with cols[j]:
                st.markdown(
                    f"<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px;"
                    f"padding:14px;margin:6px 0;border-left:4px solid {color};color:white;'>"
                    f"<div style='font-size:1.2rem;font-weight:700;'>"
                    f"<span class='rank-badge' style='background:{color};'>{emoji} {rank}</span></div>"
                    f"<div style='color:#ccc;font-size:0.85rem;margin-top:8px;'>{desc}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    st.subheader("ประเภทการแข่งขัน")
    st.markdown("แต่ละประเภทมีหลายคู่ (doubles) — Rank ของผู้เล่นต้องอยู่ในช่วงที่กำหนดสำหรับแต่ละคู่")

    for cat_key, cat in MATCH_CATEGORIES.items():
        st.markdown(f"#### ประเภท {cat_key}")
        rows = [{"จับคู่แบบที่": slot, "Rank ต่ำสุด": f"{RANK_EMOJI[lo]} {lo}", "Rank สูงสุด": f"{RANK_EMOJI[hi]} {hi}"}
                for slot, (lo, hi) in cat["pairs"].items()]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")

    st.subheader("บันไดระดับ Rank")
    ladder_html = "<div style='display:flex;flex-direction:column;gap:4px;max-width:300px;'>"
    for rank in reversed(RANKS):
        color = RANK_COLOR[rank]
        emoji = RANK_EMOJI[rank]
        bar_width = (RANKS.index(rank) + 1) * 12
        ladder_html += (
            f"<div style='display:flex;align-items:center;gap:8px;'>"
            f"<span class='rank-badge' style='background:{color};width:60px;text-align:center;'>{emoji} {rank}</span>"
            f"<div style='background:{color};height:22px;width:{bar_width}%;border-radius:4px;opacity:0.8;'></div>"
            f"</div>"
        )
    ladder_html += "</div>"
    st.markdown(ladder_html, unsafe_allow_html=True)
