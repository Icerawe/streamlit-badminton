import streamlit as st

RANK_COLOR = {
    "BG1":   "#9E9E9E",
    "BG2":   "#795548",
    "N":     "#4CAF50",
    "N+":    "#2196F3",
    "S":     "#FFC107",
    "S+/P-": "#FF9800",
    "P":     "#F44336",
    "P+":    "#B71C1C",
}

RANK_EMOJI = {
    "BG1":   "⬜",
    "BG2":   "🟫",
    "N":     "🟩",
    "N+":    "🟦",
    "S":     "🟨",
    "S+/P-": "🟧",
    "P":     "🟥",
    "P+":    "🔴",
}

RANK_DESC = {
    "BG1":   "ระดับเริ่มต้น — มือใหม่หัดแข่ง",
    "BG2":   "ระดับเริ่มต้น 2 — เริ่มแข่งขันได้",
    "N":     "ระดับ Novice — ตีลูกพื้นฐานครบ",
    "N+":    "ระดับ Novice สูง — rally ดี เริ่มวางเกม",
    "S":     "ระดับ Standard — เล่น rally ยาว เริ่มใช้ tactics",
    "S+/P-": "ระดับ Semi Pro — Knocker / ผู้ช่วย Coach",
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
