import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from database import RANKS
from utils.styles import RANK_COLOR, RANK_EMOJI, RANK_DETAIL
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
    for rank in ranks_ordered:
        color = RANK_COLOR[rank]
        emoji = RANK_EMOJI[rank]
        detail = RANK_DETAIL.get(rank, {})
        นิยาม  = detail.get("นิยาม", "")
        speed  = detail.get("ความเร็วเกม", "")
        attack = detail.get("การบุก", "")
        defend = detail.get("การรับ", "")
        idea   = detail.get("ไอเดีย-อ่านเกม", "")
        acc    = detail.get("แม่นยำ", "")
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px;"
            f"padding:14px 18px;margin:6px 0;border-left:4px solid {color};color:white;'>"
            f"<div style='font-size:1.1rem;font-weight:700;margin-bottom:8px;'>"
            f"<span class='rank-badge' style='background:{color};'>{emoji} {rank}</span></div>"
            f"<div style='font-size:0.9rem;margin-bottom:10px;color:#ddd;'>{นิยาม}</div>"
            f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:6px 24px;font-size:0.82rem;'>"
            f"<span>⚡ <b style='color:#fff;'>ความเร็วเกม:</b> <span style='color:#ccc;'>{speed}</span></span>"
            f"<span>🎯 <b style='color:#fff;'>แม่นยำ:</b> <span style='color:#ccc;'>{acc}</span></span>"
            f"<span>⚔️ <b style='color:#fff;'>การบุก:</b> <span style='color:#ccc;'>{attack}</span></span>"
            f"<span>🛡 <b style='color:#fff;'>การรับ:</b> <span style='color:#ccc;'>{defend}</span></span>"
            f"<span style='grid-column:1/-1;'>🧠 <b style='color:#fff;'>ไอเดีย-อ่านเกม:</b> <span style='color:#ccc;'>{idea}</span></span>"
            f"</div>"
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

