import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from database import (
    RANKS, RANK_INDEX,
    get_all_players, add_player, update_player, update_player_rank,
    delete_player, bulk_add_players,
    get_protest_summary, clear_protests_for_player,
    get_teams,
    get_pending_players, approve_pending, reject_pending,
    get_setting, set_setting,
    submit_pending_players,
)
from utils.styles import RANK_COLOR, RANK_EMOJI

PROTEST_THRESHOLD = 5


def render():
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

    st.markdown('<div class="big-title">🔧 Admin</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">จัดการผู้เล่น Rank และเสียงประท้วง</div>', unsafe_allow_html=True)

    # ── Fetch once ───────────────────────────────────────────────────────────
    upload_enabled = get_setting("upload_enabled") == "1"
    pending = get_pending_players()
    teams_list = get_teams()

    # ── Upload section (public) ───────────────────────────────────────────────
    if upload_enabled:
        with st.expander("📤 อัปโหลดรายชื่อผู้เล่น", expanded=True):
            template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "upload_template.xlsx")
            with open(template_path, "rb") as f:
                st.download_button(
                    "⬇️ ดาวน์โหลด Template",
                    f.read(),
                    file_name="upload_template.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            uploaded = st.file_uploader("เลือกไฟล์ Excel (.xlsx)", type=["xlsx"], key="public_upload")
            if uploaded:
                try:
                    df = pd.read_excel(uploaded, sheet_name="Players")
                    st.dataframe(df.head(10), use_container_width=True, hide_index=True)
                    if st.button("📩 ส่งรอ Admin อนุมัติ", type="primary"):
                        added, skipped = submit_pending_players(df)
                        st.success(f"ส่งข้อมูล {added} คนเรียบร้อย — รอ Admin อนุมัติ")
                        if skipped:
                            st.warning("ข้ามแถว: " + ", ".join(skipped))
                except Exception as e:
                    st.error(f"อ่านไฟล์ไม่ได้: {e}")

        if pending:
            st.markdown(f"#### ⏳ รายชื่อที่รอการอนุมัติ ({len(pending)} คน)")
            rows = [{"ชื่อ": p["name"], "Rank": p["rank"], "ทีม": p.get("team") or "—",
                     "ส่งเมื่อ": str(p["submitted_at"])[:10]} for p in pending]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.divider()

    # ── Login ─────────────────────────────────────────────────────────────────
    if not st.session_state.get("admin_logged_in", False):
        st.subheader("🔐 เข้าสู่ระบบ Admin")
        pw = st.text_input("รหัสผ่าน", type="password", key="admin_pw")
        if st.button("เข้าสู่ระบบ"):
            if pw == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("รหัสผ่านไม่ถูกต้อง")
        return

    col_info, col_logout = st.columns([3, 1])
    with col_info:
        st.success("✅ เข้าสู่ระบบสำเร็จ")
    with col_logout:
        if st.button("ออกจากระบบ"):
            st.session_state.admin_logged_in = False
            st.rerun()

    # ── Upload toggle ─────────────────────────────────────────────────────────
    new_val = st.toggle("📤 เปิดให้ผู้ใช้อัปโหลดรายชื่อ", value=upload_enabled)
    if new_val != upload_enabled:
        set_setting("upload_enabled", "1" if new_val else "0")
        st.rerun()

    pending_badge = f" ({len(pending)})" if pending else ""

    admin_tabs = st.tabs([
        "➕ เพิ่ม/แก้ไขผู้เล่น",
        f"📥 อนุมัติรายชื่อ{pending_badge}",
        "📤 Upload Excel",
        "🚩 เสียงประท้วง",
        "📋 รายชื่อทั้งหมด",
    ])

    # Sub-tab 1: Add / Edit
    with admin_tabs[0]:
        st.markdown("#### เพิ่มผู้เล่นใหม่")
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            new_name = st.text_input("ชื่อผู้เล่น (ชื่อเล่น)", key="new_name")
        with col2:
            new_rank = st.selectbox("Rank", RANKS, index=2, key="new_rank")
        with col3:
            team_options = [""] + teams_list + ["+ ทีมใหม่"]
            team_choice = st.selectbox("ทีม", team_options, key="new_team_select")
            if team_choice == "+ ทีมใหม่":
                new_team = st.text_input("ชื่อทีมใหม่", key="new_team_custom")
            else:
                new_team = team_choice
        with col4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ เพิ่ม"):
                if new_name.strip():
                    ok, msg = add_player(new_name, new_rank, new_team)
                    st.success(msg) if ok else st.error(msg)
                    st.rerun()
                else:
                    st.error("กรุณาใส่ชื่อผู้เล่น")

        st.divider()
        st.markdown("#### แก้ไขผู้เล่น")
        filter_team = st.selectbox("กรองตามทีม", ["ทุกทีม"] + teams_list, key="edit_filter_team")
        all_players = get_all_players()
        if filter_team != "ทุกทีม":
            all_players = [p for p in all_players if p.get("team") == filter_team]

        for p in sorted(all_players, key=lambda x: (x.get("team") or "", -RANK_INDEX.get(x["rank"], 0), x["name"])):
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
            with col1:
                st.write(f"**{p['name']}**")
                if p.get("team"):
                    st.caption(p["team"])
            with col2:
                new_r = st.selectbox("rank", RANKS, index=RANK_INDEX.get(p["rank"], 2),
                                     key=f"edit_rank_{p['id']}", label_visibility="collapsed")
            with col3:
                teams_for_edit = [""] + teams_list
                cur_team = p.get("team") or ""
                team_idx = teams_for_edit.index(cur_team) if cur_team in teams_for_edit else 0
                new_t = st.selectbox("team", teams_for_edit, index=team_idx,
                                     key=f"edit_team_{p['id']}", label_visibility="collapsed")
            with col4:
                if st.button("💾", key=f"save_{p['id']}", help="บันทึก"):
                    update_player(p["id"], rank=new_r, team=new_t)
                    st.success(f"อัปเดต {p['name']}")
                    st.rerun()
            with col5:
                if st.button("🗑️", key=f"del_{p['id']}", help="ลบ"):
                    delete_player(p["id"])
                    st.warning(f"ลบ {p['name']} แล้ว")
                    st.rerun()

    # Sub-tab 2: Approve pending
    with admin_tabs[1]:
        st.markdown("#### รายชื่อที่รอการอนุมัติ")
        pending = get_pending_players()
        if not pending:
            st.info("ไม่มีรายชื่อที่รอการอนุมัติ")
        else:
            for row in pending:
                color = RANK_COLOR.get(row["rank"], "#555")
                col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 1])
                with col1:
                    st.write(f"**{row['name']}**")
                with col2:
                    st.markdown(f"<span class='rank-badge' style='background:{color};font-size:0.8rem;'>{row['rank']}</span>",
                                unsafe_allow_html=True)
                with col3:
                    st.write(row.get("team") or "—")
                with col4:
                    if st.button("✅ อนุมัติ", key=f"apv_{row['id']}", type="primary"):
                        ok, msg = approve_pending(row["id"])
                        st.success(msg) if ok else st.error(msg)
                        st.rerun()
                with col5:
                    if st.button("❌ ปฏิเสธ", key=f"rej_{row['id']}"):
                        reject_pending(row["id"])
                        st.warning(f"ปฏิเสธ {row['name']} แล้ว")
                        st.rerun()

    # Sub-tab 3: Upload Excel
    with admin_tabs[2]:
        st.markdown("#### อัปโหลดรายชื่อผู้เล่นจาก Excel")
        st.markdown("""
**รูปแบบไฟล์:**
- Sheet name: `Players`
- คอลัมน์: `ทีม`, `ชื่อเล่น` **(บังคับ)**, `ระดับ` **(บังคับ)**
""")
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "upload_template.xlsx")
        if os.path.exists(template_path):
            with open(template_path, "rb") as f:
                st.download_button("⬇️ ดาวน์โหลด Template Excel", f.read(),
                                   "upload_template.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        uploaded = st.file_uploader("เลือกไฟล์ Excel (.xlsx)", type=["xlsx"], key="admin_upload")
        if uploaded:
            try:
                xls = pd.ExcelFile(uploaded)
                sheet = "Players" if "Players" in xls.sheet_names else xls.sheet_names[0]
                df = pd.read_excel(xls, sheet_name=sheet)
                df.columns = df.columns.str.strip()
                st.dataframe(df.head(20), use_container_width=True)
                if st.button("📥 นำเข้าข้อมูล"):
                    added, skipped = bulk_add_players(df)
                    st.success(f"นำเข้าสำเร็จ {added} คน")
                    if skipped:
                        st.warning("ข้ามรายการ:\n" + "\n".join(f"- {s}" for s in skipped))
                    st.rerun()
            except Exception as e:
                st.error(f"ไม่สามารถอ่านไฟล์ได้: {e}")

    # Sub-tab 4: Protests
    with admin_tabs[3]:
        st.markdown("#### เสียงโหวตประท้วง")
        summary = get_protest_summary()
        if not summary:
            st.info("ยังไม่มีเสียงโหวต")
        else:
            for p in summary:
                net = p["net_score"]
                net_str = f"+{net}" if net > 0 else str(net)
                flag = abs(net) >= PROTEST_THRESHOLD
                card_class = "flag-card" if flag else "player-card"
                flag_label = " 🚩 ควรพิจารณาปรับ!" if flag else ""
                curr_idx = RANK_INDEX.get(p["rank"], 0)
                suggested_rank = ""
                if net >= PROTEST_THRESHOLD and curr_idx < len(RANKS) - 1:
                    suggested_rank = f"→ แนะนำปรับเป็น **{RANKS[curr_idx + 1]}**"
                elif net <= -PROTEST_THRESHOLD and curr_idx > 0:
                    suggested_rank = f"→ แนะนำปรับเป็น **{RANKS[curr_idx - 1]}**"
                team_text = f" | ทีม: {p['team']}" if p.get("team") else ""
                st.markdown(
                    f"<div class='{card_class}'>"
                    f"<b>{p['name']}</b> — Rank <b>{p['rank']}</b>{team_text}{flag_label}<br>"
                    f"👍 {p['up_votes']} &nbsp; 👎 {p['down_votes']} &nbsp; net <b>{net_str}</b>"
                    f"</div>", unsafe_allow_html=True)
                if suggested_rank:
                    st.markdown(suggested_rank)
                col1, col2 = st.columns([2, 1])
                with col1:
                    new_r = st.selectbox("ปรับ Rank", RANKS, index=curr_idx, key=f"protest_rank_{p['id']}")
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("✅ ปรับ + ล้าง votes", key=f"accept_{p['id']}"):
                        update_player_rank(p["id"], new_r)
                        clear_protests_for_player(p["id"])
                        st.success(f"ปรับ {p['name']} → {new_r}")
                        st.rerun()
                    if st.button("❌ ล้าง votes อย่างเดียว", key=f"dismiss_{p['id']}"):
                        clear_protests_for_player(p["id"])
                        st.info(f"ล้าง votes ของ {p['name']} แล้ว")
                        st.rerun()
                st.divider()

    # Sub-tab 5: Full list
    with admin_tabs[4]:
        st.markdown("#### รายชื่อผู้เล่นทั้งหมด")
        all_p = get_all_players()
        if all_p:
            df = pd.DataFrame(all_p)
            cols_show = [c for c in ["name", "team", "rank", "up_votes", "down_votes", "created_at"] if c in df.columns]
            df = df[cols_show]
            df.columns = [{"name": "ชื่อ", "team": "ทีม", "rank": "Rank",
                           "up_votes": "👍 Up", "down_votes": "👎 Down", "created_at": "วันที่เพิ่ม"}.get(c, c)
                          for c in cols_show]
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ Export CSV", csv, "ranking.csv", "text/csv")
        else:
            st.info("ยังไม่มีข้อมูล")
