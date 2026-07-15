"""
app.py
�??�??�??�??�??�??
Single entry point for AskBVRITH.

Run:  streamlit run app.py

All pages live in pages/ and expose a render() function.
This file owns set_page_config, shared CSS, and st.navigation.
"""

from pathlib import Path

import streamlit as st

ROOT      = Path(__file__).parent
LOGO_PATH = ROOT / "static" / "images" / "bvrith_logo.png"

# �??�?? Must be the FIRST Streamlit call �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
st.set_page_config(
    page_title="AskBVRITH · BVRIT Hyderabad",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# �??�?? Shared CSS (injected once; all pages inherit it) �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

:root {
    --ink:        #10241E;
    --ink-soft:   #3C4F47;
    --ink-faint:  #7C8C85;
    --brand:      #0F6E52;
    --brand-dark: #0B5A42;
    --brand-soft: #E5F3EC;
    --accent:     #C98A2C;
    --line:       #DCE6E0;
    --line-soft:  #E9F0EB;
    --card:       #FFFFFF;
    --warn:       #B7791F;
    --fail:       #B3261E;
    --ok:         #0F6E52;
    --shadow-sm:  0 1px 2px rgba(16,36,30,.05), 0 1px 1px rgba(16,36,30,.04);
    --shadow-md:  0 8px 24px rgba(16,36,30,.07), 0 2px 6px rgba(16,36,30,.04);
    --shadow-lg:  0 18px 40px rgba(16,36,30,.10), 0 4px 12px rgba(16,36,30,.05);
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--ink);
}

/* Force every top-level Streamlit container off the dark theme default.
   Without this, gaps between elements (header, chat input wrapper, bottom
   bar) fall back to the app's base --background-color, which is black
   unless every one of these is pinned explicitly. */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"] {
    background:
        radial-gradient(circle at 15% 0%, rgba(15,110,82,.06) 0%, transparent 45%),
        radial-gradient(circle at 100% 15%, rgba(201,138,44,.05) 0%, transparent 40%),
        #FAFBF9 !important;
}

#MainMenu, footer, .stDeployButton { visibility: hidden; }

header[data-testid="stHeader"], [data-testid="stToolbar"] {
    background: #FAFBF9 !important;
    border-bottom: 1px solid var(--line);
}
[data-testid="stToolbarActions"] button,
[data-testid="stToolbarActions"] a {
    color: var(--ink) !important;
}

.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1150px; }

h1, h2, h3, h4 { font-family: 'Plus Jakarta Sans', sans-serif; letter-spacing: -0.01em; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FFFFFF 0%, #F3F8F5 100%);
    border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] * { color: var(--ink-soft); }

/* �??�?? Chat page �??�?? */
.hero-card {
    background: linear-gradient(135deg, #FFFFFF 0%, #F1F8F4 100%);
    border: 1px solid var(--line); border-left: 5px solid var(--brand);
    border-radius: 18px; padding: 1.4rem 1.7rem; margin-bottom: 1.4rem;
    box-shadow: var(--shadow-md);
}
.hero-card h1 { font-size:1.6rem; font-weight:800; color:var(--brand-dark); margin:0 0 .4rem; line-height:1.25; }
.hero-card p  { color:var(--ink-soft); font-size:.94rem; margin:0; line-height:1.6; }

.welcome-card {
    background: var(--card); border:1px solid var(--line-soft); border-radius:16px;
    padding:1.2rem 1.4rem; margin:.5rem 0 1.1rem;
    box-shadow: var(--shadow-sm);
}
.welcome-card h3 { color:var(--brand-dark); font-size:1.02rem; font-weight:700; margin:0 0 .7rem; }
.welcome-card ul { margin:0; padding-left:1.15rem; color:var(--ink-soft); font-size:.89rem; line-height:1.7; }

.quick-label {
    font-size:.76rem; font-weight:700; color:var(--ink-faint);
    text-transform:uppercase; letter-spacing:.08em; margin:.25rem 0 .6rem;
}

.overview-card-row { display:flex; flex-wrap:wrap; gap:1.1rem; margin-bottom:1.1rem; }
.overview-card {
    flex:1 1 190px; background: var(--card); border:1px solid var(--line-soft);
    border-radius:18px; padding:1.1rem 1.15rem .9rem;
    box-shadow: var(--shadow-md);
    transition: transform .15s ease, box-shadow .15s ease;
}
.overview-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
.overview-card-title {
    color:var(--brand); font-size:.78rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.09em; margin-bottom:.6rem;
}
.overview-card-value { font-size:1.85rem; font-weight:800; color:var(--ink); margin-bottom:.5rem; }
.overview-card-note  { color:var(--ink-faint); font-size:.83rem; line-height:1.55; }

.source-box {
    background: var(--brand-soft); border-left:4px solid var(--brand);
    border-radius:10px; padding:9px 13px; font-size:.83rem; color:var(--brand-dark); margin-top:9px;
}
.routing-badge {
    display:inline-block; background:#FFFFFF; color:var(--brand-dark);
    border:1px solid var(--line); border-radius:999px;
    font-size:.68rem; font-weight:700; padding:3px 11px; margin-bottom:7px;
    box-shadow: var(--shadow-sm);
}
.latency-tag { font-size:.72rem; color:var(--ink-faint); margin-top:7px; font-family:'JetBrains Mono', monospace; }

div[data-testid="stChatInput"] {
    background: transparent !important;
}
/* Let the input's own inner container be the ONLY element that owns a
   border + radius. Every other wrapper layer gets its border stripped so
   we don't stack two rounded rectangles on top of each other (that's what
   caused the crescent/overlap artifact). */
div[data-testid="stChatInput"] > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
div[data-testid="stChatInput"] [data-baseweb="base-input"],
div[data-testid="stChatInput"] [data-baseweb="textarea"] {
    background: #FFFFFF !important;
    border-radius: 16px !important;
    border: 1.5px solid var(--line) !important;
    box-shadow: var(--shadow-md);
}
div[data-testid="stChatInput"] textarea {
    border-radius: 16px !important;
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    color: var(--ink) !important;
}
div[data-testid="stChatInput"] [data-baseweb="base-input"]:focus-within,
div[data-testid="stChatInput"] [data-baseweb="textarea"]:focus-within {
    border-color: var(--brand) !important;
    box-shadow:0 0 0 3px rgba(15,110,82,.14) !important;
}
div[data-testid="stChatInput"] button {
    color: var(--brand) !important;
}
div[data-testid="stChatMessage"] {
    border-radius:20px !important; padding:1.1rem 1.2rem !important;
    margin-bottom:.9rem !important; background: var(--card) !important;
    border:1px solid var(--line-soft) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* �??�?? Governance page �??�?? */
.score-grid {
    display:grid; grid-template-columns:repeat(4,1fr); gap:.95rem; margin-bottom:1.5rem;
}
.score-card {
    background: var(--card); border:1px solid var(--line-soft); border-top:4px solid var(--brand);
    border-radius:16px; padding:1.1rem 1.15rem 1rem;
    box-shadow: var(--shadow-md); text-align:center;
    transition: transform .15s ease;
}
.score-card:hover { transform: translateY(-2px); }
.score-card.warn { border-top-color: var(--warn); }
.score-card.fail { border-top-color: var(--fail); }
.score-card.na   { border-top-color:#90A4AE; }
.score-num       { font-size:2.1rem; font-weight:800; color:var(--brand-dark); line-height:1.1; }
.score-num.warn  { color:#95610E; }
.score-num.fail  { color:var(--fail); }
.score-num.na    { color:#607D8B; }
.score-label     { font-size:.73rem; font-weight:700; color:var(--ink-faint); text-transform:uppercase; letter-spacing:.08em; margin-top:.35rem; }
.score-sub       { font-size:.79rem; color:var(--ink-faint); margin-top:.25rem; line-height:1.45; }

.cat-pill {
    display:inline-flex; align-items:center; gap:.45rem;
    background: var(--brand-soft); border:1px solid #BFE0CE; border-radius:999px;
    padding:.32rem .95rem; font-size:.8rem; font-weight:700; color:var(--brand-dark); margin-bottom:.75rem;
}
.gov-section {
    font-size:.78rem; font-weight:700; color:var(--brand); text-transform:uppercase;
    letter-spacing:.08em; margin:1.2rem 0 .45rem;
    border-bottom:1px solid var(--line); padding-bottom:.3rem;
}
.gov-hero {
    background: linear-gradient(135deg, #FFFFFF 0%, #F1F8F4 100%);
    border:1px solid var(--line); border-left:5px solid var(--brand);
    border-radius:18px; padding:1.2rem 1.6rem; margin-bottom:1.4rem;
    box-shadow: var(--shadow-md);
}
.gov-hero h1 { font-size:1.6rem; font-weight:800; color:var(--brand-dark); margin:0 0 .35rem; }
.gov-hero p  { color:var(--ink-soft); font-size:.92rem; margin:0; line-height:1.6; }

/* �??�?? Evaluation page �??�?? */
.summary-banner {
    background: linear-gradient(135deg, #F1F8F4 0%, #FFFFFF 100%);
    border:1.5px solid #BFE0CE; border-left:6px solid var(--brand);
    border-radius:18px; padding:1.3rem 1.7rem; margin-bottom:1.4rem;
    box-shadow: var(--shadow-lg);
}
.summary-banner h2 { font-size:1.12rem; font-weight:800; color:var(--brand-dark); margin:0 0 .75rem; }
.summary-stat-row  { display:flex; flex-wrap:wrap; gap:1.6rem; align-items:center; }
.summary-stat      { text-align:center; min-width:82px; }
.summary-stat-num  { font-size:2.1rem; font-weight:800; line-height:1.05; color:var(--brand-dark); }
.summary-stat-num.fail { color:var(--fail); }
.summary-stat-num.warn { color:#95610E; }
.summary-stat-num.pct  { color:var(--ok); }
.summary-stat-label    { font-size:.73rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; color:var(--ink-faint); margin-top:.2rem; }
.summary-divider       { width:1px; height:50px; background:var(--line); }

.dim-table { width:100%; border-collapse:separate; border-spacing:0 7px; margin-bottom:.6rem; }
.dim-table th { font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; color:var(--ink-faint); padding:0 12px 7px; border-bottom:2px solid var(--line); }
.dim-table td { padding:11px 13px; font-size:.89rem; background: var(--card); border-top:1px solid var(--line-soft); border-bottom:1px solid var(--line-soft); }
.dim-table td:first-child { border-left:1px solid var(--line-soft); border-radius:10px 0 0 10px; }
.dim-table td:last-child  { border-right:1px solid var(--line-soft); border-radius:0 10px 10px 0; }
.dim-table tr.dim-row-pass td { border-left:4px solid var(--brand) !important; }
.dim-table tr.dim-row-warn td { border-left:4px solid var(--warn) !important; }
.dim-table tr.dim-row-fail td { border-left:4px solid var(--fail) !important; }

.prog-bar-bg   { background:var(--line-soft); border-radius:999px; height:8px; width:120px; display:inline-block; vertical-align:middle; }
.prog-bar-fill { height:8px; border-radius:999px; background: var(--brand); }
.prog-bar-fill.warn { background: var(--warn); }
.prog-bar-fill.fail { background: var(--fail); }

.diagnosis-box { border-radius:16px; padding:1.1rem 1.3rem; margin-bottom:1rem; box-shadow: var(--shadow-sm); }
.diagnosis-box.weakest { background:#FDF6E8; border:1px solid #F0DDA8; border-left:5px solid var(--accent); }
.diagnosis-box.ragas   { background: var(--brand-soft); border:1px solid #BFE0CE; border-left:5px solid var(--brand); }
.diagnosis-box h3 { font-size:.96rem; font-weight:700; margin:0 0 .45rem; color:var(--ink); }
.diagnosis-box p  { font-size:.87rem; color:var(--ink-soft); margin:0; line-height:1.6; }
.fix-label { font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; color:var(--accent); margin-top:.55rem; margin-bottom:.25rem; }

.ragas-row  { display:flex; flex-wrap:wrap; gap:.9rem; margin:.65rem 0 .85rem; }
.ragas-pill { background: var(--card); border:1.5px solid var(--line); border-radius:14px; padding:.65rem 1.05rem; min-width:130px; text-align:center; box-shadow: var(--shadow-sm); }
.ragas-pill.lowest { border-color:#F0DDA8; background:#FDF6E8; }
.ragas-pill-num    { font-size:1.6rem; font-weight:800; color:var(--brand-dark); line-height:1.1; }
.ragas-pill-num.lowest { color:#95610E; }
.ragas-pill-label  { font-size:.7rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:var(--ink-faint); margin-top:.25rem; }

/* �??�?? Shared badges & sidebar �??�?? */
.badge-ok   { color: var(--brand); font-weight:700; }
.badge-warn { color:#95610E; font-weight:700; }
.badge-pass { background: var(--brand-soft); color:var(--brand-dark); border:1px solid #BFE0CE; border-radius:999px; padding:3px 11px; font-size:.72rem; font-weight:700; }
.badge-fail { background:#FBEAE8; color:var(--fail); border:1px solid #EFC3BE; border-radius:999px; padding:3px 11px; font-size:.72rem; font-weight:700; }

.section-title {
    font-size:.78rem; font-weight:700; color:var(--brand); text-transform:uppercase;
    letter-spacing:.08em; margin:1.2rem 0 .55rem;
    border-bottom:1px solid var(--line); padding-bottom:.3rem;
}
.sidebar-section {
    font-size:.76rem; font-weight:700; color:var(--brand-dark);
    text-transform:uppercase; letter-spacing:.06em; margin:.7rem 0 .4rem;
}
.sidebar-footer { font-size:.68rem; color:var(--ink-faint); text-align:center; line-height:1.6; margin-top:1.1rem; }

/* �??�?? Sidebar st.metric widgets (Live Observability) �??�??
   Native st.metric truncates in narrow sidebar columns unless we let the
   label wrap and shrink the value font a touch. */
[data-testid="stSidebar"] div[data-testid="stMetric"] {
    background: var(--card);
    border: 1px solid var(--line-soft);
    border-radius: 12px;
    padding: .6rem .7rem .55rem;
    box-shadow: var(--shadow-sm);
    margin-bottom: .55rem;
}
[data-testid="stSidebar"] div[data-testid="stMetricLabel"] {
    overflow: visible !important;
    white-space: normal !important;
}
[data-testid="stSidebar"] div[data-testid="stMetricLabel"] p {
    font-size: .68rem !important;
    font-weight: 700 !important;
    color: var(--ink-faint) !important;
    text-transform: uppercase;
    letter-spacing: .04em;
    white-space: normal !important;
    line-height: 1.25 !important;
}
[data-testid="stSidebar"] div[data-testid="stMetricValue"] {
    font-size: 1.25rem !important;
    font-weight: 800 !important;
    color: var(--brand-dark) !important;
    overflow: visible !important;
    white-space: normal !important;
    word-break: break-word;
}

/* �??�?? Session Stats (custom grid, replaces plain markdown lines) �??�?? */
.session-stats-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: .5rem;
    margin-bottom: .3rem;
}
.session-stat {
    background: var(--card); border: 1px solid var(--line-soft);
    border-radius: 12px; padding: .5rem .65rem;
    display: flex; flex-direction: column; gap: .15rem;
    box-shadow: var(--shadow-sm);
}
.session-stat-label {
    font-size: .64rem; font-weight: 700; color: var(--ink-faint);
    text-transform: uppercase; letter-spacing: .04em;
}
.session-stat-value {
    font-size: .92rem; font-weight: 700; color: var(--ink);
    overflow-wrap: break-word;
}
</style>
""", unsafe_allow_html=True)

# �??�?? Shared sidebar brand block �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    st.markdown(
        '<p style="text-align:center;font-size:1.15rem;font-weight:800;color:#0B5A42;margin:.5rem 0 .15rem;letter-spacing:-.01em">AskBVRITH</p>'
        '<p style="text-align:center;font-size:.73rem;color:#3C4F47;letter-spacing:.07em;text-transform:uppercase">College Information Assistant</p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

# �??�?? Navigation �??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??�??
from pages.chat       import render as _chat_render
from pages.governance import render as _gov_render
from pages.evaluation import render as _eval_render

pg = st.navigation(
    [
        st.Page(_chat_render,  title="💬 Chat",        url_path="chat"),
        st.Page(_gov_render,   title="🏛️ Governance",  url_path="governance"),
        st.Page(_eval_render,  title="🧪 Evaluation",  url_path="evaluation"),
    ],
    position="sidebar",
)
pg.run()

