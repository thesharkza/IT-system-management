import streamlit as st
import pandas as pd
import base64
from datetime import datetime
from supabase import create_client, Client
from streamlit_calendar import calendar
from dateutil.relativedelta import relativedelta
from fpdf import FPDF
import io
import tempfile
import os
import uuid

st.set_page_config(
    page_title="ILT IT Helpdesk",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

:root {
    --navy:        #0B1829;
    --navy-mid:    #112240;
    --navy-light:  #1A3356;
    --blue:        #1E6FD9;
    --blue-light:  #3B8FFF;
    --blue-glow:   rgba(30,111,217,0.18);
    --accent:      #00C6FF;
    --success:     #10B981;
    --warn:        #F59E0B;
    --danger:      #EF4444;
    --purple:      #8B5CF6;
    --text-primary:   #E8EDF5;
    --text-secondary: #8BA0BC;
    --text-muted:     #4A6080;
    --border:      rgba(30,111,217,0.25);
    --border-subtle: rgba(255,255,255,0.07);
    --card-bg:     rgba(17,34,64,0.90);
    --sidebar-bg:  #0D1F38;
    --radius:      12px;
    --radius-lg:   18px;
    --shadow:      0 4px 24px rgba(0,0,0,0.35);
    --shadow-blue: 0 4px 20px rgba(30,111,217,0.3);
}

/* ── Global ── */
html, body, [class*="css"], .stApp {
    font-family: 'Noto Sans Thai', sans-serif !important;
    background-color: var(--navy) !important;
    color: var(--text-primary) !important;
}
/* lock ตัวหนังสือทุกตัวในแอป */
p, span, div, label, li, td, th, h1, h2, h3, h4, h5, h6,
.stMarkdown, .stText, [class*="css"] {
    color: var(--text-primary) !important;
}
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(30,111,217,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(30,111,217,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }
[data-testid="stSidebar"] hr { border-color: var(--border) !important; margin: 12px 0 !important; }
[data-testid="stSidebar"] h1 {
    font-size: 15px !important; font-weight: 600 !important;
    color: var(--text-muted) !important; text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
}
/* radio nav */
[data-testid="stSidebar"] div[role="radiogroup"] { gap: 4px !important; }
[data-testid="stSidebar"] div[role="radiogroup"] label {
    display: flex !important; align-items: center !important;
    padding: 11px 16px !important; border-radius: 10px !important;
    margin-bottom: 3px !important; border: 1px solid transparent !important;
    transition: all 0.18s ease !important; width: 100% !important;
    cursor: pointer !important; background: transparent !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(30,111,217,0.12) !important; border-color: var(--border) !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label p {
    font-size: 14px !important; font-weight: 500 !important;
    color: var(--text-secondary) !important; margin: 0 !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] [data-checked="true"] {
    background: linear-gradient(135deg, var(--blue), #1557B0) !important;
    border-color: var(--blue-light) !important;
    box-shadow: var(--shadow-blue) !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] [data-checked="true"] p {
    color: #fff !important; font-weight: 600 !important;
}
[data-testid="stSidebar"] .st-bo { display: none !important; }

/* ── Main ── */
.main .block-container { padding: 28px 36px !important; max-width: 1400px !important; }
h1 { font-size: 26px !important; font-weight: 700 !important; color: var(--text-primary) !important; letter-spacing: -0.01em !important; }
h2 { font-size: 20px !important; font-weight: 600 !important; color: var(--text-primary) !important; }
h3 { font-size: 15px !important; font-weight: 600 !important; color: var(--text-secondary) !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; }

/* ── Metric Cards ── */
[data-testid="metric-container"] {
    background: var(--card-bg) !important; border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important; padding: 20px 24px !important;
    backdrop-filter: blur(12px) !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
}
[data-testid="metric-container"]:hover { transform: translateY(-2px) !important; box-shadow: var(--shadow-blue) !important; border-color: var(--blue) !important; }
[data-testid="metric-container"] label { font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; color: var(--text-secondary) !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { font-family: 'DM Mono', monospace !important; font-size: 28px !important; font-weight: 500 !important; color: var(--text-primary) !important; }

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] { border-bottom: 2px solid var(--border) !important; gap: 4px !important; background: transparent !important; }
[data-testid="stTabs"] [role="tab"] { font-size: 13px !important; font-weight: 500 !important; color: var(--text-secondary) !important; padding: 10px 20px !important; border-radius: 8px 8px 0 0 !important; border: 1px solid transparent !important; border-bottom: none !important; transition: all 0.15s ease !important; background: transparent !important; }
[data-testid="stTabs"] [role="tab"]:hover { color: var(--text-primary) !important; background: var(--blue-glow) !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: var(--accent) !important; border-color: var(--border) !important; background: var(--card-bg) !important; font-weight: 600 !important; }
[data-testid="stTabContent"] { padding-top: 20px !important; }

/* ── Buttons ── */
.stButton > button {
    font-family: 'Noto Sans Thai', sans-serif !important; font-size: 13px !important;
    font-weight: 600 !important; background: linear-gradient(135deg, var(--blue) 0%, #1557B0 100%) !important;
    color: #fff !important; border: none !important; border-radius: 8px !important;
    padding: 10px 22px !important; transition: all 0.18s ease !important;
    box-shadow: 0 2px 12px rgba(30,111,217,0.25) !important;
}
.stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 6px 20px rgba(30,111,217,0.45) !important; }
[data-testid="stDownloadButton"] > button {
    background: transparent !important; border: 1px solid var(--blue) !important;
    color: var(--blue-light) !important; border-radius: 8px !important;
    font-size: 13px !important; font-weight: 500 !important; padding: 9px 18px !important;
    transition: all 0.18s ease !important;
}
[data-testid="stDownloadButton"] > button:hover { background: var(--blue-glow) !important; color: #fff !important; }
[data-testid="stFormSubmitButton"] > button {
    font-family: 'Noto Sans Thai', sans-serif !important;
    background: linear-gradient(135deg, var(--blue) 0%, #1557B0 100%) !important;
    color: #fff !important; border: none !important; border-radius: 8px !important;
    font-size: 14px !important; font-weight: 600 !important;
    padding: 11px 28px !important; width: 100% !important;
    transition: all 0.18s ease !important; box-shadow: var(--shadow-blue) !important;
}
[data-testid="stFormSubmitButton"] > button:hover { transform: translateY(-1px) !important; }

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
    background: var(--navy-mid) !important; border: 1px solid var(--border) !important;
    border-radius: 8px !important; color: var(--text-primary) !important;
    font-family: 'Noto Sans Thai', sans-serif !important; font-size: 13px !important;
    padding: 10px 14px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus { border-color: var(--blue) !important; box-shadow: 0 0 0 3px var(--blue-glow) !important; }
[data-testid="stTextInput"] label, [data-testid="stTextArea"] label,
[data-testid="stNumberInput"] label, [data-testid="stSelectbox"] label,
[data-testid="stDateInput"] label, [data-testid="stFileUploader"] label {
    font-size: 12px !important; font-weight: 600 !important;
    color: var(--text-secondary) !important; text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}
[data-testid="stSelectbox"] > div > div {
    background: var(--navy-mid) !important; border: 1px solid var(--border) !important;
    border-radius: 8px !important; color: var(--text-primary) !important;
}
[data-testid="stDateInput"] input { background: var(--navy-mid) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; color: var(--text-primary) !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: var(--radius) !important; overflow: hidden !important; border: 1px solid var(--border) !important; }

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: var(--radius) !important; border: 1px solid !important; font-size: 13px !important; }
[data-testid="stAlert"] p { color: inherit !important; }

/* ── Expander ── */
[data-testid="stExpander"] { background: var(--card-bg) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; overflow: hidden !important; }
[data-testid="stExpander"] summary { font-size: 13px !important; font-weight: 600 !important; color: var(--text-primary) !important; padding: 14px 18px !important; }
[data-testid="stExpander"] summary:hover { background: var(--blue-glow) !important; }

/* ── Divider ── */
hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 20px 0 !important; }

/* ── File Uploader ── */
[data-testid="stFileUploader"] > div { background: var(--navy-mid) !important; border: 1px dashed var(--border) !important; border-radius: var(--radius) !important; }
[data-testid="stFileUploader"] > div:hover { border-color: var(--blue) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--navy); }
::-webkit-scrollbar-thumb { background: var(--navy-light); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: var(--blue); }

/* ── Toast ── */
[data-testid="stToast"] { background: var(--navy-mid) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; color: var(--text-primary) !important; }

/* ── Form Container ── */
[data-testid="stForm"] { background: var(--card-bg) !important; border: 1px solid var(--border) !important; border-radius: var(--radius-lg) !important; padding: 24px !important; }

/* ── Sidebar brand / login ── */
.sidebar-brand { padding: 20px 16px 12px; border-bottom: 1px solid var(--border); margin-bottom: 12px; }
.sidebar-brand-title { font-size: 18px; font-weight: 700; color: var(--text-primary); margin: 0; }
.sidebar-brand-sub { font-size: 11px; color: var(--text-muted); font-family: 'DM Mono', monospace; margin: 2px 0 0 0; letter-spacing: 0.05em; }
.login-box { background: rgba(255,255,255,0.04); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; margin: 0 0 10px 0; }
.login-box-title { font-size: 11px; font-weight: 600; color: var(--text-muted) !important; text-transform: uppercase; letter-spacing: 0.1em; margin: 0 0 8px 0; }
.admin-badge { display: flex; align-items: center; gap: 8px; background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.3); border-radius: 8px; padding: 10px 14px; margin-bottom: 10px; }
.admin-dot { width: 8px; height: 8px; border-radius: 50%; background: #10B981; box-shadow: 0 0 6px #10B981; flex-shrink: 0; }
.admin-badge-text { font-size: 12px; font-weight: 600; color: #6EE7B7 !important; margin: 0; }
.nav-section-label { font-size: 10px; font-weight: 700; color: var(--text-muted) !important; text-transform: uppercase; letter-spacing: 0.14em; padding: 0 4px; margin: 4px 0 8px 0; }
[data-testid="stSidebar"] .stButton > button { background: linear-gradient(135deg, var(--blue), #1557B0) !important; color: #fff !important; border: none !important; border-radius: 8px !important; font-size: 13px !important; font-weight: 600 !important; padding: 10px 18px !important; width: 100% !important; box-shadow: var(--shadow-blue) !important; }
[data-testid="stSidebar"] .stTextInput input { background: rgba(255,255,255,0.06) !important; border-color: var(--border) !important; color: var(--text-primary) !important; }
[data-testid="stSidebar"] .stRadio input[type="radio"] { display: none !important; }
[data-testid="stSidebar"] .stRadio > div > label > div:first-child { display: none !important; }
[data-testid="stSidebar"] .stRadio > label { display: none !important; }

/* ── Ticket Card (แทนตาราง) ── */
.ticket-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px 18px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 16px;
    transition: all 0.16s ease;
}
.ticket-card:hover { border-color: var(--blue); box-shadow: var(--shadow-blue); transform: translateX(2px); }
.ticket-card-left { flex: 0 0 auto; }
.ticket-id { font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 500; color: var(--accent) !important; }
.ticket-user { font-size: 14px; font-weight: 600; color: var(--text-primary) !important; margin: 2px 0; }
.ticket-date { font-size: 11px; color: var(--text-muted) !important; }
.ticket-card-mid { flex: 1; }
.ticket-cat { font-size: 12px; color: var(--text-secondary) !important; }
.ticket-urgency-ด่วนมาก { color: #FCA5A5 !important; font-weight: 600; font-size: 11px; }
.ticket-urgency-ด่วน      { color: #FCD34D !important; font-weight: 600; font-size: 11px; }
.ticket-urgency-ปกติ      { color: var(--text-muted) !important; font-size: 11px; }
.ticket-card-right { flex: 0 0 auto; text-align: right; }
.ticket-rating { font-size: 12px; color: var(--warn) !important; }

/* Status badges */
.status-badge {
    display: inline-block; padding: 3px 10px; border-radius: 99px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.03em;
}
.status-รอตรวจสอบ { background: rgba(239,68,68,0.15);   color: #FCA5A5 !important; border: 1px solid rgba(239,68,68,0.35); }
.status-ดำเนินการ  { background: rgba(245,158,11,0.15);  color: #FCD34D !important; border: 1px solid rgba(245,158,11,0.35); }
.status-ส่งซ่อม   { background: rgba(139,92,246,0.15);  color: #C4B5FD !important; border: 1px solid rgba(139,92,246,0.35); }
.status-สำเร็จ     { background: rgba(16,185,129,0.15);  color: #6EE7B7 !important; border: 1px solid rgba(16,185,129,0.35); }

/* ── CSAT table ── */
.csat-table { width: 100%; border-collapse: collapse; }
.csat-table th { font-size: 11px; font-weight: 700; color: var(--text-muted) !important; text-transform: uppercase; letter-spacing: 0.08em; padding: 8px 12px; border-bottom: 1px solid var(--border); text-align: left; }
.csat-table td { padding: 10px 12px; border-bottom: 1px solid var(--border-subtle); font-size: 13px; color: var(--text-primary) !important; }
.csat-table td:first-child { text-align: left; }
.csat-table td:last-child { text-align: right; font-family: 'DM Mono', monospace; }
.csat-bar-wrap { background: rgba(255,255,255,0.07); border-radius: 99px; height: 6px; width: 120px; display: inline-block; vertical-align: middle; margin-right: 8px; }
.csat-bar { height: 6px; border-radius: 99px; background: linear-gradient(90deg, var(--blue), var(--accent)); }

/* ── Feedback cards ── */
.feedback-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 18px; margin-bottom: 8px; }
.feedback-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.feedback-user { font-size: 13px; font-weight: 600; color: var(--text-primary) !important; }
.feedback-date { font-size: 11px; color: var(--text-muted) !important; }
.feedback-text { font-size: 13px; color: var(--text-secondary) !important; line-height: 1.6; }
.feedback-stars { color: var(--warn) !important; font-size: 13px; }

/* ── Chart wrapper ── */
.chart-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; }
.chart-title { font-size: 13px; font-weight: 600; color: var(--text-secondary) !important; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 16px; }

/* ── PM Coverage ── */
.pm-bar-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.pm-bar-label { font-size: 13px; color: var(--text-primary) !important; width: 100px; flex-shrink: 0; }
.pm-bar-track { flex: 1; background: rgba(255,255,255,0.07); border-radius: 99px; height: 10px; }
.pm-bar-fill-green { height: 10px; border-radius: 99px; background: linear-gradient(90deg, #059669, #10B981); }
.pm-bar-fill-blue  { height: 10px; border-radius: 99px; background: linear-gradient(90deg, var(--blue), var(--blue-light)); }
.pm-bar-pct { font-family: 'DM Mono', monospace; font-size: 12px; color: var(--text-secondary) !important; width: 44px; text-align: right; flex-shrink: 0; }

/* ── Fade-in ── */
@keyframes fadeUp { from { opacity:0; transform:translateY(10px);} to {opacity:1; transform:translateY(0);} }
.main .block-container > * { animation: fadeUp 0.28s ease both; }

/* selectbox dropdown background */
[data-baseweb="popover"] { background: var(--navy-mid) !important; }
[data-baseweb="menu"] { background: var(--navy-mid) !important; }
[data-baseweb="option"] { background: var(--navy-mid) !important; color: var(--text-primary) !important; }
[data-baseweb="option"]:hover { background: var(--navy-light) !important; }

/* ── Top Navigation Bar (Main Page) ── */
.top-nav-wrap {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 8px;
    margin: 0 0 22px 0;
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    overflow-x: auto;
}
.top-nav-btn-group { display: flex; gap: 6px; flex: 1; flex-wrap: wrap; }

/* เปลี่ยนปุ่ม top-nav (ใช้ st.button) ให้ดูเป็น tab */
.top-nav-wrap [data-testid="stHorizontalBlock"] [data-testid="stButton"] > button,
.top-nav-row [data-testid="stButton"] > button {
    background: transparent !important;
    color: var(--text-secondary) !important;
    border: 1px solid transparent !important;
    box-shadow: none !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 9px 14px !important;
    border-radius: 10px !important;
    white-space: nowrap !important;
}
.top-nav-row [data-testid="stButton"] > button:hover {
    background: rgba(30,111,217,0.1) !important;
    color: var(--text-primary) !important;
    border-color: rgba(30,111,217,0.3) !important;
    transform: none !important;
}
.top-nav-row .top-nav-active [data-testid="stButton"] > button {
    background: linear-gradient(135deg, var(--blue), #1557B0) !important;
    color: #fff !important;
    border-color: var(--blue-light) !important;
    box-shadow: var(--shadow-blue) !important;
    font-weight: 600 !important;
}

/* ── ซ่อน Streamlit menu / footer ── */
#MainMenu, footer { visibility: hidden !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* header โปร่งใส แต่ยังคงไว้เพื่อให้ปุ่ม sidebar collapse ของ Streamlit ทำงาน */
header[data-testid="stHeader"] {
    background: transparent !important;
}

/* ── ทำให้ปุ่ม sidebar collapse ของ Streamlit เห็นชัด สีส้ม ── */
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button,
[data-testid="collapsedControl"] {
    background: linear-gradient(135deg, #F59E0B, #EA580C) !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 16px rgba(245,158,11,0.55) !important;
}
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg {
    color: #ffffff !important;
    fill: #ffffff !important;
    stroke: #ffffff !important;
    width: 22px !important;
    height: 22px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar brand ──
st.sidebar.markdown("""
<div class="sidebar-brand">
  <p class="sidebar-brand-title">🛠️ ILT Helpdesk</p>
  <p class="sidebar-brand-sub">IT SERVICE MANAGEMENT</p>
</div>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- HELPER FUNCTIONS ---
def load_table(table_name):
    try:
        if table_name == "tickets":
            cols = "id, date, user, dept, category, equipment_type, desc, status, urgency, asset_id, location, assignee, root_cause, solution, cost, q1, q2, q3, q4, q5, rating, feedback"
            response = supabase.table(table_name).select(cols).execute()
        else:
            response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"🚨 เกิดข้อผิดพลาดในการดึงข้อมูลจากตาราง '{table_name}': {str(e)}")
        return pd.DataFrame()

def insert_data(table_name, data_dict):
    supabase.table(table_name).insert(data_dict).execute()

def update_ticket_full(record_id, status, assignee, root_cause, solution, cost):
    supabase.table("tickets").update({
        "status": status, "assignee": assignee, "root_cause": root_cause,
        "solution": solution, "cost": cost
    }).eq("id", record_id).execute()

def update_csat_full(record_id, q1, q2, q3, q4, q5, feedback):
    avg_score = (q1 + q2 + q3 + q4 + q5) / 5
    supabase.table("tickets").update({
        "q1": int(q1), "q2": int(q2), "q3": int(q3), "q4": int(q4), "q5": int(q5),
        "feedback": feedback, "rating": round(avg_score, 2)
    }).eq("id", record_id).execute()

def update_pm_full(record_id, status, pm_result):
    supabase.table("pm_schedules").update({
        "status": status, "pm_result": pm_result
    }).eq("id", record_id).execute()

def update_asset(asset_id, data_dict):
    supabase.table("assets").update(data_dict).eq("id", asset_id).execute()

def delete_asset(asset_id):
    supabase.table("assets").delete().eq("id", asset_id).execute()

def update_ticket_user_fields(ticket_id, data_dict):
    """แก้ไขฟิลด์ที่ user มีสิทธิ์แก้ — เฉพาะงาน status='รอตรวจสอบ' เท่านั้น"""
    supabase.table("tickets").update(data_dict).eq("id", ticket_id).eq("status", "รอตรวจสอบ").execute()

def delete_ticket(ticket_id):
    """ลบ ticket — เฉพาะงาน status='รอตรวจสอบ' เท่านั้น เพื่อความปลอดภัย"""
    supabase.table("tickets").delete().eq("id", ticket_id).eq("status", "รอตรวจสอบ").execute()

# =========================================================
# 🔔 TELEGRAM NOTIFICATION MODULE
# =========================================================
import requests

def _tg_config():
    """อ่าน config จาก secrets — คืน (token, chat_id, enabled)"""
    try:
        token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = st.secrets.get("TELEGRAM_CHAT_ID", "")
        enabled = st.secrets.get("TELEGRAM_ENABLED", True)
        return token, chat_id, enabled
    except Exception:
        return "", "", False

def send_telegram(message: str, parse_mode: str = "Markdown", silent: bool = False) -> tuple:
    """
    ส่งข้อความเข้า Telegram chat ที่กำหนดใน secrets
    คืน (success: bool, info: str)
    """
    token, chat_id, enabled = _tg_config()
    if not enabled:
        return False, "Telegram ถูกปิดไว้ใน config"
    if not token or not chat_id:
        return False, "ยังไม่ได้ตั้งค่า TELEGRAM_BOT_TOKEN หรือ TELEGRAM_CHAT_ID ใน secrets"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode,
        "disable_notification": silent,
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=8)
        if r.status_code == 200:
            return True, "ส่งสำเร็จ"
        return False, f"HTTP {r.status_code}: {r.text[:120]}"
    except Exception as e:
        return False, f"Error: {str(e)[:120]}"

def _tg_escape(text: str) -> str:
    """escape ตัวอักษรพิเศษของ Markdown ของ Telegram"""
    if text is None: return "—"
    s = str(text)
    for ch in ['_','*','`','[']:
        s = s.replace(ch, '\\' + ch)
    return s

def notify_new_ticket(ticket: dict):
    """แจ้งเตือนเมื่อมี ticket ใหม่"""
    urgency = ticket.get('urgency','ปกติ')
    icon = "🚨" if urgency == "ด่วนมาก" else ("⚡" if urgency == "ด่วน" else "🆕")
    silent = (urgency == "ปกติ")
    msg = (
        f"{icon} *งานแจ้งซ่อมใหม่*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 `{ticket.get('id','')}`\n"
        f"👤 *ผู้แจ้ง:* {_tg_escape(ticket.get('user',''))}\n"
        f"🏢 *แผนก:* {_tg_escape(ticket.get('dept',''))}\n"
        f"📂 *ประเภท:* {_tg_escape(ticket.get('category',''))}\n"
        f"🖥️ *อุปกรณ์:* {_tg_escape(ticket.get('equipment_type',''))}\n"
        f"📍 *สถานที่:* {_tg_escape(ticket.get('location','—'))}\n"
        f"⚡ *เร่งด่วน:* {_tg_escape(urgency)}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📝 _{_tg_escape(ticket.get('desc',''))[:200]}_"
    )
    return send_telegram(msg, silent=silent)

def notify_ticket_closed(ticket: dict, assignee: str = "", cost: float = 0.0):
    """แจ้งเตือนเมื่อปิดงาน"""
    msg = (
        f"✅ *ปิดงานซ่อมสำเร็จ*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 `{ticket.get('id','')}`\n"
        f"🔧 *ช่างผู้รับผิดชอบ:* {_tg_escape(assignee or '—')}\n"
        f"💰 *ค่าใช้จ่าย:* {cost:,.2f} บาท\n"
        f"👤 *ผู้แจ้ง:* {_tg_escape(ticket.get('user',''))}"
    )
    return send_telegram(msg, silent=True)

def notify_pm_overdue(pm: dict, days_late: int):
    """แจ้งเตือน PM เลยกำหนด"""
    msg = (
        f"🚨 *งาน PM เลยกำหนด {days_late} วัน*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📋 *งาน:* {_tg_escape(pm.get('task_name',''))}\n"
        f"🖥️ *อุปกรณ์:* {_tg_escape(pm.get('asset_id','—'))}\n"
        f"👷 *ผู้รับผิดชอบ:* {_tg_escape(pm.get('assignee','—'))}\n"
        f"📅 *กำหนดเดิม:* {_tg_escape(pm.get('next_due_date',''))}"
    )
    return send_telegram(msg, silent=False)

def send_daily_summary():
    """รายงานสรุปประจำวัน"""
    df = load_table("tickets")
    df_pm = load_table("pm_schedules")
    today_str = datetime.now().strftime("%d %b %Y")

    if df.empty:
        return send_telegram(f"📊 *รายงานประจำวัน — {today_str}*\nยังไม่มีข้อมูลในระบบ")

    pending  = len(df[df['status'] == 'รอตรวจสอบ'])
    inprog   = len(df[df['status'] == 'ดำเนินการ'])
    sending  = len(df[df['status'] == 'ส่งซ่อม'])
    done     = len(df[df['status'] == 'สำเร็จ'])
    urgent   = len(df[(df['status'] != 'สำเร็จ') & (df['urgency'] == 'ด่วนมาก')])

    # PM งานที่ครบกำหนดวันนี้/พรุ่งนี้
    pm_today_txt = ""
    if not df_pm.empty:
        df_pm['_due'] = pd.to_datetime(df_pm['next_due_date']).dt.date
        today_d = datetime.now().date()
        tomorrow_d = today_d + relativedelta(days=1)
        overdue = df_pm[(df_pm['_due'] < today_d) & (df_pm['status'] != 'Completed')]
        upcoming = df_pm[((df_pm['_due'] == today_d) | (df_pm['_due'] == tomorrow_d)) & (df_pm['status'] != 'Completed')]
        if len(overdue) > 0 or len(upcoming) > 0:
            pm_today_txt = f"\n🔧 *PM:* เลยกำหนด {len(overdue)} | ใกล้ครบ {len(upcoming)}"

    urgent_txt = f"\n🚨 *งานด่วนมากค้าง:* {urgent}" if urgent > 0 else ""

    msg = (
        f"📊 *รายงานสรุปประจำวัน*\n"
        f"📅 {today_str}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔴 *รอตรวจสอบ:* {pending}\n"
        f"🟡 *ดำเนินการ:* {inprog}\n"
        f"🟣 *ส่งซ่อม:* {sending}\n"
        f"🟢 *สำเร็จ:* {done}"
        f"{urgent_txt}"
        f"{pm_today_txt}"
    )
    return send_telegram(msg, silent=True)

def send_weekly_summary():
    """รายงานสรุปประจำสัปดาห์"""
    df = load_table("tickets")
    today_d = datetime.now().date()
    week_ago = today_d + relativedelta(days=-7)

    if df.empty:
        return send_telegram("📈 *รายงานประจำสัปดาห์*\nยังไม่มีข้อมูล")

    df['_date'] = pd.to_datetime(df['date']).dt.date
    df_week = df[df['_date'] >= week_ago]

    total_week = len(df_week)
    done_week  = len(df_week[df_week['status'] == 'สำเร็จ'])
    success_rate = (done_week/total_week*100) if total_week > 0 else 0

    avg_csat = df_week['rating'].mean() if 'rating' in df_week.columns else None
    csat_txt = f"\n⭐ *คะแนนเฉลี่ย:* {avg_csat:.2f}/5.0" if pd.notna(avg_csat) else ""

    total_cost = pd.to_numeric(df_week['cost'], errors='coerce').sum()

    # Top แผนก
    top_dept = df_week['dept'].value_counts().head(3) if not df_week.empty else None
    dept_txt = ""
    if top_dept is not None and len(top_dept) > 0:
        dept_txt = "\n\n🏢 *Top แผนกที่แจ้งซ่อม:*\n" + "\n".join(
            [f"  • {_tg_escape(d)}: {n} งาน" for d, n in top_dept.items()]
        )

    msg = (
        f"📈 *รายงานสรุปประจำสัปดาห์*\n"
        f"📅 {week_ago.strftime('%d %b')} → {today_d.strftime('%d %b %Y')}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *งานทั้งหมด:* {total_week}\n"
        f"✅ *ปิดงานสำเร็จ:* {done_week} ({success_rate:.1f}%)\n"
        f"💰 *ค่าซ่อมรวม:* {total_cost:,.2f} บาท"
        f"{csat_txt}"
        f"{dept_txt}"
    )
    return send_telegram(msg, silent=True)

def _setup_thai_font(pdf):
    for family, filename in [("ThaiSarabun","THSarabunNew.ttf"),("ThaiPrompt","Prompt-Regular.ttf")]:
        if os.path.exists(filename):
            try:
                pdf.add_font(family, "", filename)
                return family
            except: continue
    return None

def generate_repair_pdf(tk, img_base64=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(10); pdf.set_right_margin(10)
    thai_family = _setup_thai_font(pdf)
    if thai_family:
        pdf.set_font(thai_family, size=16)
    else:
        pdf.set_font("Helvetica", size=16)
        pdf.set_text_color(200,0,0)
        pdf.cell(190,8,txt="[WARNING: Thai font not found]",ln=True)
        pdf.set_text_color(0,0,0)
    pdf.cell(190,10,txt="IT SERVICE REPORT (ใบงานซ่อมคอมพิวเตอร์)",align='C',ln=True)
    pdf.set_font(pdf.font_family,size=12); pdf.ln(5)
    pdf.cell(95,10,txt=f"หมายเลขงาน: {tk.get('id','')}"); pdf.cell(95,10,txt=f"วันที่แจ้ง: {tk.get('date','')}",ln=True)
    pdf.cell(95,10,txt=f"ผู้แจ้ง: {tk.get('user','')}"); pdf.cell(95,10,txt=f"แผนก: {tk.get('dept','')}",ln=True)
    pdf.cell(190,10,txt=f"สถานที่ตั้ง: {tk.get('location','ไม่ได้ระบุ')}",ln=True); pdf.ln(2)
    pdf.set_fill_color(240,240,240)
    pdf.cell(190,10,txt=" รายละเอียดอุปกรณ์และปัญหา",ln=True,fill=True)
    pdf.cell(95,10,txt=f"ประเภทอุปกรณ์: {tk.get('equipment_type','ไม่ได้ระบุ')}")
    pdf.cell(95,10,txt=f"รหัสทรัพย์สิน: {tk.get('asset_id','ไม่ได้ระบุ')}",ln=True)
    pdf.set_x(10); pdf.multi_cell(190,10,txt=f"อาการที่แจ้ง: {tk.get('desc','')}"); pdf.ln(2)
    pdf.cell(190,10,txt=" รายละเอียดการแก้ไข (Technician Report)",ln=True,fill=True)
    pdf.cell(95,10,txt=f"ช่างผู้รับผิดชอบ: {tk.get('assignee','ไม่ได้ระบุ')}")
    pdf.cell(95,10,txt=f"สถานะ: {tk.get('status','')}",ln=True)
    pdf.set_x(10); pdf.multi_cell(190,10,txt=f"สาเหตุ: {tk.get('root_cause','') or 'ไม่ได้ระบุ'}")
    pdf.set_x(10); pdf.multi_cell(190,10,txt=f"วิธีแก้ไข: {tk.get('solution','') or 'ไม่ได้ระบุ'}")
    cost_val = tk.get('cost',0)
    try: cost_val = float(cost_val)
    except: cost_val = 0.0
    pdf.set_x(10); pdf.cell(190,10,txt=f"ค่าใช้จ่าย: {cost_val:,.2f} บาท",ln=True)
    if img_base64 and str(img_base64).startswith('data:image'):
        pdf.ln(5); pdf.cell(190,10,txt=" รูปภาพประกอบการแจ้งซ่อม",ln=True,fill=True); pdf.ln(5)
        try:
            b64_data = img_base64.split(',')[1]; img_bytes = base64.b64decode(b64_data)
            with tempfile.NamedTemporaryFile(delete=False,suffix=".png") as tmp:
                tmp.write(img_bytes); tmp_path = tmp.name
            if pdf.get_y() > 200: pdf.add_page()
            pdf.image(tmp_path,w=90); pdf.ln(5); os.remove(tmp_path)
        except: pdf.cell(190,10,txt="[ไม่สามารถโหลดรูปภาพลง PDF ได้]",ln=True)
    pdf.ln(15)
    pdf.cell(63,10,txt="................................",align='C')
    pdf.cell(63,10,txt="................................",align='C')
    pdf.cell(63,10,txt="................................",align='C',ln=True)
    pdf.cell(63,10,txt="(ลงชื่อผู้แจ้ง/รับงาน)",align='C')
    pdf.cell(63,10,txt="(ลงชื่อช่างผู้ซ่อม)",align='C')
    pdf.cell(63,10,txt="(ผู้อนุมัติ / MGR)",align='C',ln=True)
    return bytes(pdf.output())

# --- CONFIG ---
rating_scale = {"พอใจมากที่สุด":5,"พอใจ":4,"ปานกลาง":3,"ไม่พอใจ":2,"ไม่พอใจอย่างมาก":1}
scale_options = list(rating_scale.keys())
depts = ["CHASSIS","PANEL","LOGISTICS","QC","CCR","FINANCE","HR","PROCUREMENT",
         "PACKAGING DESIGN","PRODUCTION PLANNING & PROJECT CONTROL",
         "SERVICE PARTS DIVISION","IMPORT-EXPORT OPERATION","MOTOR POOL OPERATION","Other"]
ticket_statuses = ["รอตรวจสอบ","ดำเนินการ","ส่งซ่อม","สำเร็จ"]

# --- LOGIN ---
ADMIN_PASSWORD = "itpassword123"
if "is_admin" not in st.session_state: st.session_state.is_admin = False

if not st.session_state.is_admin:
    # ── แสดงสถานะ + ปุ่ม Login ใน sidebar ──
    st.sidebar.markdown('<div class="login-box"><p class="login-box-title">🔐 Admin Login</p></div>', unsafe_allow_html=True)
    admin_pass_sb = st.sidebar.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter admin password", key="pwd_sb")
    if st.sidebar.button("เข้าสู่ระบบ", use_container_width=True, key="login_sb"):
        if admin_pass_sb == ADMIN_PASSWORD:
            st.session_state.is_admin = True; st.rerun()
        else: st.sidebar.error("รหัสผ่านไม่ถูกต้อง")
else:
    st.sidebar.markdown("""<div class="admin-badge"><div class="admin-dot"></div><p class="admin-badge-text">IT Admin Mode</p></div>""", unsafe_allow_html=True)
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.is_admin = False; st.rerun()

st.sidebar.markdown("<hr style='border-color:rgba(30,111,217,0.25);margin:14px 0;'>", unsafe_allow_html=True)
st.sidebar.markdown('<p class="nav-section-label">Navigation</p>', unsafe_allow_html=True)

# ── Master menu list ──
ALL_MENU = [
    ("📝", "แจ้งซ่อม / ติดตามงาน",  "📝 แจ้งซ่อม (User)",         True),    # (icon, label, page_key, public)
    ("💻", "จัดการงานซ่อม",          "💻 จัดการงานซ่อม (ช่าง)",   False),
    ("📊", "Dashboard & รายงาน",      "📊 Dashboard",               False),
    ("🗄️", "ทะเบียนอุปกรณ์",          "🗄️ ทะเบียนอุปกรณ์",         False),
    ("🔧", "แผนบำรุงรักษา (PM)",     "🔧 แผนบำรุงรักษา (PM)",     False),
    ("🔔", "การแจ้งเตือน",            "🔔 Notifications",           False),
]
visible_menu = [m for m in ALL_MENU if m[3] or st.session_state.is_admin]

if "active_page" not in st.session_state:
    st.session_state.active_page = visible_menu[0][2]

# ถ้า logout แล้ว active_page เป็นหน้า admin → กลับไปหน้า user
allowed_keys = [m[2] for m in visible_menu]
if st.session_state.active_page not in allowed_keys:
    st.session_state.active_page = visible_menu[0][2]

# ── Sidebar navigation ──
sb_options = [f"{m[0]}  {m[1]}" for m in visible_menu]
sb_keys    = [m[2] for m in visible_menu]
sb_key_by_label = dict(zip(sb_options, sb_keys))

def _on_sb_nav_change():
    """ถูกเรียกเฉพาะตอนผู้ใช้คลิก sidebar radio จริง ๆ"""
    chosen = st.session_state.sb_nav
    st.session_state.active_page = sb_key_by_label.get(chosen, st.session_state.active_page)

try:
    sb_default_idx = sb_keys.index(st.session_state.active_page)
except ValueError:
    sb_default_idx = 0

# sync sidebar radio ให้ตรงกับ active_page ก่อน render (กรณี top nav เพิ่งเปลี่ยน)
st.session_state.sb_nav = sb_options[sb_default_idx]

st.sidebar.radio(
    "ไปที่หน้า",
    sb_options,
    index=sb_default_idx,
    label_visibility="collapsed",
    key="sb_nav",
    on_change=_on_sb_nav_change,
)

page = st.session_state.active_page

# ── Global Login Bar (อยู่บนสุด) ──
login_col1, login_col2 = st.columns([3, 1])
with login_col2:
    if not st.session_state.is_admin:
        with st.popover("🔐 IT Admin Login", use_container_width=True):
            st.markdown("**เข้าสู่ระบบสำหรับผู้ดูแล**")
            pwd_main = st.text_input("รหัสผ่าน", type="password", key="pwd_main", placeholder="Enter password", label_visibility="collapsed")
            if st.button("เข้าสู่ระบบ", use_container_width=True, key="login_main"):
                if pwd_main == ADMIN_PASSWORD:
                    st.session_state.is_admin = True; st.rerun()
                else:
                    st.error("รหัสผ่านไม่ถูกต้อง")
    else:
        st.markdown("""
        <div style="text-align:right;padding-top:6px;">
          <span class="status-badge status-สำเร็จ">✓ IT Admin Mode</span>
        </div>
        """, unsafe_allow_html=True)

# ── Top Navigation Bar ──
nav_cols = st.columns(len(visible_menu))
for i, (icon, label, key, _) in enumerate(visible_menu):
    is_active = (st.session_state.active_page == key)
    with nav_cols[i]:
        wrapper_class = "top-nav-row top-nav-active" if is_active else "top-nav-row"
        st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
        if st.button(f"{icon}  {label}", key=f"topnav_{key}", use_container_width=True):
            st.session_state.active_page = key
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:18px;'></div>", unsafe_allow_html=True)

# ==========================================
# หน้า 1: แจ้งซ่อม
# ==========================================
if page == "📝 แจ้งซ่อม (User)":
    st.header("ระบบแจ้งซ่อมและติดตามงานออนไลน์")
    tab_status, tab1 = st.tabs(["📋 ตรวจสอบสถานะงานซ่อม", "🆕 ส่งใบแจ้งซ่อม"])

    with tab_status:
        df_tickets = load_table("tickets")
        if not df_tickets.empty:
            sort_map = {'รอตรวจสอบ':1,'ดำเนินการ':2,'ส่งซ่อม':3,'สำเร็จ':4}
            df_tickets['_sort'] = df_tickets['status'].map(sort_map)
            df_sorted = df_tickets.sort_values(by=['_sort','date'], ascending=[True,False])

            # แสดงสูงสุด 15 รายการ — เรียงตามสถานะ (งานที่ยังไม่เสร็จมาก่อน)
            TICKETS_LIMIT = 15
            total_count = len(df_sorted)
            df_show = df_sorted.head(TICKETS_LIMIT)
            unfinished = len(df_sorted[df_sorted['status'] != 'สำเร็จ'])

            st.markdown(f"""
            <p style='color:#8BA0BC;margin-bottom:14px;font-size:13px;'>
              แสดง <b style='color:#E8EDF5;'>{len(df_show)}</b> จาก <b style='color:#E8EDF5;'>{total_count}</b> รายการล่าสุด
              &nbsp;•&nbsp; งานที่ยังไม่เสร็จ <b style='color:#FCD34D;'>{unfinished}</b> รายการ
            </p>
            """, unsafe_allow_html=True)

            @st.dialog("📋 รายละเอียดงานซ่อม", width="large")
            def show_ticket_detail(row):
                status_cls = f"status-{row['status']}"
                rating_val = row.get('rating')
                stars = "⭐" * int(round(float(rating_val))) if pd.notna(rating_val) else "รอประเมิน"
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                  <div>
                    <span style="font-family:'DM Mono',monospace;font-size:13px;color:#00C6FF;">{row['id']}</span>
                    <span style="margin-left:12px;" class="status-badge {status_cls}">{row['status']}</span>
                  </div>
                  <div style="font-size:12px;color:#4A6080;">{row.get('date','')}</div>
                </div>
                """, unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**👤 ผู้แจ้ง:** {row.get('user','—')}")
                    st.markdown(f"**🏢 แผนก:** {row.get('dept','—')}")
                    st.markdown(f"**📍 สถานที่ตั้ง:** {row.get('location','—')}")
                    st.markdown(f"**⚡ ความเร่งด่วน:** {row.get('urgency','—')}")
                with c2:
                    st.markdown(f"**🖥️ ประเภทอุปกรณ์:** {row.get('equipment_type','—')}")
                    st.markdown(f"**🔖 รหัสทรัพย์สิน:** `{row.get('asset_id','—')}`")
                    st.markdown(f"**📂 ประเภทงาน:** {row.get('category','—')}")
                    st.markdown(f"**🔧 ช่างผู้รับผิดชอบ:** {row.get('assignee','—')}")
                st.divider()
                st.markdown("**📝 อาการที่แจ้ง**")
                st.info(row.get('desc','—'))
                if pd.notna(row.get('root_cause')) and row.get('root_cause'):
                    st.markdown("**🔍 สาเหตุ**"); st.info(row.get('root_cause'))
                if pd.notna(row.get('solution')) and row.get('solution'):
                    st.markdown("**✅ วิธีแก้ไข**"); st.success(row.get('solution'))
                cost_val = row.get('cost',0)
                try: cost_val = float(cost_val)
                except: cost_val = 0.0
                if cost_val > 0:
                    st.markdown(f"**💰 ค่าใช้จ่าย:** `฿{cost_val:,.2f}`")
                if pd.notna(rating_val):
                    st.markdown(f"**⭐ คะแนนประเมิน:** {stars} `({float(rating_val):.1f}/5.0)`")
                if pd.notna(row.get('feedback')) and row.get('feedback'):
                    st.markdown("**💬 ข้อเสนอแนะ**")
                    st.markdown(f"<p style='color:#8BA0BC;font-style:italic;'>\"{row.get('feedback')}\"</p>", unsafe_allow_html=True)

                # ── ฟอร์มประเมินความพึงพอใจ (เฉพาะงานสำเร็จที่ยังไม่ประเมิน) ──
                is_done_ticket = row['status'] == 'สำเร็จ'
                not_rated = pd.isna(row.get('q1'))
                if is_done_ticket and not_rated:
                    st.divider()
                    st.markdown("### ⭐ ประเมินความพึงพอใจ")
                    st.markdown("<p style='color:#8BA0BC;font-size:12px;margin-bottom:12px;'>งานนี้ดำเนินการเสร็จสิ้นแล้ว กรุณาประเมินการให้บริการเพื่อช่วยเราพัฒนา</p>", unsafe_allow_html=True)
                    with st.form(f"csat_dialog_{row['id']}"):
                        q1 = st.radio("1. ความพอใจการสนับสนุนจากทีมงาน?", scale_options, horizontal=True, key=f"q1_{row['id']}")
                        q2 = st.radio("2. คุณภาพการบริการ HW/SW?",        scale_options, horizontal=True, key=f"q2_{row['id']}")
                        q3 = st.radio("3. ความมืออาชีพของทีมงาน?",         scale_options, horizontal=True, key=f"q3_{row['id']}")
                        q4 = st.radio("4. การบริการที่ตรงต่อเวลา?",         scale_options, horizontal=True, key=f"q4_{row['id']}")
                        q5 = st.radio("5. ความพึงพอใจในภาพรวม?",          scale_options, horizontal=True, key=f"q5_{row['id']}")
                        fb = st.text_area("ข้อเสนอแนะเพิ่มเติม", key=f"fb_{row['id']}")
                        if st.form_submit_button("✅ บันทึกการประเมิน", use_container_width=True):
                            update_csat_full(row['id'],
                                rating_scale[q1], rating_scale[q2], rating_scale[q3],
                                rating_scale[q4], rating_scale[q5], fb)
                            st.toast("ขอบคุณสำหรับการประเมิน!", icon="⭐")
                            st.rerun()

                # ── ปุ่ม แก้ไข / ยกเลิก (เฉพาะงานสถานะ "รอตรวจสอบ") ──
                if row['status'] == 'รอตรวจสอบ':
                    st.divider()
                    st.markdown("<p style='color:#8BA0BC;font-size:12px;margin-bottom:8px;'>💡 ขณะนี้ช่างยังไม่ได้รับงาน คุณสามารถแก้ไขหรือยกเลิกใบแจ้งซ่อมนี้ได้</p>", unsafe_allow_html=True)
                    ub1, ub2 = st.columns(2)
                    with ub1:
                        if st.button("✏️ แก้ไขข้อมูล", use_container_width=True, key=f"user_edit_{row['id']}"):
                            st.session_state["pending_user_action"] = ("edit", row['id'])
                            st.rerun()
                    with ub2:
                        if st.button("🗑️ ยกเลิกใบแจ้งซ่อม", use_container_width=True, key=f"user_cancel_{row['id']}"):
                            st.session_state["pending_user_action"] = ("cancel", row['id'])
                            st.rerun()
                elif row['status'] in ['ดำเนินการ', 'ส่งซ่อม']:
                    st.divider()
                    st.markdown("<p style='color:#FCD34D;font-size:12px;'>ℹ️ ช่างกำลังดำเนินการแล้ว ไม่สามารถแก้ไขหรือยกเลิกได้</p>", unsafe_allow_html=True)

            # ── Dialog แก้ไข ticket (สำหรับ user) ──
            @st.dialog("✏️ แก้ไขใบแจ้งซ่อม", width="large")
            def edit_ticket_user_dialog(tk):
                tid = tk['id']
                st.markdown(f"<p style='color:#8BA0BC;font-size:12px;'>กำลังแก้ไข <b style='color:#00C6FF;font-family:DM Mono,monospace;'>{tid}</b></p>", unsafe_allow_html=True)
                with st.form(f"user_edit_form_{tid}"):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        e_user = st.text_input("ชื่อผู้แจ้ง", value=tk.get('user') or "")
                        # dept dropdown
                        cur_dept = tk.get('dept') or depts[0]
                        try: dept_idx = depts.index(cur_dept) if cur_dept in depts else len(depts) - 1
                        except: dept_idx = 0
                        e_dept_choice = st.selectbox("แผนก", depts, index=dept_idx)
                        e_dept_custom = st.text_input("ระบุแผนก (ถ้าเลือก Other)", value=cur_dept if cur_dept not in depts else "")
                        cat_opts = ["Hardware","Software","Network","Other"]
                        e_cat = st.selectbox("ประเภทงานซ่อม", cat_opts,
                                             index=cat_opts.index(tk.get('category')) if tk.get('category') in cat_opts else 0)
                        eq_opts = ["Computer PC","Notebook","TEC Printer","Laser Printer","IPDS Printer","TV","CCTV","IPad","Other"]
                        e_eq = st.selectbox("ประเภทอุปกรณ์", eq_opts,
                                            index=eq_opts.index(tk.get('equipment_type')) if tk.get('equipment_type') in eq_opts else 0)
                    with ec2:
                        e_asset = st.text_input("รหัสอุปกรณ์ (Asset ID)", value=tk.get('asset_id') or "")
                        e_loc = st.text_input("สถานที่ตั้งอุปกรณ์", value=tk.get('location') or "")
                        urg_opts = ["ปกติ","ด่วน","ด่วนมาก"]
                        e_urgency = st.selectbox("ระดับความเร่งด่วน", urg_opts,
                                                 index=urg_opts.index(tk.get('urgency')) if tk.get('urgency') in urg_opts else 0)
                    e_desc = st.text_area("รายละเอียดปัญหา", value=tk.get('desc') or "", height=120)

                    if st.form_submit_button("💾 บันทึกการแก้ไข", use_container_width=True):
                        final_dept = e_dept_custom.strip() if e_dept_choice == "Other" else e_dept_choice
                        if not e_user.strip() or not e_desc.strip() or not final_dept:
                            st.error("❌ กรุณากรอกชื่อผู้แจ้ง แผนก และรายละเอียดปัญหา")
                        else:
                            update_ticket_user_fields(tid, {
                                "user": e_user.strip(),
                                "dept": final_dept,
                                "category": e_cat,
                                "equipment_type": e_eq,
                                "asset_id": e_asset.strip(),
                                "location": e_loc.strip(),
                                "urgency": e_urgency,
                                "desc": e_desc.strip()
                            })
                            st.toast(f"แก้ไข {tid} สำเร็จ!", icon="✅")
                            st.rerun()

            # ── Dialog ยืนยันยกเลิก ticket ──
            @st.dialog("⚠️ ยืนยันการยกเลิกใบแจ้งซ่อม", width="small")
            def cancel_ticket_dialog(tk):
                tid = tk['id']
                st.markdown(f"""
                <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.4);border-radius:10px;padding:14px;margin-bottom:14px;">
                    <p style="color:#FCA5A5;margin:0;font-weight:600;">⚠️ คุณกำลังจะยกเลิกใบแจ้งซ่อมนี้</p>
                    <p style="color:#8BA0BC;margin:6px 0 0 0;font-size:12px;">การกระทำนี้ไม่สามารถย้อนกลับได้</p>
                </div>
                <p><b style="color:#E8EDF5;">รหัส:</b> <span style="color:#00C6FF;font-family:DM Mono,monospace;">{tid}</span></p>
                <p><b style="color:#E8EDF5;">ผู้แจ้ง:</b> <span style="color:#8BA0BC;">{tk.get('user','—')}</span></p>
                <p><b style="color:#E8EDF5;">อาการ:</b> <span style="color:#8BA0BC;">{tk.get('desc','—')}</span></p>
                """, unsafe_allow_html=True)
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("❌ ไม่ยกเลิก", use_container_width=True, key=f"keep_{tid}"):
                        st.rerun()
                with dc2:
                    if st.button("🗑️ ยืนยันยกเลิก", use_container_width=True, key=f"confirm_cancel_{tid}", type="primary"):
                        delete_ticket(tid)
                        st.toast(f"ยกเลิก {tid} แล้ว", icon="🗑️")
                        st.rerun()

            # ── ตรวจสอบ pending action (เกิดจากผู้ใช้กดปุ่มในรอบก่อน) ──
            _pa = st.session_state.pop("pending_user_action", None)
            if _pa:
                _act, _tid = _pa
                _match = df_show[df_show['id'] == _tid]
                if not _match.empty:
                    _row = _match.iloc[0]
                    if _act == "edit" and _row['status'] == 'รอตรวจสอบ':
                        edit_ticket_user_dialog(_row)
                    elif _act == "cancel" and _row['status'] == 'รอตรวจสอบ':
                        cancel_ticket_dialog(_row)

            for _, row in df_show.iterrows():
                status_cls  = f"status-{row['status']}"
                urgency_cls = f"ticket-urgency-{row.get('urgency','ปกติ')}"
                rating_val  = row.get('rating')
                rating_html = "⭐" * int(round(float(rating_val))) if pd.notna(rating_val) else '<span style="color:#4A6080;font-size:11px;">รอประเมิน</span>'
                col_card, col_btn = st.columns([11, 1])
                with col_card:
                    st.markdown(f"""
                    <div class="ticket-card">
                        <div class="ticket-card-left">
                            <div class="ticket-id">{row['id']}</div>
                            <div class="ticket-user">{row.get('user','')}</div>
                            <div class="ticket-date">{row.get('date','')}</div>
                        </div>
                        <div class="ticket-card-mid">
                            <div class="ticket-cat">📂 {row.get('category','')} &nbsp;|&nbsp; 🖥️ {row.get('equipment_type','')}</div>
                            <div class="ticket-cat" style="margin-top:4px;">🏢 {row.get('dept','')}</div>
                            <div class="{urgency_cls}" style="margin-top:4px;">⚡ {row.get('urgency','')}</div>
                        </div>
                        <div class="ticket-card-right">
                            <div><span class="status-badge {status_cls}">{row['status']}</span></div>
                            <div class="ticket-rating" style="margin-top:8px;">{rating_html}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
                    if st.button("🔍", key=f"view_{row['id']}", help="ดูรายละเอียด", use_container_width=True):
                        show_ticket_detail(row)
        else:
            st.info("ยังไม่มีข้อมูลงานซ่อม")

    with tab1:
        with st.form("ticket_form"):
            c1, c2 = st.columns(2)
            with c1:
                user_name = st.text_input("ชื่อผู้แจ้ง")
                dept_choice = st.selectbox("แผนก", depts)
                department = st.text_input("กรุณาระบุแผนกของคุณ") if dept_choice == "Other" else dept_choice
                category = st.selectbox("ประเภทงานซ่อม (Category)", ["Hardware","Software","Network","Other"])
                eq_type = st.selectbox("ประเภทอุปกรณ์ (Equipment Type)", ["Computer PC","Notebook","TEC Printer","Laser Printer","IPDS Printer","TV","CCTV","IPad","Other"])
            with c2:
                asset_id_input = st.text_input("รหัสอุปกรณ์ (Asset ID)")
                loc_input = st.text_input("สถานที่ตั้งอุปกรณ์ (เช่น KD2 / เสา 4B)")
                urgency = st.selectbox("ระดับความเร่งด่วน", ["ปกติ","ด่วน","ด่วนมาก"])
                uploaded_file = st.file_uploader("แนบรูปภาพประกอบ", type=['png','jpg','jpeg'])
            description = st.text_area("รายละเอียดปัญหา")
            submitted = st.form_submit_button("ส่งเรื่องแจ้งซ่อม")
            if submitted:
                ticket_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
                image_data = ""
                if uploaded_file:
                    encoded_img = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                    image_data = f"data:{uploaded_file.type};base64,{encoded_img}"
                if dept_choice == "Other" and not department.strip():
                    st.error("❌ กรุณาระบุชื่อแผนกของคุณ")
                elif user_name and description and department.strip():
                    new_ticket = {
                        "id": ticket_id, "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "user": user_name, "dept": department.strip(), "category": category,
                        "equipment_type": eq_type, "desc": description, "status": "รอตรวจสอบ",
                        "urgency": urgency, "image_path": image_data,
                        "asset_id": asset_id_input, "location": loc_input
                    }
                    insert_data("tickets", new_ticket)
                    # ── ส่ง Telegram แจ้งทีม IT ──
                    try: notify_new_ticket(new_ticket)
                    except Exception: pass
                    st.toast('ส่งเรื่องแจ้งซ่อมเรียบร้อยแล้ว!', icon='✅')
                    st.success(f"🎉 บันทึกข้อมูลสำเร็จ! หมายเลขอ้างอิง: **{ticket_id}**")
                else:
                    st.error("❌ กรุณาระบุชื่อผู้แจ้ง, แผนก และรายละเอียดปัญหา")

# ==========================================
# หน้า 2: จัดการงานซ่อม
# ==========================================
elif page == "💻 จัดการงานซ่อม (ช่าง)" and st.session_state.is_admin:
    st.header("💻 จัดการงานซ่อม")
    df_tickets = load_table("tickets")
    if not df_tickets.empty:
        # ── Mini Dashboard ──
        total   = len(df_tickets)
        done    = len(df_tickets[df_tickets['status'] == 'สำเร็จ'])
        pending = len(df_tickets[df_tickets['status'] == 'รอตรวจสอบ'])
        wip     = len(df_tickets[df_tickets['status'].isin(['ดำเนินการ','ส่งซ่อม'])])
        done_rate = (done/total*100) if total > 0 else 0
        md1, md2, md3, md4 = st.columns(4)
        with md1: st.metric("📋 งานแจ้งซ่อมทั้งหมด", total)
        with md2: st.metric("✅ ปิดงานสำเร็จ", f"{done} งาน", f"{done_rate:.1f}%")
        with md3: st.metric("⏳ กำลังดำเนินการ", f"{wip} งาน")
        with md4: st.metric("🔴 งานค้าง (รอตรวจสอบ)", pending, delta=f"{pending} งาน" if pending else "ไม่มี", delta_color="inverse")
        st.divider()
        df_pending = df_tickets[df_tickets['status'] != 'สำเร็จ'].copy()
        if not df_pending.empty:
            sort_map = {'รอตรวจสอบ':1,'ดำเนินการ':2,'ส่งซ่อม':3}
            df_pending['_sort'] = df_pending['status'].map(sort_map).fillna(9)
            df_pending = df_pending.sort_values(by=['_sort','date'], ascending=[True,False])

            st.markdown(f"<p style='color:#8BA0BC;margin-bottom:16px;'>งานรอดำเนินการทั้งหมด <b style='color:#E8EDF5;'>{len(df_pending)}</b> รายการ — คลิกที่การ์ดเพื่อแก้ไข</p>", unsafe_allow_html=True)

            # ── Dialog: แก้ไขได้ + PDF ──
            @st.dialog("🔧 จัดการงานซ่อม", width="large")
            def edit_ticket_dialog(tk):
                tid = tk['id']

                # ดึงรูปครั้งเดียว
                try:
                    img_res = supabase.table("tickets").select("image_path").eq("id", tid).execute()
                    img_path = img_res.data[0].get('image_path','') if img_res.data else ''
                except:
                    img_path = ''

                # Header
                status_cls = f"status-{tk['status']}"
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                  <div>
                    <span style="font-family:'DM Mono',monospace;font-size:14px;color:#00C6FF;">{tid}</span>
                    <span style="margin-left:12px;" class="status-badge {status_cls}">{tk['status']}</span>
                  </div>
                  <div style="font-size:12px;color:#4A6080;">{tk.get('date','')}</div>
                </div>
                """, unsafe_allow_html=True)

                # ข้อมูลอ่านอย่างเดียว
                ci1, ci2 = st.columns(2)
                with ci1:
                    st.markdown(f"**👤 ผู้แจ้ง:** {tk.get('user','—')}")
                    st.markdown(f"**🏢 แผนก:** {tk.get('dept','—')}")
                    st.markdown(f"**📍 สถานที่:** {tk.get('location','—')}")
                    st.markdown(f"**🖥️ อุปกรณ์:** {tk.get('equipment_type','—')}  `{tk.get('asset_id','')}`")
                with ci2:
                    st.markdown(f"**📂 ประเภท:** {tk.get('category','—')}")
                    st.markdown(f"**⚡ ความเร่งด่วน:** {tk.get('urgency','—')}")

                st.markdown("**📝 อาการที่แจ้ง**")
                st.info(tk.get('desc','—'))

                if img_path and str(img_path).startswith('data:image'):
                    try: st.image(img_path, caption="รูปประกอบ", width=360)
                    except: pass

                st.divider()
                st.markdown("**✏️ บันทึกการซ่อม**")

                # ── Form แก้ไข ──
                with st.form(f"edit_form_{tid}"):
                    fa, fb = st.columns(2)
                    with fa:
                        n_status  = st.selectbox("สถานะ", ticket_statuses, index=ticket_statuses.index(tk['status']))
                        assignee  = st.text_input("ช่างผู้รับผิดชอบ", value=tk.get('assignee') or "")
                        cost      = st.number_input("ค่าใช้จ่าย (บาท)", value=float(tk.get('cost') or 0.0), min_value=0.0)
                    with fb:
                        root = st.text_area("สาเหตุของปัญหา", value=tk.get('root_cause') or "", height=100)
                        sol  = st.text_area("วิธีการแก้ไข",   value=tk.get('solution')   or "", height=100)

                    sc1, sc2 = st.columns(2)
                    with sc1:
                        save_btn = st.form_submit_button("💾 บันทึก", use_container_width=True)
                    with sc2:
                        # PDF ต้องอยู่นอก form จึงสร้างก่อน
                        pass

                    if save_btn:
                        update_ticket_full(tid, n_status, assignee, root, sol, cost)
                        # ── ส่ง Telegram แจ้งเตือนเมื่อปิดงานสำเร็จ ──
                        if n_status == "สำเร็จ" and tk.get('status') != "สำเร็จ":
                            try:
                                notify_ticket_closed(dict(tk), assignee=assignee, cost=float(cost or 0.0))
                            except Exception: pass
                        st.toast(f"บันทึกงาน {tid} สำเร็จ!", icon="✅")
                        st.rerun()

                # ปุ่ม PDF อยู่นอก form
                pdf_tk = tk.copy()
                pdf_bytes = generate_repair_pdf(pdf_tk, img_path)
                st.download_button(
                    label="📥 ดาวน์โหลดใบงานซ่อม (PDF)",
                    data=pdf_bytes,
                    file_name=f"Service_Report_{tid}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"pdf_{tid}"
                )

            # ── Render Cards ──
            for _, row in df_pending.iterrows():
                status_cls  = f"status-{row['status']}"
                urgency_cls = f"ticket-urgency-{row.get('urgency','ปกติ')}"
                col_card, col_btn = st.columns([11, 1])
                with col_card:
                    st.markdown(f"""
                    <div class="ticket-card">
                        <div class="ticket-card-left">
                            <div class="ticket-id">{row['id']}</div>
                            <div class="ticket-user">{row.get('user','')}</div>
                            <div class="ticket-date">{row.get('date','')}</div>
                        </div>
                        <div class="ticket-card-mid">
                            <div class="ticket-cat">📂 {row.get('category','')} &nbsp;|&nbsp; 🖥️ {row.get('equipment_type','')}</div>
                            <div class="ticket-cat" style="margin-top:4px;">🏢 {row.get('dept','')} &nbsp;|&nbsp; 📍 {row.get('location','—')}</div>
                            <div class="{urgency_cls}" style="margin-top:4px;">⚡ {row.get('urgency','')}</div>
                        </div>
                        <div class="ticket-card-right">
                            <div><span class="status-badge {status_cls}">{row['status']}</span></div>
                            <div style="font-size:11px;color:#4A6080;margin-top:6px;">{row.get('assignee','ยังไม่มอบหมาย')}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
                    if st.button("✏️", key=f"edit_{row['id']}", help="แก้ไขงาน", use_container_width=True):
                        edit_ticket_dialog(row)

        else:
            st.success("🎉 ยอดเยี่ยม! ขณะนี้ไม่มีงานซ่อมค้างในระบบ")
    else:
        st.info("ยังไม่มีข้อมูลงานซ่อมในระบบ")

# ==========================================
# หน้า 3: Dashboard
# ==========================================
elif page == "📊 Dashboard" and st.session_state.is_admin:
    st.title("📈 IT Performance Overview")
    df = load_table("tickets")

    if not df.empty:
        df['date_dt'] = pd.to_datetime(df['date'])
        df['month_year'] = df['date_dt'].dt.strftime('%m-%Y')

        # ── เลือกเดือน: default = เดือนปัจจุบัน, เพิ่ม "ทั้งหมด" ท้ายสุด ──
        sorted_months = sorted(df['month_year'].unique(), reverse=True)
        current_month = datetime.now().strftime('%m-%Y')
        month_options = sorted_months + ["ทั้งหมด"]
        default_idx = month_options.index(current_month) if current_month in month_options else 0
        selected_month = st.selectbox("📅 เลือกเดือนที่ต้องการดู", month_options, index=default_idx)

        if selected_month != "ทั้งหมด":
            df_filtered = df[df['month_year'] == selected_month].copy()
            st.info(f"🔎 แสดงข้อมูลเฉพาะเดือน: **{selected_month}**")
        else:
            df_filtered = df.copy()
            st.info("🔎 แสดงข้อมูลภาพรวมทั้งหมด")

        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("งานแจ้งซ่อม", len(df_filtered))
        with m2:
            resolved = len(df_filtered[df_filtered['status'] == 'สำเร็จ'])
            rate = (resolved/len(df_filtered)*100) if len(df_filtered) > 0 else 0
            st.metric("ปิดงานสำเร็จ", f"{resolved} งาน", f"{rate:.1f}%")
        with m3:
            avg_csat = df_filtered['rating'].mean()
            st.metric("คะแนนเฉลี่ย", f"{avg_csat:.2f} ⭐" if not pd.isna(avg_csat) else "0.00 ⭐")
        with m4:
            pending = len(df_filtered[df_filtered['status'] == 'รอตรวจสอบ'])
            st.metric("งานค้าง", pending, delta=f"{pending} งาน", delta_color="inverse")

        st.markdown("---")

        # ── กราฟ 3 คอลัมน์ด้วย Plotly ──
        import plotly.graph_objects as go

        col1, col2, col3 = st.columns(3)

        def make_bar(labels, values, title, color_start, color_end):
            fig = go.Figure(go.Bar(
                x=values, y=labels, orientation='h',
                marker=dict(
                    color=values,
                    colorscale=[[0, color_start],[1, color_end]],
                    line=dict(width=0)
                ),
                text=values, textposition='outside',
                textfont=dict(color='#8BA0BC', size=11)
            ))
            fig.update_layout(
                title=dict(text=title, font=dict(size=13, color='#8BA0BC'), x=0),
                paper_bgcolor='rgba(17,34,64,0.9)',
                plot_bgcolor='rgba(17,34,64,0.9)',
                font=dict(color='#E8EDF5', family='Noto Sans Thai'),
                margin=dict(l=10, r=30, t=40, b=10),
                height=300,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, color='#8BA0BC'),
                yaxis=dict(showgrid=False, zeroline=False, color='#E8EDF5', autorange='reversed'),
                bargap=0.3,
            )
            return fig

        with col1:
            dept_counts = df_filtered['dept'].value_counts()
            fig1 = make_bar(dept_counts.index.tolist(), dept_counts.values.tolist(),
                            "🏢 แยกตามแผนก", "#1E6FD9", "#00C6FF")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            cat_counts = df_filtered['category'].value_counts()
            fig2 = make_bar(cat_counts.index.tolist(), cat_counts.values.tolist(),
                            "🛠️ ประเภทปัญหา", "#8B5CF6", "#C4B5FD")
            st.plotly_chart(fig2, use_container_width=True)

        with col3:
            eq_counts = df_filtered['equipment_type'].value_counts() if 'equipment_type' in df_filtered.columns else pd.Series()
            if not eq_counts.empty:
                fig3 = make_bar(eq_counts.index.tolist(), eq_counts.values.tolist(),
                                "🖥️ ประเภทอุปกรณ์", "#F59E0B", "#FCD34D")
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลประเภทอุปกรณ์")

        st.divider()

        # ── CSAT ──
        with st.expander("📊 รายละเอียดคะแนนประเมิน (CSAT)", expanded=True):
            qs = [
                ("1. การสนับสนุนจากทีมงาน",   df_filtered['q1'].mean()),
                ("2. คุณภาพการบริการ HW/SW",   df_filtered['q2'].mean()),
                ("3. ความเป็นมืออาชีพ",        df_filtered['q3'].mean()),
                ("4. ความตรงต่อเวลา",           df_filtered['q4'].mean()),
                ("5. ความพึงพอใจในภาพรวม",     df_filtered['q5'].mean()),
            ]
            rows_html = ""
            for label, val in qs:
                pct = (val/5*100) if pd.notna(val) else 0
                bar_w = int(pct * 1.2)  # max 120px
                rows_html += f"""
                <tr>
                  <td style="text-align:left;padding:10px 12px;border-bottom:1px solid rgba(255,255,255,0.07);
                             font-size:13px;color:#E8EDF5;">{label}</td>
                  <td style="padding:10px 12px;border-bottom:1px solid rgba(255,255,255,0.07);text-align:right;">
                    <span style="display:inline-block;background:rgba(255,255,255,0.07);border-radius:99px;
                                 height:6px;width:120px;vertical-align:middle;margin-right:8px;overflow:hidden;">
                      <span style="display:block;height:6px;width:{bar_w}px;border-radius:99px;
                                   background:linear-gradient(90deg,#1E6FD9,#00C6FF);"></span>
                    </span>
                    <span style="font-family:'DM Mono',monospace;font-size:13px;color:#E8EDF5;">
                      {f'{pct:.1f}%' if pd.notna(val) else '0.0%'}
                    </span>
                  </td>
                </tr>"""
            st.markdown(f"""
            <table style="width:100%;border-collapse:collapse;">
              <thead><tr>
                <th style="text-align:left;padding:8px 12px;border-bottom:1px solid rgba(30,111,217,0.25);
                           font-size:11px;color:#4A6080;text-transform:uppercase;letter-spacing:0.08em;">หัวข้อการประเมิน</th>
                <th style="text-align:right;padding:8px 12px;border-bottom:1px solid rgba(30,111,217,0.25);
                           font-size:11px;color:#4A6080;text-transform:uppercase;letter-spacing:0.08em;">คะแนน (%)</th>
              </tr></thead>
              <tbody>{rows_html}</tbody>
            </table>
            """, unsafe_allow_html=True)

        # ── Feedback ──
        st.subheader("💬 ข้อเสนอแนะล่าสุด")
        if 'feedback' in df_filtered.columns:
            fb = df_filtered[(df_filtered['feedback'].notna()) & (df_filtered['feedback'].str.strip() != "")].sort_values('date', ascending=False)
            if not fb.empty:
                for _, r in fb.iterrows():
                    stars = "⭐" * int(round(float(r['rating']))) if pd.notna(r.get('rating')) else ""
                    st.markdown(f"""
                    <div class="feedback-card">
                      <div class="feedback-header">
                        <span class="feedback-user">👤 {r.get('user','')}</span>
                        <span class="feedback-date">{r.get('date','')}</span>
                      </div>
                      <div style="margin-bottom:6px;" class="feedback-stars">{stars}</div>
                      <div class="feedback-text">{r.get('feedback','')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.write("ไม่มีข้อเสนอแนะเพิ่มเติม")

        st.divider()

        # ── PM Coverage ──
        st.subheader("🔧 สรุปผลการบำรุงรักษา (PM Coverage)")
        df_pm_all = load_table("pm_schedules")
        if not df_pm_all.empty:
            df_pm_all['date_dt'] = pd.to_datetime(df_pm_all['next_due_date'])
            df_pm_all['month_year'] = df_pm_all['date_dt'].dt.strftime('%m-%Y')
            pm_filtered = df_pm_all[df_pm_all['month_year'] == selected_month] if selected_month != "ทั้งหมด" else df_pm_all

            if not pm_filtered.empty:
                total_pm   = len(pm_filtered)
                done_pm    = len(pm_filtered[pm_filtered['status'] == 'Completed'])
                pending_pm = total_pm - done_pm
                p_done    = (done_pm/total_pm*100)    if total_pm > 0 else 0
                p_pending = (pending_pm/total_pm*100) if total_pm > 0 else 0

                cp1, cp2, cp3 = st.columns(3)
                cp1.metric("แผน PM ทั้งหมด",    f"{total_pm} รายการ")
                cp2.metric("ดำเนินการแล้ว (%)", f"{p_done:.1f}%",    delta=f"{done_pm} งาน")
                cp3.metric("รอดำเนินการ (%)",   f"{p_pending:.1f}%", delta=f"-{pending_pm} งาน", delta_color="inverse")

                # Horizontal bar สวยงาม
                done_w    = int(p_done * 1.6)
                pending_w = int(p_pending * 1.6)
                st.markdown(f"""
                <div style="background:rgba(17,34,64,0.9);border:1px solid rgba(30,111,217,0.25);
                            border-radius:12px;padding:20px 24px;margin-top:16px;">
                  <div class="pm-bar-row">
                    <div class="pm-bar-label">✅ เสร็จสิ้น</div>
                    <div class="pm-bar-track">
                      <div class="pm-bar-fill-green" style="width:{done_w}px;max-width:100%;"></div>
                    </div>
                    <div class="pm-bar-pct" style="color:#10B981;">{p_done:.1f}%</div>
                    <div style="font-size:12px;color:#8BA0BC;width:60px;">{done_pm} งาน</div>
                  </div>
                  <div class="pm-bar-row">
                    <div class="pm-bar-label">🔄 รอดำเนินการ</div>
                    <div class="pm-bar-track">
                      <div class="pm-bar-fill-blue" style="width:{pending_w}px;max-width:100%;"></div>
                    </div>
                    <div class="pm-bar-pct" style="color:#3B8FFF;">{p_pending:.1f}%</div>
                    <div style="font-size:12px;color:#8BA0BC;width:60px;">{pending_pm} งาน</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.write("ไม่มีแผนงาน PM ในเดือนนี้")
        else:
            st.info("ยังไม่มีการสร้างแผนงานบำรุงรักษา (PM) ในระบบ")
    else:
        st.warning("⚠️ ยังไม่มีข้อมูลงานแจ้งซ่อมในฐานข้อมูล")

# ==========================================
# หน้า 4: ทะเบียนอุปกรณ์
# ==========================================
elif page == "🗄️ ทะเบียนอุปกรณ์" and st.session_state.is_admin:
    st.title("🗄️ IT Asset Management")
    with st.expander("➕ ลงทะเบียนอุปกรณ์ใหม่"):
        with st.form("new_asset_form"):
            a1, a2 = st.columns(2)
            with a1:
                aid = st.text_input("รหัสอุปกรณ์ (Asset ID)*")
                awarranty = st.date_input("วันที่หมดประกัน")
                aloc = st.text_input("สถานที่ตั้ง (Location)")
            with a2:
                amod = st.text_input("ยี่ห้อ/รุ่น")
                adept = st.selectbox("แผนกที่ใช้งาน", depts)
                auser = st.text_input("ผู้ถือครอง/ผู้รับผิดชอบ (Assigned User)")
            if st.form_submit_button("บันทึกทะเบียน"):
                if aid:
                    insert_data("assets", {"id":aid,"model":amod,"dept":adept,"warranty_expire":str(awarranty),"location":aloc,"assigned_user":auser,"status":"Active"})
                    st.success(f"ลงทะเบียน {aid} สำเร็จ"); st.rerun()
                else: st.error("กรุณาระบุรหัสอุปกรณ์")

    df_a = load_table("assets"); df_t = load_table("tickets")
    st.divider()

    # ── Export CSV ──
    if not df_a.empty:
        ea1, ea2 = st.columns([8,2])
        with ea1:
            st.markdown(f"<p style='color:#8BA0BC;'>อุปกรณ์ทั้งหมดในระบบ <b style='color:#E8EDF5;'>{len(df_a)}</b> รายการ</p>", unsafe_allow_html=True)
        with ea2:
            csv_data = df_a.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Export CSV",
                data=csv_data,
                file_name=f"IT_Assets_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    search_query = st.text_input("🔍 ตรวจสอบประวัติเครื่องรายอุปกรณ์", placeholder="พิมพ์ Asset ID...")
    if search_query and not df_a.empty:
        match = df_a[df_a['id'].str.contains(search_query, case=False, na=False)]
        if not match.empty:
            target_asset = match.iloc[0]
            today = datetime.now().date()
            w_date_str = target_asset.get('warranty_expire')
            if w_date_str and pd.notna(w_date_str):
                w_date = pd.to_datetime(w_date_str).date()
                if w_date < today:
                    w_status = "🔴 **หมดอายุการรับประกัน**"; border_col = '#d32f2f'
                else:
                    days_left = (w_date - today).days
                    w_status = f"🟢 **อยู่ในประกัน** (เหลือ {days_left} วัน)"; border_col = '#2e7d32'
            else:
                w_status = "⚪ ไม่ระบุข้อมูลประกัน"; w_date = "N/A"; border_col = '#4A6080'
            st.markdown(f"""
            <div style="background:rgba(17,34,64,0.9);padding:20px;border-radius:12px;border-left:5px solid {border_col};border:1px solid rgba(30,111,217,0.25);">
                <h4 style="margin-top:0;color:#E8EDF5;">ข้อมูลอุปกรณ์: {target_asset['id']}</h4>
                <p style="color:#8BA0BC;"><b style="color:#E8EDF5;">รุ่น:</b> {target_asset.get('model','N/A')} &nbsp;|&nbsp; <b style="color:#E8EDF5;">แผนก:</b> {target_asset.get('dept','N/A')}</p>
                <p style="color:#8BA0BC;"><b style="color:#E8EDF5;">สถานที่:</b> {target_asset.get('location','N/A')} &nbsp;|&nbsp; <b style="color:#E8EDF5;">ผู้รับผิดชอบ:</b> {target_asset.get('assigned_user','N/A')}</p>
                <p style="color:#E8EDF5;">สถานะประกัน: {w_status}</p>
                <p style="color:#8BA0BC;">วันที่หมดประกัน: 📅 {w_date}</p>
            </div>
            """, unsafe_allow_html=True)

            # ── ปุ่มแก้ไข / ยกเลิกอุปกรณ์ ──
            ab1, ab2, _ = st.columns([1, 1, 3])

            @st.dialog("✏️ แก้ไขข้อมูลอุปกรณ์", width="large")
            def edit_asset_dialog(asset):
                st.markdown(f"<p style='color:#8BA0BC;font-size:12px;'>กำลังแก้ไข <b style='color:#00C6FF;font-family:DM Mono,monospace;'>{asset['id']}</b></p>", unsafe_allow_html=True)
                with st.form(f"edit_asset_form_{asset['id']}"):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        e_model = st.text_input("ยี่ห้อ/รุ่น", value=asset.get('model','') or "")
                        try:
                            dept_idx = depts.index(asset.get('dept','CHASSIS')) if asset.get('dept') in depts else 0
                        except: dept_idx = 0
                        e_dept = st.selectbox("แผนกที่ใช้งาน", depts, index=dept_idx)
                        e_loc = st.text_input("สถานที่ตั้ง", value=asset.get('location','') or "")
                    with ec2:
                        e_user = st.text_input("ผู้ถือครอง/ผู้รับผิดชอบ", value=asset.get('assigned_user','') or "")
                        # warranty date
                        cur_w = asset.get('warranty_expire')
                        try: w_default = pd.to_datetime(cur_w).date() if cur_w and pd.notna(cur_w) else datetime.now().date()
                        except: w_default = datetime.now().date()
                        e_warranty = st.date_input("วันที่หมดประกัน", value=w_default)
                        e_status = st.selectbox("สถานะ", ["Active","Inactive","Disposed"],
                                                index=["Active","Inactive","Disposed"].index(asset.get('status','Active')) if asset.get('status') in ["Active","Inactive","Disposed"] else 0)
                    if st.form_submit_button("💾 บันทึกการเปลี่ยนแปลง", use_container_width=True):
                        update_asset(asset['id'], {
                            "model": e_model, "dept": e_dept, "location": e_loc,
                            "assigned_user": e_user, "warranty_expire": str(e_warranty),
                            "status": e_status
                        })
                        st.toast(f"บันทึกข้อมูล {asset['id']} สำเร็จ!", icon="✅")
                        st.rerun()

            @st.dialog("⚠️ ยืนยันการยกเลิกอุปกรณ์", width="small")
            def delete_asset_dialog(asset):
                st.markdown(f"""
                <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.4);border-radius:10px;padding:14px;margin-bottom:14px;">
                    <p style="color:#FCA5A5;margin:0;font-weight:600;">⚠️ คุณกำลังจะลบอุปกรณ์นี้ออกจากระบบ</p>
                    <p style="color:#8BA0BC;margin:6px 0 0 0;font-size:12px;">การกระทำนี้ไม่สามารถย้อนกลับได้</p>
                </div>
                <p><b style="color:#E8EDF5;">รหัส:</b> <span style="color:#00C6FF;font-family:DM Mono,monospace;">{asset['id']}</span></p>
                <p><b style="color:#E8EDF5;">รุ่น:</b> <span style="color:#8BA0BC;">{asset.get('model','—')}</span></p>
                <p><b style="color:#E8EDF5;">แผนก:</b> <span style="color:#8BA0BC;">{asset.get('dept','—')}</span></p>
                """, unsafe_allow_html=True)
                confirm_text = st.text_input(f"พิมพ์ **{asset['id']}** เพื่อยืนยัน", placeholder=asset['id'], key=f"del_confirm_{asset['id']}")
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("❌ ยกเลิก", use_container_width=True, key=f"cancel_del_{asset['id']}"):
                        st.rerun()
                with dc2:
                    if st.button("🗑️ ยืนยันลบ", use_container_width=True, key=f"confirm_del_{asset['id']}",
                                 disabled=(confirm_text != asset['id'])):
                        delete_asset(asset['id'])
                        st.toast(f"ลบอุปกรณ์ {asset['id']} แล้ว", icon="🗑️")
                        st.rerun()

            with ab1:
                if st.button("✏️ แก้ไขข้อมูล", use_container_width=True, key=f"edit_btn_{target_asset['id']}"):
                    edit_asset_dialog(target_asset)
            with ab2:
                if st.button("🗑️ ยกเลิกอุปกรณ์", use_container_width=True, key=f"del_btn_{target_asset['id']}"):
                    delete_asset_dialog(target_asset)

            st.write("---")
            st.write("### 🛠️ ประวัติการซ่อมและบำรุงรักษา (PM)")
            tab_repair, tab_pm_hist = st.tabs(["🔧 ประวัติการแจ้งซ่อม","📅 ประวัติการทำ PM"])
            with tab_repair:
                if 'asset_id' in df_t.columns:
                    history = df_t[df_t['asset_id'] == target_asset['id']]
                    if not history.empty:
                        total_cost = pd.to_numeric(history['cost'], errors='coerce').sum()
                        st.metric("💸 ยอดค่าซ่อมสะสม", f"฿{total_cost:,.2f}")
                        h_view = history[['date','user','root_cause','solution','cost','status']].copy()
                        h_view.columns = ['วันที่','ผู้แจ้ง','สาเหตุ','วิธีแก้','ค่าใช้จ่าย','สถานะ']
                        st.dataframe(h_view, use_container_width=True, hide_index=True)
                    else: st.info("✨ อุปกรณ์นี้ยังไม่มีประวัติการซ่อม")
                else: st.warning("⚠️ ไม่พบคอลัมน์ 'asset_id' ในฐานข้อมูล")
            with tab_pm_hist:
                df_pm_hist = load_table("pm_schedules")
                if not df_pm_hist.empty and 'asset_id' in df_pm_hist.columns:
                    asset_pm_hist = df_pm_hist[df_pm_hist['asset_id'] == target_asset['id']]
                    if not asset_pm_hist.empty:
                        pm_view = asset_pm_hist[['next_due_date','task_name','assignee','status','pm_result']].copy()
                        pm_view.columns = ['วันที่กำหนดทำ','ชื่องาน','ผู้รับผิดชอบ','สถานะ','ผลการตรวจสอบ']
                        st.dataframe(pm_view, use_container_width=True, hide_index=True)
                    else: st.info("ยังไม่มีประวัติการทำ PM สำหรับอุปกรณ์นี้")
                else: st.info("ยังไม่มีประวัติการทำ PM สำหรับอุปกรณ์นี้")
        else: st.error("❌ ไม่พบรหัสอุปกรณ์")

# ==========================================
# หน้า 5: แผน PM
# ==========================================
elif page == "🔧 แผนบำรุงรักษา (PM)" and st.session_state.is_admin:
    st.title("🔧 IT Preventive Maintenance System")
    tab_cal, tab_list, tab_add = st.tabs(["📅 ปฏิทินงาน PM","📋 รายการและบันทึกผล","➕ ลงทะเบียนแผนใหม่"])
    df_pm = load_table("pm_schedules")

    with tab_cal:
        if not df_pm.empty:
            # ── คำนวณสถิติ + ตรวจสอบ Overdue ──
            today = datetime.now().date()
            df_pm['_due'] = pd.to_datetime(df_pm['next_due_date']).dt.date
            df_pm['_overdue'] = (df_pm['_due'] < today) & (df_pm['status'] != 'Completed')

            current_month_str = datetime.now().strftime('%Y-%m')
            df_pm['_month'] = pd.to_datetime(df_pm['next_due_date']).dt.strftime('%Y-%m')

            month_total    = len(df_pm[df_pm['_month'] == current_month_str])
            month_done     = len(df_pm[(df_pm['_month'] == current_month_str) & (df_pm['status'] == 'Completed')])
            month_pending  = month_total - month_done
            overdue_count  = int(df_pm['_overdue'].sum())

            # ── Mini Stats ──
            ms1, ms2, ms3, ms4 = st.columns(4)
            with ms1: st.metric("📅 แผนเดือนนี้", f"{month_total} งาน")
            with ms2: st.metric("✅ เสร็จแล้ว", f"{month_done} งาน")
            with ms3: st.metric("🔄 รอดำเนินการ", f"{month_pending} งาน")
            with ms4: st.metric("🚨 เลยกำหนด", f"{overdue_count} งาน",
                                delta=f"{overdue_count} งาน" if overdue_count else "ไม่มี",
                                delta_color="inverse")

            # ── Overdue Alert ──
            if overdue_count > 0:
                overdue_list = df_pm[df_pm['_overdue']].sort_values('_due')
                items_html = ""
                for _, ov in overdue_list.head(5).iterrows():
                    days = (today - ov['_due']).days
                    items_html += f"""<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(239,68,68,0.15);">
                      <span style="color:#FCA5A5;font-size:13px;">⚠️ <b>{ov['task_name']}</b> ({ov.get('assignee','—')})</span>
                      <span style="color:#FCA5A5;font-family:'DM Mono',monospace;font-size:12px;">เลย {days} วัน</span>
                    </div>"""
                more = f"<div style='margin-top:6px;color:#FCA5A5;font-size:12px;'>... และอีก {len(overdue_list)-5} งาน</div>" if len(overdue_list) > 5 else ""
                st.markdown(f"""
                <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.4);
                  border-radius:12px;padding:14px 18px;margin:14px 0;">
                  <div style="font-weight:700;color:#FCA5A5;margin-bottom:8px;font-size:14px;">
                    🚨 มีงาน PM เลยกำหนด {overdue_count} รายการ — กรุณาตรวจสอบ
                  </div>
                  {items_html}{more}
                </div>
                """, unsafe_allow_html=True)

            # ── Filter ──
            with st.expander("🔍 กรองข้อมูลปฏิทิน", expanded=False):
                fc1, fc2, fc3 = st.columns(3)
                with fc1:
                    assignees = ["ทั้งหมด"] + sorted(df_pm['assignee'].dropna().unique().tolist())
                    f_assignee = st.selectbox("👷 ผู้รับผิดชอบ", assignees, key="pm_filter_assignee")
                with fc2:
                    eq_types_list = ["ทั้งหมด"] + sorted(df_pm['equipment_type'].dropna().unique().tolist()) if 'equipment_type' in df_pm.columns else ["ทั้งหมด"]
                    f_eqtype = st.selectbox("🖥️ ประเภทอุปกรณ์", eq_types_list, key="pm_filter_eqtype")
                with fc3:
                    f_status = st.selectbox("📌 สถานะ", ["ทั้งหมด","รอดำเนินการ","เสร็จสิ้น","เลยกำหนด"], key="pm_filter_status")

            # apply filter
            df_view = df_pm.copy()
            if f_assignee != "ทั้งหมด": df_view = df_view[df_view['assignee'] == f_assignee]
            if f_eqtype != "ทั้งหมด" and 'equipment_type' in df_view.columns: df_view = df_view[df_view['equipment_type'] == f_eqtype]
            if f_status == "รอดำเนินการ": df_view = df_view[df_view['status'] != 'Completed']
            elif f_status == "เสร็จสิ้น": df_view = df_view[df_view['status'] == 'Completed']
            elif f_status == "เลยกำหนด": df_view = df_view[df_view['_overdue']]

            # ── Export Schedule ──
            ec1, ec2, _ = st.columns([1,1,3])
            with ec1:
                csv_pm = df_view.drop(columns=['_due','_overdue','_month'], errors='ignore').to_csv(index=False).encode('utf-8-sig')
                st.download_button("📤 Export ตาราง (CSV)", csv_pm,
                    file_name=f"PM_Schedule_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv", use_container_width=True)
            with ec2:
                if st.button("🔄 รีเฟรช", use_container_width=True):
                    st.rerun()

            st.divider()
            st.subheader("📅 ตารางงานบำรุงรักษาประจำเดือน")

            # ── สร้าง events พร้อมสี Overdue ──
            calendar_events = []
            for _, row in df_view.iterrows():
                try:
                    due_date = pd.to_datetime(row['next_due_date']).strftime('%Y-%m-%d')
                    is_done = row['status'] == "Completed"
                    is_overdue = row.get('_overdue', False)
                    if is_done:
                        col, border = "#059669", "#10B981"; icon = "✅"
                    elif is_overdue:
                        col, border = "#DC2626", "#EF4444"; icon = "🚨"
                    else:
                        col, border = "#1E6FD9", "#3B8FFF"; icon = "🔧"
                    calendar_events.append({
                        "id": str(row['id']),
                        "title": f"{icon} {row['task_name']}",
                        "start": due_date, "end": due_date,
                        "color": col, "borderColor": border,
                        "textColor": "#ffffff", "allDay": True,
                    })
                except: continue

            st.markdown("""
            <style>
            .fc { font-family: 'Noto Sans Thai', sans-serif !important; }
            .fc-toolbar-title { font-size:16px !important; font-weight:700 !important; color:#E8EDF5 !important; }
            .fc-button { background:#1E6FD9 !important; border-color:#3B8FFF !important; border-radius:6px !important; font-size:12px !important; }
            .fc-button:hover { background:#3B8FFF !important; }
            .fc-button-active { background:#1557B0 !important; }
            .fc-daygrid-day { background:rgba(17,34,64,0.6) !important; border-color:rgba(30,111,217,0.15) !important; }
            .fc-daygrid-day:hover { background:rgba(30,111,217,0.12) !important; }
            .fc-day-today { background:rgba(30,111,217,0.2) !important; }
            .fc-col-header-cell { background:rgba(17,34,64,0.9) !important; color:#8BA0BC !important; font-size:12px !important; font-weight:600 !important; }
            .fc-daygrid-day-number { color:#8BA0BC !important; font-size:12px !important; }
            .fc-event { border-radius:6px !important; padding:2px 6px !important; font-size:11px !important; cursor:pointer !important; }
            .fc-event:hover { opacity:0.85 !important; }
            .fc-more-link { color:#00C6FF !important; font-size:11px !important; }
            </style>""", unsafe_allow_html=True)

            @st.dialog("📌 รายละเอียดงาน PM", width="large")
            def show_pm_detail(target):
                is_done = target['status'] == "Completed"
                sc = "#10B981" if is_done else "#F59E0B"
                sl = "✅ เสร็จสิ้น" if is_done else "🔄 รอดำเนินการ"
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                  <div style="font-size:16px;font-weight:700;color:#E8EDF5;">{target['task_name']}</div>
                  <div style="background:{'rgba(16,185,129,0.15)' if is_done else 'rgba(245,158,11,0.15)'};
                    color:{sc};border:1px solid {sc}50;border-radius:99px;padding:3px 12px;font-size:12px;font-weight:600;">{sl}</div>
                </div>""", unsafe_allow_html=True)
                ci1, ci2 = st.columns(2)
                with ci1:
                    st.markdown(f"**🔖 รหัสอุปกรณ์:** `{target.get('asset_id','—')}`")
                    st.markdown(f"**📅 วันที่กำหนด:** {target.get('next_due_date','—')}")
                    st.markdown(f"**🔁 ความถี่:** {target.get('frequency','—')}")
                with ci2:
                    st.markdown(f"**👷 ผู้รับผิดชอบ:** {target.get('assignee','—')}")
                    st.markdown(f"**🖥️ ประเภทอุปกรณ์:** {target.get('equipment_type','—')}")
                st.divider()
                st.markdown("**📝 Checklist**")
                st.info(target.get('checklist','ไม่มีข้อมูล Checklist'))
                if is_done and pd.notna(target.get('pm_result')):
                    st.markdown("**✅ ผลการตรวจสอบ**"); st.success(target.get('pm_result'))
                elif not is_done:
                    st.divider()
                    st.markdown("**📋 บันทึกผลการตรวจสอบ**")
                    with st.form(f"pm_dialog_{target['id']}"):
                        res = st.text_area("ผลการตรวจสอบ / ปัญหาที่พบ", placeholder="กรอกผลการตรวจสอบ...")
                        if st.form_submit_button("✅ บันทึกและปิดงาน PM", use_container_width=True):
                            update_pm_full(target['id'], "Completed", res)
                            st.toast("บันทึกผล PM เรียบร้อยแล้ว!", icon="✅"); st.rerun()

            cal_action = calendar(events=calendar_events, options={
                "headerToolbar": {"left":"prev,next today","center":"title","right":"dayGridMonth,listMonth"},
                "initialView": "dayGridMonth", "selectable": True, "editable": False,
                "dayMaxEvents": 3, "height": 580,
            }, key=f"pm_calendar_{len(calendar_events)}")

            if cal_action and "callback" in cal_action:
                cb = cal_action["callback"]
                if cb == "eventClick":
                    event_id = cal_action["eventClick"]["event"]["id"]
                    ev = df_pm[df_pm['id'] == event_id]
                    if not ev.empty: show_pm_detail(ev.iloc[0])

            st.markdown("""
            <div style="display:flex;gap:16px;margin-top:12px;font-size:12px;color:#8BA0BC;flex-wrap:wrap;">
              <span><span style="display:inline-block;width:12px;height:12px;background:#059669;border-radius:3px;margin-right:5px;vertical-align:middle;"></span>เสร็จสิ้น</span>
              <span><span style="display:inline-block;width:12px;height:12px;background:#1E6FD9;border-radius:3px;margin-right:5px;vertical-align:middle;"></span>รอดำเนินการ</span>
              <span><span style="display:inline-block;width:12px;height:12px;background:#DC2626;border-radius:3px;margin-right:5px;vertical-align:middle;"></span>เลยกำหนด</span>
              <span style="color:#4A6080;margin-left:8px;">💡 คลิกชื่องานเพื่อดูรายละเอียดและบันทึกผล</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("💡 ยังไม่มีข้อมูลแผนงาน PM")

    with tab_list:
        if not df_pm.empty:
            today_d = datetime.now().date()
            df_pm_view = df_pm.copy()
            df_pm_view['_due'] = pd.to_datetime(df_pm_view['next_due_date']).dt.date
            df_pm_view['_overdue'] = (df_pm_view['_due'] < today_d) & (df_pm_view['status'] != 'Completed')

            # Filter selector
            fc1, fc2 = st.columns([2, 3])
            with fc1:
                view_mode = st.selectbox("แสดง", ["รอดำเนินการ + เลยกำหนด", "เลยกำหนดเท่านั้น", "เสร็จสิ้นแล้ว", "ทั้งหมด"], key="pm_list_view")
            with fc2:
                pm_search = st.text_input("🔍 ค้นหา", placeholder="พิมพ์ชื่องาน, Asset ID, ผู้รับผิดชอบ...", key="pm_list_search", label_visibility="collapsed")

            df_pm_list = df_pm_view.copy()
            if view_mode == "รอดำเนินการ + เลยกำหนด":
                df_pm_list = df_pm_list[df_pm_list['status'] != 'Completed']
            elif view_mode == "เลยกำหนดเท่านั้น":
                df_pm_list = df_pm_list[df_pm_list['_overdue']]
            elif view_mode == "เสร็จสิ้นแล้ว":
                df_pm_list = df_pm_list[df_pm_list['status'] == 'Completed']

            if pm_search:
                q = pm_search.lower()
                df_pm_list = df_pm_list[df_pm_list.apply(
                    lambda r: any(q in str(r.get(c,'')).lower() for c in ['task_name','asset_id','assignee','id']),
                    axis=1
                )]

            # เรียง: เลยกำหนดมาก่อน → รอดำเนินการ → เสร็จสิ้น, แล้วเรียงตามวันที่
            df_pm_list['_status_order'] = df_pm_list.apply(
                lambda r: 0 if r['_overdue'] else (1 if r['status'] != 'Completed' else 2), axis=1
            )
            df_pm_list = df_pm_list.sort_values(by=['_status_order','_due'], ascending=[True, True])

            st.markdown(f"<p style='color:#8BA0BC;margin:10px 0;font-size:13px;'>พบ <b style='color:#E8EDF5;'>{len(df_pm_list)}</b> รายการ — คลิกที่การ์ดเพื่อบันทึกผล / ดูรายละเอียด</p>", unsafe_allow_html=True)

            # ── Dialog: บันทึกผล / ดูรายละเอียด ──
            @st.dialog("🔧 รายละเอียดงาน PM", width="large")
            def pm_detail_dialog(pm):
                pid = pm['id']
                is_done = pm['status'] == 'Completed'
                is_overdue = bool(pm.get('_overdue', False))

                # Header
                if is_done:
                    badge_cls, badge_text = "status-สำเร็จ", "✅ เสร็จสิ้น"
                elif is_overdue:
                    badge_cls, badge_text = "status-รอตรวจสอบ", "🚨 เลยกำหนด"
                else:
                    badge_cls, badge_text = "status-ดำเนินการ", "🔧 รอดำเนินการ"

                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                  <div>
                    <span style="font-family:'DM Mono',monospace;font-size:12px;color:#00C6FF;">{pid}</span>
                    <span style="margin-left:10px;" class="status-badge {badge_cls}">{badge_text}</span>
                  </div>
                  <div style="font-size:12px;color:#4A6080;">📅 {pm.get('next_due_date','')}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"### {pm.get('task_name','—')}")

                ci1, ci2 = st.columns(2)
                with ci1:
                    st.markdown(f"**🖥️ ประเภทอุปกรณ์:** {pm.get('equipment_type','—')}")
                    st.markdown(f"**🔖 รหัสอุปกรณ์:** `{pm.get('asset_id','—')}`")
                with ci2:
                    st.markdown(f"**👷 ผู้รับผิดชอบ:** {pm.get('assignee','—')}")
                    st.markdown(f"**🔁 ความถี่:** {pm.get('frequency','—')}")

                st.divider()
                st.markdown("**📝 Checklist ที่ต้องตรวจสอบ**")
                st.info(pm.get('checklist','ไม่มีข้อมูล Checklist'))

                if is_done:
                    st.divider()
                    st.markdown("**✅ ผลการตรวจสอบ**")
                    st.success(pm.get('pm_result') or "ไม่มีบันทึกผล")
                else:
                    # ── ฟอร์มบันทึกผล ──
                    st.divider()
                    st.markdown("### ✏️ บันทึกผลการตรวจสอบ")
                    with st.form(f"pm_save_{pid}"):
                        result_text = st.text_area("ผลการตรวจสอบ / ปัญหาที่พบ",
                                                   placeholder="ระบุสิ่งที่ตรวจพบ, ปัญหา, หรือการดำเนินการที่ทำ...",
                                                   height=120)
                        if st.form_submit_button("✅ บันทึกและปิดงาน PM", use_container_width=True):
                            update_pm_full(pid, "Completed", result_text)
                            st.toast(f"บันทึกผล {pid} สำเร็จ!", icon="✅")
                            st.rerun()

            # ── Render Cards ──
            if df_pm_list.empty:
                st.success("🎉 ไม่มีรายการที่ตรงกับเงื่อนไข")
            else:
                for _, pm in df_pm_list.iterrows():
                    is_done = pm['status'] == 'Completed'
                    is_overdue = bool(pm.get('_overdue', False))
                    if is_done:
                        badge_cls, badge_text = "status-สำเร็จ", "✅ เสร็จสิ้น"
                        days_html = ""
                    elif is_overdue:
                        badge_cls, badge_text = "status-รอตรวจสอบ", "🚨 เลยกำหนด"
                        days_late = (today_d - pm['_due']).days
                        days_html = f'<div style="font-size:11px;color:#FCA5A5;margin-top:6px;">เลย {days_late} วัน</div>'
                    else:
                        badge_cls, badge_text = "status-ดำเนินการ", "🔧 รอทำ"
                        days_left = (pm['_due'] - today_d).days
                        days_html = f'<div style="font-size:11px;color:#FCD34D;margin-top:6px;">อีก {days_left} วัน</div>' if days_left >= 0 else ""

                    col_card, col_btn = st.columns([11, 1])
                    # ── ช่วยจัดการ NaN / None / empty ในการ์ด ──
                    def _sf(v, default='—'):
                        if v is None: return default
                        try:
                            if pd.isna(v): return default
                        except (TypeError, ValueError): pass
                        s = str(v).strip()
                        return s if s and s.lower() != 'nan' else default

                    pm_id        = _sf(pm.get('id'), '—')
                    pm_id_short  = pm_id[:24] + ('...' if len(pm_id) > 24 else '')
                    pm_task      = _sf(pm.get('task_name'))
                    pm_due       = _sf(pm.get('next_due_date'), '')
                    pm_eq        = _sf(pm.get('equipment_type'))
                    pm_asset     = _sf(pm.get('asset_id'))
                    pm_assignee  = _sf(pm.get('assignee'), 'ยังไม่มอบหมาย')
                    pm_freq      = _sf(pm.get('frequency'))

                    with col_card:
                        st.markdown(f"""<div class="ticket-card"><div class="ticket-card-left"><div class="ticket-id">{pm_id_short}</div><div class="ticket-user">{pm_task}</div><div class="ticket-date">📅 {pm_due}</div></div><div class="ticket-card-mid"><div class="ticket-cat">🖥️ {pm_eq} &nbsp;|&nbsp; 🔖 {pm_asset}</div><div class="ticket-cat" style="margin-top:4px;">👷 {pm_assignee} &nbsp;|&nbsp; 🔁 {pm_freq}</div></div><div class="ticket-card-right"><div><span class="status-badge {badge_cls}">{badge_text}</span></div>{days_html}</div></div>""", unsafe_allow_html=True)
                    with col_btn:
                        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
                        icon = "🔍" if is_done else "✏️"
                        if st.button(icon, key=f"pm_view_{pm['id']}", help="ดู / บันทึกผล", use_container_width=True):
                            pm_detail_dialog(pm)
        else:
            st.info("ยังไม่มีแผนงาน PM ในระบบ")

    with tab_add:
        st.subheader("➕ เพิ่มแผนบำรุงรักษาและจัดตารางอัตโนมัติ")
        with st.form("pm_auto_form"):
            asset_id_pm = st.text_input("รหัสอุปกรณ์ (Asset ID)*", placeholder="เช่น CCTV-001")
            eq_type = st.selectbox("ประเภทอุปกรณ์", ["Computer PC","Notebook","TEC Printer","Laser Printer","IPDS Printer","TV","CCTV","Server room","Other"])
            c1, c2 = st.columns(2)
            with c1:
                s_date = st.date_input("เริ่มตั้งแต่วันที่")
                freq = st.selectbox("ความถี่", ["รายวัน","รายสัปดาห์","รายเดือน","รายปี"])
            with c2:
                assign = st.text_input("ช่างผู้รับผิดชอบ")
                count = st.number_input("จำนวนครั้งที่ต้องการวางแผนล่วงหน้า", min_value=1, value=12)
            check = st.text_area("รายการ Checklist")
            if st.form_submit_button("📅 บันทึกและจัดตารางลงปฏิทิน"):
                if asset_id_pm and assign and check:
                    curr_date = s_date; current_year = datetime.now().year
                    for i in range(int(count)):
                        unique_suffix = uuid.uuid4().hex[:6].upper()
                        unique_id = f"PM-{asset_id_pm}-{eq_type}({i+1}/{int(count)}){current_year}-{unique_suffix}"
                        insert_data("pm_schedules", {"id":unique_id,"task_name":f"PM {eq_type}: {asset_id_pm} ({i+1}/{int(count)})","next_due_date":str(curr_date),"status":"Scheduled","assignee":assign,"checklist":check,"frequency":freq,"asset_id":asset_id_pm,"equipment_type":eq_type})
                        if freq == "รายวัน": curr_date += relativedelta(days=1)
                        elif freq == "รายสัปดาห์": curr_date += relativedelta(weeks=1)
                        elif freq == "รายเดือน": curr_date += relativedelta(months=1)
                        elif freq == "รายปี": curr_date += relativedelta(years=1)
                    st.success(f"✅ สร้างแผนงานสำเร็จ! จำนวน {int(count)} รายการสำหรับ {asset_id_pm}"); st.rerun()
                else: st.error("❌ กรุณากรอกข้อมูลให้ครบถ้วน (Asset ID, ผู้รับผิดชอบ, Checklist)")

# ==========================================
# หน้า 6: 🔔 Notification Settings
# ==========================================
elif page == "🔔 Notifications" and st.session_state.is_admin:
    st.title("🔔 การแจ้งเตือน Telegram")

    # Status block
    token, chat_id, enabled = _tg_config()
    if not token or not chat_id:
        st.warning("⚠️ ยังไม่ได้ตั้งค่า Telegram — โปรดเพิ่ม `TELEGRAM_BOT_TOKEN` และ `TELEGRAM_CHAT_ID` ใน Streamlit secrets")
    elif not enabled:
        st.info("ℹ️ Telegram ถูกปิดอยู่ ตั้ง `TELEGRAM_ENABLED = true` ใน secrets เพื่อเปิดใช้งาน")
    else:
        st.markdown("""
        <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.4);border-radius:10px;padding:12px 16px;margin-bottom:16px;">
          <span style="color:#6EE7B7;font-weight:600;">✅ Telegram พร้อมใช้งาน</span>
        </div>
        """, unsafe_allow_html=True)

    # ── ทดสอบส่งข้อความ ──
    st.subheader("🧪 ทดสอบส่งข้อความ")
    with st.form("test_telegram_form"):
        test_msg = st.text_area("ข้อความทดสอบ", value="🧪 ทดสอบการแจ้งเตือนจาก ILT IT Helpdesk\nเชื่อมต่อสำเร็จ!", height=80)
        if st.form_submit_button("📨 ส่งทดสอบ", use_container_width=True):
            ok, info = send_telegram(test_msg)
            if ok: st.success(f"✅ {info}")
            else: st.error(f"❌ {info}")

    st.divider()

    # ── ปุ่มส่งรายงานทันที ──
    st.subheader("📊 ส่งรายงานทันที")
    rc1, rc2 = st.columns(2)
    with rc1:
        if st.button("📅 ส่งรายงานประจำวัน", use_container_width=True):
            ok, info = send_daily_summary()
            if ok: st.success(f"✅ {info}")
            else: st.error(f"❌ {info}")
    with rc2:
        if st.button("📈 ส่งรายงานประจำสัปดาห์", use_container_width=True):
            ok, info = send_weekly_summary()
            if ok: st.success(f"✅ {info}")
            else: st.error(f"❌ {info}")

    st.divider()

    # ── ประเภทการแจ้งเตือน ──
    st.subheader("📋 ประเภทการแจ้งเตือนที่ระบบส่ง")
    notifications_info = [
        ("🆕", "ticket ใหม่",             "ทันที เมื่อ user ส่งใบแจ้งซ่อม",            "Real-time"),
        ("🚨", "งานด่วนมาก",              "ทันที พร้อมเสียงเตือน",                       "Real-time + Alert"),
        ("✅", "ปิดงานสำเร็จ",            "เมื่อช่างเปลี่ยน status เป็น 'สำเร็จ'",       "Real-time"),
        ("📅", "รายงานประจำวัน",          "ทุกวัน 08:00 น.",                             "Daily"),
        ("📈", "รายงานประจำสัปดาห์",      "ทุกศุกร์ 17:00 น.",                           "Weekly"),
        ("🚨", "PM เลยกำหนด",             "ทุกวัน 09:00 น. (เฉพาะถ้ามีงานเลยกำหนด)",     "Daily"),
    ]
    rows_html = ""
    for icon, name, when, freq in notifications_info:
        rows_html += f"""
        <tr>
          <td style="padding:10px;font-size:18px;">{icon}</td>
          <td style="padding:10px;color:#E8EDF5;font-weight:500;">{name}</td>
          <td style="padding:10px;color:#8BA0BC;font-size:13px;">{when}</td>
          <td style="padding:10px;"><span class="status-badge status-ดำเนินการ">{freq}</span></td>
        </tr>"""
    st.markdown(f"""
    <table style="width:100%;border-collapse:collapse;background:rgba(17,34,64,0.85);border:1px solid rgba(30,111,217,0.25);border-radius:12px;overflow:hidden;">
      <thead><tr style="background:rgba(30,111,217,0.1);">
        <th style="padding:10px;text-align:left;color:#8BA0BC;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;width:50px;"></th>
        <th style="padding:10px;text-align:left;color:#8BA0BC;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;">ประเภท</th>
        <th style="padding:10px;text-align:left;color:#8BA0BC;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;">เงื่อนไข</th>
        <th style="padding:10px;text-align:left;color:#8BA0BC;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;">ความถี่</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    st.divider()

    # ── คู่มือ Setup ──
    with st.expander("📖 คู่มือ Setup Telegram Bot (ครั้งแรก)"):
        st.markdown("""
        ### ขั้นตอน Setup

        **1. สร้าง Bot ใน Telegram**
        - เปิด Telegram → ค้นหา `@BotFather` → กด Start
        - พิมพ์ `/newbot` → ตั้งชื่อ (เช่น `ILT IT Helpdesk Bot`) → ตั้ง username (เช่น `ilt_helpdesk_bot`)
        - BotFather จะส่ง **Bot Token** กลับมา รูปแบบ `123456:ABC-DEF...` → คัดลอกเก็บไว้

        **2. สร้างกลุ่มและ invite Bot**
        - สร้าง Group ใหม่ใน Telegram ชื่อ "IT Team Notifications"
        - เพิ่มสมาชิกทีม IT ทั้งหมด
        - กดเพิ่ม Bot ของคุณเข้ากลุ่ม → ตั้งเป็น Admin (ให้สิทธิ์ส่งข้อความ)

        **3. หา Chat ID ของกลุ่ม**
        - ส่งข้อความใดๆ ในกลุ่ม (เช่น "hi bot")
        - เปิดเบราว์เซอร์ → วาง URL นี้ (แทนที่ `<TOKEN>` ด้วย Bot Token):
        ```
        https://api.telegram.org/bot<TOKEN>/getUpdates
        ```
        - ดูค่า `"chat":{"id":-123456789,...}` → คัดลอกเลข Chat ID (มีเครื่องหมาย `-` นำหน้าสำหรับ group)

        **4. ตั้งค่า Streamlit Secrets**
        - Streamlit Cloud → Manage App → Settings → Secrets
        - เพิ่มบรรทัด:
        ```toml
        TELEGRAM_BOT_TOKEN = "123456:ABC-DEF_your_token_here"
        TELEGRAM_CHAT_ID = "-123456789"
        TELEGRAM_ENABLED = true
        ```
        - Save แล้ว Reboot app

        **5. ทดสอบ**
        - กลับมาที่หน้านี้ → กดปุ่ม "📨 ส่งทดสอบ" → ดูข้อความเด้งในกลุ่ม Telegram

        ### รายงานรายวัน/รายสัปดาห์ (ตั้งเวลาอัตโนมัติ)
        จะต้องตั้ง GitHub Actions แยก (ดูไฟล์ `.github/workflows/scheduled_reports.yml`)
        """)
