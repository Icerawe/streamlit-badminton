import streamlit as st

RANK_COLOR = {
    "BG1":   "#BDBDBD",
    "BG2":   "#AB47BC",
    "N":     "#2196F3",
    "N+":    "#4CAF50",
    "S":     "#FFC107",
    "P-": "#FF9800",
    "P":     "#F44336",
    "P+":    "#B71C1C",
}

RANK_EMOJI = {
    "BG1":   "⬜️",
    "BG2":   "🟪",
    "N":     "🟦",
    "N+":    "🟩",
    "S":     "🟨",
    "P-": "🟧",
    "P":     "🟥",
    "P+":    "🔴",
}

RANK_DETAIL = {
    "BG1": {
        "นิยาม":          "เริ่มเล่นแบดได้ ตีโต้ลูกสั้นๆ ได้บ้าง ยังควบคุมทิศทางไม่สม่ำเสมอ",
        "ความเร็วเกม":    "ช้า",
        "การบุก":         "ตีหนักได้บ้าง ยังไม่มีจังหวะที่แน่นอน",
        "การรับ":         "รับลูกตรงๆ ได้ ยังวางตำแหน่งไม่ดี",
        "ไอเดีย-อ่านเกม": "เริ่มเข้าใจจังหวะรับ-ส่งลูก",
        "แม่นยำ":         "ยังไม่สม่ำเสมอ — คุมทิศทางได้บางลูก",
    },
    "BG2": {
        "นิยาม":          "ตีโต้ต่อเนื่องได้ clear มีระยะ เริ่มจับจังหวะและวางตำแหน่งได้",
        "ความเร็วเกม":    "ช้า–ปานกลาง",
        "การบุก":         "smash ได้บ้าง มีแรงพอใช้ ยังขาดมุม",
        "การรับ":         "รับ clear และยกได้ดี เริ่มรับ smash เบาได้",
        "ไอเดีย-อ่านเกม": "จับจังหวะลูกได้ เริ่มรู้ว่าควรตีไปไหน",
        "แม่นยำ":         "พอใช้ — คุมทิศทางหลักและระยะได้",
    },
    "N": {
        "นิยาม":          "ลูกพื้นฐานครบ เล่นต่อเนื่องได้ ยืนตำแหน่งดีขึ้น",
        "ความเร็วเกม":    "ปานกลาง",
        "การบุก":         "smash ตรงๆ ได้ drop shot เริ่มใช้ได้",
        "การรับ":         "block และยกได้ รับ smash เบาได้",
        "ไอเดีย-อ่านเกม": "เริ่มวางตำแหน่ง รู้ว่าควรตีไปไหน",
        "แม่นยำ":         "ปานกลาง — เล่นต่อเนื่องได้โดยไม่เสียง่าย",
    },
    "N+": {
        "นิยาม":          "คุมทิศทางได้ มีรูปเกม วางแผนได้",
        "ความเร็วเกม":    "ปานกลาง–เร็ว",
        "การบุก":         "smash มีแรง วางมุมได้ เริ่มใช้ deception",
        "การรับ":         "รับแล้วโต้กลับได้ เริ่มเลือกทิศทางตอบ",
        "ไอเดีย-อ่านเกม": "อ่านลูกคู่แข่งได้บางส่วน วางแผนสั้นๆ ได้",
        "แม่นยำ":         "ดี — คุมมุมหลักได้ เสียน้อยลง",
    },
    "S": {
        "นิยาม":          "เกมนิ่ง วางลูกแม่น ใช้ tactics",
        "ความเร็วเกม":    "เร็ว",
        "การบุก":         "smash หนัก วางมุมคม เปลี่ยนจังหวะรุกได้",
        "การรับ":         "รับแล้วเปลี่ยนเป็นรุก เลือกตอบได้หลายแบบ",
        "ไอเดีย-อ่านเกม": "อ่านเกมคู่แข่งได้ วางกับดักลูกได้",
        "แม่นยำ":         "สูง — วางลูกได้ตรงจุด ควบคุม rally ได้",
    },
    "P-": {
        "นิยาม":          "Knocker / ผู้ช่วยโค้ช — เกมเร็ว ลูกหนัก วางคม คุมจังหวะ",
        "ความเร็วเกม":    "สูงมาก",
        "การบุก":         "smash หนักและแม่น กดมุมสุดได้ ใช้ net kill ได้",
        "การรับ":         "คุมเกมหรือสวนได้ รับ smash แล้วโต้แบบ counter ได้",
        "ไอเดีย-อ่านเกม": "อ่านเกมขั้นสูง คาดการณ์ลูกถัดไปได้ล่วงหน้า",
        "แม่นยำ":         "สูงมาก — วางลูกคมแม่น ควบคุมความเร็วได้ดี",
    },
    "P": {
        "นิยาม":          "Coach — เทคนิคครบ คุมเกมทั้งแมตช์",
        "ความเร็วเกม":    "สูง + คุมจังหวะ",
        "การบุก":         "บุกได้หลายรูปแบบ เปลี่ยนจังหวะและหลอกได้ตลอด",
        "การรับ":         "รับแล้วพลิกเป็นรุกทันที รับ smash หนักได้สบาย",
        "ไอเดีย-อ่านเกม": "คุมเกมทั้งแมตช์ รู้จุดอ่อนคู่แข่งและใช้ประโยชน์ได้",
        "แม่นยำ":         "สูงมาก — เชี่ยวชาญทุก stroke ควบคุมเกมได้เต็มที่",
    },
    "P+": {
        "นิยาม":          "Coach / แข่งระดับประเทศ — เกมเร็วมาก tactics สูง",
        "ความเร็วเกม":    "สูงสุด",
        "การบุก":         "บุกระดับแข่งขัน smash เต็มแรง net kill รวดเร็ว",
        "การรับ":         "รับ smash หนักและสวนแต้มได้ รับได้แม้อยู่ในสถานการณ์เสียเปรียบ",
        "ไอเดีย-อ่านเกม": "tactics ระดับสูง อ่านเกมและปรับแผนในกลางแมตช์ได้",
        "แม่นยำ":         "สูงสุด — ควบคุมทุกลูกอย่างแม่นยำแม้ในสถานการณ์กดดัน",
    },
}

RANK_DESC = {
    "BG1":   "ระดับเริ่มต้น — มือใหม่หัดแข่ง",
    "BG2":   "ระดับเริ่มต้น 2 — เริ่มแข่งขันได้",
    "N":     "ระดับ Novice — ตีลูกพื้นฐานครบ",
    "N+":    "ระดับ Novice สูง — rally ดี เริ่มวางเกม",
    "S":     "ระดับ Standard — เล่น rally ยาว เริ่มใช้ tactics",
    "P-": "ระดับ Semi Pro — Knocker / ผู้ช่วย Coach",
    "P":     "ระดับ Pro — Coach",
    "P+":    "ระดับ Pro สูง — Coach / แข่งระดับประเทศ",
}


def apply_styles():
    st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;600;700;900&family=Space+Mono&display=swap');


  html, body, [class*="css"] { font-family: 'Kanit', sans-serif; }

  [data-testid="stSidebarNav"] { display: none; }

  .rank-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 1rem;
    color: white;
    letter-spacing: 1px;
    text-shadow: 0 1px 3px rgba(0,0,0,0.4);
    margin-right: 6px;
  }

  .player-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 12px;
    padding: 12px 16px;
    margin: 6px 0;
    border-left: 4px solid var(--rank-color, #555);
    color: white;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .protest-meter {
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    color: #aaa;
  }

  .big-title {
    font-size: 2.5rem;
    font-weight: 900;
    background: linear-gradient(90deg, #FFD700, #FF6B35);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.2rem;
  }

  .subtitle {
    text-align: center;
    color: #888;
    margin-bottom: 2rem;
    font-size: 0.95rem;
  }

  .flag-card {
    background: linear-gradient(135deg, #3a0000, #1a0000);
    border: 1px solid #FF4444;
    border-radius: 10px;
    padding: 14px;
    margin: 8px 0;
    color: white;
  }

  .match-category-card {
    background: linear-gradient(135deg, #0f3460, #16213e);
    border-radius: 10px;
    padding: 14px;
    margin: 8px 0;
    color: white;
    border: 1px solid #0f3460;
  }

  .match-category-card.valid {
    border-color: #4CAF50;
    background: linear-gradient(135deg, #1b3a1b, #0f2a0f);
  }


</style>
""", unsafe_allow_html=True)
