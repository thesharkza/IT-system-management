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
import uuid  # เพิ่มสำหรับแก้ไข Race Condition (ข้อ 2)

# =========================================================
# แก้ไขข้อ 3: ย้าย st.set_page_config() ขึ้นมาเป็นบรรทัดแรกสุด
# ก่อน st.markdown() และคำสั่ง UI อื่น ๆ ทั้งหมด
# =========================================================
st.set_page_config(
    page_title="ILT IT Helpdesk",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────
#  ENTERPRISE UI  —  "Steel & Precision" Design System
#  โทนสี: Deep Navy (#0B1829) + Steel Blue (#1E6FD9) + Warm White
#  ฟอนต์: Noto Sans Thai (ภาษาไทยคมชัด) + DM Mono (ID/ตัวเลข)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── CSS Variables ─────────────────────────────────── */
:root {
    --navy:       #0B1829;
    --navy-mid:   #112240;
    --navy-light: #1A3356;
    --blue:       #1E6FD9;
    --blue-light: #3B8FFF;
    --blue-glow:  rgba(30,111,217,0.18);
    --accent:     #00C6FF;
    --warn:       #F59E0B;
    --danger:     #EF4444;
    --success:    #10B981;
    --purple:     #8B5CF6;
    --text-primary:   #E8EDF5;
    --text-secondary: #8BA0BC;
    --text-muted:     #4A6080;
    --border:     rgba(30,111,217,0.25);
    --border-subtle: rgba(255,255,255,0.07);
    --card-bg:    rgba(17,34,64,0.85);
    --sidebar-bg: #0D1F38;
    --radius:     12px;
    --radius-lg:  18px;
    --shadow:     0 4px 24px rgba(0,0,0,0.35);
    --shadow-blue:0 4px 20px rgba(30,111,217,0.3);
}

/* ── Global Base ───────────────────────────────────── */
html, body, [class*="css"], .stApp {
    font-family: 'Noto Sans Thai', sans-serif !important;
    background-color: var(--navy) !important;
    color: var(--text-primary) !important;
}

/* subtle grid texture overlay */
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

/* ── Sidebar ───────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* Sidebar header brand block */
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--text-primary) !important;
    letter-spacing: 0.04em;
}

/* Nav radio group */
[data-testid="stSidebar"] div[role="radiogroup"] { gap: 4px !important; }
[data-testid="stSidebar"] div[role="radiogroup"] label {
    display: flex !important;
    align-items: center !important;
    padding: 11px 16px !important;
    border-radius: 10px !important;
    margin-bottom: 3px !important;
    border: 1px solid transparent !important;
    transition: all 0.18s ease !important;
    width: 100% !important;
    cursor: pointer !important;
    background: transparent !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(30,111,217,0.12) !important;
    border-color: var(--border) !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label p {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    margin: 0 !important;
    letter-spacing: 0.02em;
}
[data-testid="stSidebar"] div[role="radiogroup"] [data-checked="true"] {
    background: linear-gradient(135deg, var(--blue), #1557B0) !important;
    border-color: var(--blue-light) !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] [data-checked="true"] p {
    color: #fff !important;
    font-weight: 600 !important;
}
/* hide radio dot */
[data-testid="stSidebar"] .st-bo { display: none !important; }

/* Sidebar divider */
[data-testid="stSidebar"] hr {
    border-color: var(--border) !important;
    margin: 12px 0 !important;
}

/* Sidebar title */
[data-testid="stSidebar"] h1 {
    font-size: 15px !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
}

/* ── Main Content Area ─────────────────────────────── */
.main .block-container {
    padding: 28px 36px !important;
    max-width: 1400px !important;
}

/* ── Page Headers ──────────────────────────────────── */
h1 {
    font-size: 26px !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.01em !important;
    margin-bottom: 4px !important;
}
h2 {
    font-size: 20px !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
}
h3 {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

/* ── Metric Cards ──────────────────────────────────── */
[data-testid="metric-container"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 20px 24px !important;
    backdrop-filter: blur(12px) !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-blue) !important;
    border-color: var(--blue) !important;
}
[data-testid="metric-container"] label {
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--text-secondary) !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 28px !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

/* ── Tabs ──────────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 2px solid var(--border) !important;
    gap: 4px !important;
    background: transparent !important;
}
[data-testid="stTabs"] [role="tab"] {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    padding: 10px 20px !important;
    border-radius: 8px 8px 0 0 !important;
    border: 1px solid transparent !important;
    border-bottom: none !important;
    transition: all 0.15s ease !important;
    background: transparent !important;
}
[data-testid="stTabs"] [role="tab"]:hover {
    color: var(--text-primary) !important;
    background: var(--blue-glow) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--accent) !important;
    border-color: var(--border) !important;
    background: var(--card-bg) !important;
    font-weight: 600 !important;
}
[data-testid="stTabContent"] {
    padding-top: 20px !important;
}

/* ── Buttons ───────────────────────────────────────── */
.stButton > button {
    font-family: 'Noto Sans Thai', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
    background: linear-gradient(135deg, var(--blue) 0%, #1557B0 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 22px !important;
    transition: all 0.18s ease !important;
    box-shadow: 0 2px 12px rgba(30,111,217,0.25) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(30,111,217,0.45) !important;
    background: linear-gradient(135deg, var(--blue-light) 0%, var(--blue) 100%) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* Download button variant */
[data-testid="stDownloadButton"] > button {
    font-family: 'Noto Sans Thai', sans-serif !important;
    background: transparent !important;
    border: 1px solid var(--blue) !important;
    color: var(--blue-light) !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 9px 18px !important;
    transition: all 0.18s ease !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: var(--blue-glow) !important;
    border-color: var(--blue-light) !important;
    color: #fff !important;
}

/* Form submit button */
[data-testid="stFormSubmitButton"] > button {
    font-family: 'Noto Sans Thai', sans-serif !important;
    background: linear-gradient(135deg, var(--blue) 0%, #1557B0 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 11px 28px !important;
    width: 100% !important;
    transition: all 0.18s ease !important;
    box-shadow: var(--shadow-blue) !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 28px rgba(30,111,217,0.5) !important;
}

/* ── Form Inputs ───────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
    background: var(--navy-mid) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-family: 'Noto Sans Thai', sans-serif !important;
    font-size: 13px !important;
    padding: 10px 14px !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: var(--blue) !important;
    box-shadow: 0 0 0 3px var(--blue-glow) !important;
    outline: none !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stDateInput"] label,
[data-testid="stFileUploader"] label {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    margin-bottom: 4px !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div > div {
    background: var(--navy-mid) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}
[data-testid="stSelectbox"] > div > div:hover {
    border-color: var(--blue) !important;
}

/* Date input */
[data-testid="stDateInput"] input {
    background: var(--navy-mid) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}

/* ── Dataframe / Table ─────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    overflow: hidden !important;
    border: 1px solid var(--border) !important;
}
[data-testid="stDataFrame"] iframe {
    border-radius: var(--radius) !important;
}
.stTable td, .stTable th { text-align: center !important; }
.stTable {
    background: var(--card-bg) !important;
    border-radius: var(--radius) !important;
    overflow: hidden !important;
}
.stTable th {
    background: var(--navy-light) !important;
    color: var(--text-secondary) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
.stTable td {
    color: var(--text-primary) !important;
    border-color: var(--border-subtle) !important;
    font-size: 13px !important;
}

/* ── Alert / Info / Success / Error ───────────────── */
[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    border: 1px solid !important;
    font-size: 13px !important;
}
.stSuccess {
    background: rgba(16,185,129,0.1) !important;
    border-color: rgba(16,185,129,0.4) !important;
    color: #6EE7B7 !important;
}
.stError {
    background: rgba(239,68,68,0.1) !important;
    border-color: rgba(239,68,68,0.4) !important;
    color: #FCA5A5 !important;
}
.stWarning {
    background: rgba(245,158,11,0.1) !important;
    border-color: rgba(245,158,11,0.4) !important;
    color: #FCD34D !important;
}
.stInfo {
    background: rgba(30,111,217,0.1) !important;
    border-color: rgba(30,111,217,0.35) !important;
    color: #93C5FD !important;
}

/* ── Expander ──────────────────────────────────────── */
[data-testid="stExpander"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    padding: 14px 18px !important;
}
[data-testid="stExpander"] summary:hover {
    background: var(--blue-glow) !important;
}

/* ── Divider ───────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 20px 0 !important;
}

/* ── File Uploader ─────────────────────────────────── */
[data-testid="stFileUploader"] > div {
    background: var(--navy-mid) !important;
    border: 1px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    transition: border-color 0.15s ease !important;
}
[data-testid="stFileUploader"] > div:hover {
    border-color: var(--blue) !important;
}

/* ── Radio Buttons ─────────────────────────────────── */
[data-testid="stRadio"] label {
    color: var(--text-primary) !important;
    font-size: 13px !important;
}

/* ── Number Input ──────────────────────────────────── */
[data-testid="stNumberInput"] button {
    background: var(--navy-light) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
}

/* ── Scrollbar ─────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--navy); }
::-webkit-scrollbar-thumb { background: var(--navy-light); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: var(--blue); }

/* ── Toast ─────────────────────────────────────────── */
[data-testid="stToast"] {
    background: var(--navy-mid) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
}

/* ── Form Container ────────────────────────────────── */
[data-testid="stForm"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 24px !important;
    backdrop-filter: blur(12px) !important;
}

/* ── Bar Chart ─────────────────────────────────────── */
[data-testid="stArrowVegaLiteChart"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 16px !important;
}

/* ── Sidebar login block ────────────────────────────── */
[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,0.06) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
    font-size: 13px !important;
}

/* ── Page-specific header band ─────────────────────── */
.page-header {
    background: linear-gradient(135deg, var(--navy-mid) 0%, var(--navy-light) 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 22px 28px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 14px;
}
.page-header-icon {
    font-size: 28px;
    line-height: 1;
}
.page-header-title {
    font-size: 22px;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    letter-spacing: -0.01em;
}
.page-header-sub {
    font-size: 12px;
    color: var(--text-secondary);
    margin: 2px 0 0 0;
    font-weight: 400;
}

/* ── Status Badge Chip ─────────────────────────────── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.badge-wait   { background: rgba(239,68,68,0.15);  color: #FCA5A5; border: 1px solid rgba(239,68,68,0.3); }
.badge-active { background: rgba(245,158,11,0.15); color: #FCD34D; border: 1px solid rgba(245,158,11,0.3); }
.badge-done   { background: rgba(16,185,129,0.15); color: #6EE7B7; border: 1px solid rgba(16,185,129,0.3); }
.badge-send   { background: rgba(139,92,246,0.15); color: #C4B5FD; border: 1px solid rgba(139,92,246,0.3); }

/* ── Sidebar brand logo area ───────────────────────── */
.sidebar-brand {
    padding: 20px 16px 12px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 12px;
}
.sidebar-brand-title {
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.01em;
    margin: 0;
}
.sidebar-brand-sub {
    font-size: 11px;
    color: var(--text-muted);
    font-family: 'DM Mono', monospace;
    margin: 2px 0 0 0;
    letter-spacing: 0.05em;
}

/* ── Stagger fade-in animation ─────────────────────── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
.main .block-container > * {
    animation: fadeUp 0.3s ease both;
}

</style>
""", unsafe_allow_html=True)

# ── Sidebar brand block ──────────────────────────────
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

# =========================================================
# แก้ไขข้อ 4 (ฟอนต์ไทยใน PDF): เพิ่มฟังก์ชัน _setup_thai_font()
# ลำดับความสำคัญ: THSarabunNew → Prompt-Regular → fallback ใช้ latin
# แทนที่จะ fallback เป็น Arial ซึ่งแสดงภาษาไทยไม่ได้
# =========================================================
def _setup_thai_font(pdf: FPDF) -> str:
    """
    ลองโหลดฟอนต์ที่รองรับภาษาไทยตามลำดับ
    คืนค่าชื่อ family ที่ใช้งานได้ หรือ None ถ้าไม่พบเลย
    """
    font_candidates = [
        ("ThaiSarabun", "THSarabunNew.ttf"),
        ("ThaiPrompt",  "Prompt-Regular.ttf"),
    ]
    for family, filename in font_candidates:
        if os.path.exists(filename):
            try:
                pdf.add_font(family, "", filename)
                return family
            except Exception:
                continue
    # ไม่พบฟอนต์ไทยเลย — ใช้ Helvetica (ตัวอักษรลาตินล้วน)
    return None


def generate_repair_pdf(tk, img_base64=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)

    # =========================================================
    # แก้ไขข้อ 4: ใช้ฟังก์ชัน _setup_thai_font() แทนการ try/except เดิม
    # =========================================================
    thai_family = _setup_thai_font(pdf)
    if thai_family:
        pdf.set_font(thai_family, size=16)
    else:
        pdf.set_font("Helvetica", size=16)
        # แสดง warning บนหน้า PDF ให้ผู้ดูแลทราบ
        pdf.set_text_color(200, 0, 0)
        pdf.cell(190, 8, txt="[WARNING: Thai font not found - text may not display correctly]", ln=True)
        pdf.set_text_color(0, 0, 0)

    # Header
    pdf.cell(190, 10, txt="IT SERVICE REPORT (ใบงานซ่อมคอมพิวเตอร์)", align='C', ln=True)
    pdf.set_font(pdf.font_family, size=12)
    pdf.ln(5)

    pdf.cell(95, 10, txt=f"หมายเลขงาน: {tk.get('id', '')}")
    pdf.cell(95, 10, txt=f"วันที่แจ้ง: {tk.get('date', '')}", ln=True)
    pdf.cell(95, 10, txt=f"ผู้แจ้ง: {tk.get('user', '')}")
    pdf.cell(95, 10, txt=f"แผนก: {tk.get('dept', '')}", ln=True)
    pdf.cell(190, 10, txt=f"สถานที่ตั้ง: {tk.get('location', 'ไม่ได้ระบุ')}", ln=True)
    pdf.ln(2)

    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 10, txt=" รายละเอียดอุปกรณ์และปัญหา", ln=True, fill=True)
    pdf.cell(95, 10, txt=f"ประเภทอุปกรณ์: {tk.get('equipment_type', 'ไม่ได้ระบุ')}")
    pdf.cell(95, 10, txt=f"รหัสทรัพย์สิน: {tk.get('asset_id', 'ไม่ได้ระบุ')}", ln=True)
    pdf.set_x(10)
    pdf.multi_cell(190, 10, txt=f"อาการที่แจ้ง: {tk.get('desc', '')}")
    pdf.ln(2)

    pdf.cell(190, 10, txt=" รายละเอียดการแก้ไข (Technician Report)", ln=True, fill=True)
    pdf.cell(95, 10, txt=f"ช่างผู้รับผิดชอบ: {tk.get('assignee', 'ไม่ได้ระบุ')}")
    pdf.cell(95, 10, txt=f"สถานะ: {tk.get('status', '')}", ln=True)
    pdf.set_x(10)
    pdf.multi_cell(190, 10, txt=f"สาเหตุ: {tk.get('root_cause', '') or 'ไม่ได้ระบุ'}")
    pdf.set_x(10)
    pdf.multi_cell(190, 10, txt=f"วิธีแก้ไข: {tk.get('solution', '') or 'ไม่ได้ระบุ'}")

    cost_val = tk.get('cost', 0)
    try: cost_val = float(cost_val)
    except: cost_val = 0.0
    pdf.set_x(10)
    pdf.cell(190, 10, txt=f"ค่าใช้จ่าย: {cost_val:,.2f} บาท", ln=True)

    if img_base64 and str(img_base64).startswith('data:image'):
        pdf.ln(5)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 10, txt=" รูปภาพประกอบการแจ้งซ่อม", ln=True, fill=True)
        pdf.ln(5)
        try:
            b64_data = img_base64.split(',')[1]
            img_bytes = base64.b64decode(b64_data)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                tmp_file.write(img_bytes)
                tmp_file_path = tmp_file.name
            if pdf.get_y() > 200:
                pdf.add_page()
            pdf.image(tmp_file_path, w=90)
            pdf.ln(5)
            os.remove(tmp_file_path)
        except Exception:
            pdf.set_x(10)
            pdf.cell(190, 10, txt="[ไม่สามารถโหลดรูปภาพลง PDF ได้]", ln=True)

    pdf.ln(15)
    pdf.cell(63, 10, txt="................................", align='C')
    pdf.cell(63, 10, txt="................................", align='C')
    pdf.cell(63, 10, txt="................................", align='C', ln=True)
    pdf.cell(63, 10, txt="(ลงชื่อผู้แจ้ง/รับงาน)", align='C')
    pdf.cell(63, 10, txt="(ลงชื่อช่างผู้ซ่อม)", align='C')
    pdf.cell(63, 10, txt="(ผู้อนุมัติ / MGR)", align='C', ln=True)

    return bytes(pdf.output())


# --- CONFIG ---
rating_scale = {"พอใจมากที่สุด": 5, "พอใจ": 4, "ปานกลาง": 3, "ไม่พอใจ": 2, "ไม่พอใจอย่างมาก": 1}
scale_options = list(rating_scale.keys())
depts = [
    "CHASSIS", "PANEL", "LOGISTICS", "QC", "CCR", "FINANCE", "HR", 
    "PROCUREMENT", "PACKAGING DESIGN", "PRODUCTION PLANNING & PROJECT CONTROL", 
    "SERVICE PARTS DIVISION", "IMPORT-EXPORT OPERATION", "MOTOR POOL OPERATION", "Other"
]
ticket_statuses = ["รอตรวจสอบ", "ดำเนินการ", "ส่งซ่อม", "สำเร็จ"]

# --- LOGIN SYSTEM ---
ADMIN_PASSWORD = "itpassword123"
if "is_admin" not in st.session_state: st.session_state.is_admin = False

# ── Login / Admin block ──────────────────────────────
if not st.session_state.is_admin:
    st.sidebar.markdown('<div class="login-box"><p class="login-box-title">🔐 Admin Login</p></div>', unsafe_allow_html=True)
    admin_pass = st.sidebar.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter admin password")
    if st.sidebar.button("เข้าสู่ระบบ", use_container_width=True):
        if admin_pass == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.rerun()
        else:
            st.sidebar.error("รหัสผ่านไม่ถูกต้อง")
else:
    st.sidebar.markdown("""
    <div class="admin-badge">
        <div class="admin-dot"></div>
        <p class="admin-badge-text">IT Admin Mode</p>
    </div>
    """, unsafe_allow_html=True)
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.is_admin = False
        st.rerun()

st.sidebar.markdown("<hr style='border-color:var(--border);margin:14px 0;'>", unsafe_allow_html=True)
st.sidebar.markdown('<p class="nav-section-label">Navigation</p>', unsafe_allow_html=True)

# ── Menu ใช้ st.radio() แบบเดิม — คลิกตรง ไม่มีจุดไข่ปลา ──
menu_options = [
    "📝  แจ้งซ่อม / ติดตามงาน",
    "💻  จัดการงานซ่อม",
    "📊  Dashboard & รายงาน",
    "🗄️  ทะเบียนอุปกรณ์",
    "🔧  แผนบำรุงรักษา (PM)",
] if st.session_state.is_admin else [
    "📝  แจ้งซ่อม / ติดตามงาน",
]
page_label = st.sidebar.radio("ไปที่หน้า", menu_options, label_visibility="collapsed")

# map label → page key เดิม
_page_map = {
    "📝  แจ้งซ่อม / ติดตามงาน":  "📝 แจ้งซ่อม (User)",
    "💻  จัดการงานซ่อม":          "💻 จัดการงานซ่อม (ช่าง)",
    "📊  Dashboard & รายงาน":     "📊 Dashboard",
    "🗄️  ทะเบียนอุปกรณ์":         "🗄️ ทะเบียนอุปกรณ์",
    "🔧  แผนบำรุงรักษา (PM)":     "🔧 แผนบำรุงรักษา (PM)",
}
page = _page_map.get(page_label, "📝 แจ้งซ่อม (User)")

st.sidebar.markdown("""
<style>
/* ── Login / Admin badges ── */
.login-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    margin: 0 0 16px 0;
}
.login-box-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 0 0 12px 0;
}
.admin-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(16,185,129,0.12);
    border: 1px solid rgba(16,185,129,0.3);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 10px;
}
.admin-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 6px #10B981;
    flex-shrink: 0;
}
.admin-badge-text {
    font-size: 12px;
    font-weight: 600;
    color: #6EE7B7;
    margin: 0;
}

/* ── NAV section label ── */
.nav-section-label {
    font-size: 10px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.14em;
    padding: 0 4px;
    margin: 4px 0 8px 0;
}

/* ── Radio nav: ซ่อน dot ── */
[data-testid="stSidebar"] .stRadio > div { gap: 3px !important; }
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] { display: none !important; }
[data-testid="stSidebar"] .stRadio input[type="radio"] { display: none !important; }
[data-testid="stSidebar"] .stRadio div[role="radio"] { display: none !important; }
[data-testid="stSidebar"] .st-bo,
[data-testid="stSidebar"] .st-bp,
[data-testid="stSidebar"] .st-bq { display: none !important; }

/* label = nav item */
[data-testid="stSidebar"] .stRadio label {
    display: flex !important;
    align-items: center !important;
    padding: 10px 14px !important;
    border-radius: 10px !important;
    margin-bottom: 3px !important;
    border: 1px solid transparent !important;
    cursor: pointer !important;
    transition: all 0.16s ease !important;
    width: 100% !important;
    background: transparent !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(30,111,217,0.1) !important;
    border-color: var(--border) !important;
}
[data-testid="stSidebar"] .stRadio label[data-checked="true"] {
    background: linear-gradient(135deg, #1E6FD9, #1557B0) !important;
    border-color: #3B8FFF !important;
    box-shadow: 0 4px 16px rgba(30,111,217,0.3) !important;
}
[data-testid="stSidebar"] .stRadio label p {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    margin: 0 !important;
}
[data-testid="stSidebar"] .stRadio label:hover p {
    color: var(--text-primary) !important;
}
[data-testid="stSidebar"] .stRadio label[data-checked="true"] p {
    color: #ffffff !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stRadio > label { display: none !important; }

/* ── ปุ่ม Login / Logout ── */
[data-testid="stSidebar"] .stButton > button {
    color: #fff !important;
    background: linear-gradient(135deg, var(--blue), #1557B0) !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Noto Sans Thai', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 10px 18px !important;
    box-shadow: var(--shadow-blue) !important;
    transition: all 0.18s ease !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(30,111,217,0.45) !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# หน้าที่ 1: แจ้งซ่อม (User)
# ==========================================
if page == "📝 แจ้งซ่อม (User)":
    st.header("ระบบแจ้งซ่อมและติดตามงานออนไลน์")
    tab1, tab2 = st.tabs(["🆕 ส่งใบแจ้งซ่อม", "⭐ ประเมินความพึงพอใจ"])
    
    with tab1:
        with st.form("ticket_form"):
            c1, c2 = st.columns(2)
            with c1:
                user_name = st.text_input("ชื่อผู้แจ้ง")
                dept_choice = st.selectbox("แผนก", depts)
                if dept_choice == "Other":
                    department = st.text_input("กรุณาระบุแผนกของคุณ")
                else:
                    department = dept_choice
                
                category = st.selectbox("ประเภทงานซ่อม (Category)", ["Hardware", "Software", "Network", "Other"])
                eq_type = st.selectbox("ประเภทอุปกรณ์ (Equipment Type)", [
                    "Computer PC", "Notebook", "TEC Printer", "Laser Printer", 
                    "IPDS Printer", "TV", "CCTV", "IPad", "Other"
                ])
            with c2:
                asset_id_input = st.text_input("รหัสอุปกรณ์ (Asset ID)") 
                loc_input = st.text_input("สถานที่ตั้งอุปกรณ์ (เช่น KD2 / เสา 4B / Mini office QC)") 
                urgency = st.selectbox("ระดับความเร่งด่วน", ["ปกติ", "ด่วน", "ด่วนมาก"])
                uploaded_file = st.file_uploader("แนบรูปภาพประกอบ", type=['png', 'jpg', 'jpeg'])
            
            description = st.text_area("รายละเอียดปัญหา")
            submitted = st.form_submit_button("ส่งเรื่องแจ้งซ่อม")
            
            if submitted:
                # =========================================================
                # แก้ไขข้อ 2: สร้าง Ticket ID ด้วย UUID แทนการนับ len()
                # ป้องกัน Race Condition กรณีมีผู้ใช้หลายคน Submit พร้อมกัน
                # รูปแบบ: JOB-XXXXXXXX (8 ตัวอักขระแรกของ UUID)
                # =========================================================
                ticket_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
                
                image_data = ""
                if uploaded_file:
                    encoded_img = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                    image_data = f"data:{uploaded_file.type};base64,{encoded_img}"

                # =========================================================
                # แก้ไขข้อ 2 (เพิ่มเติม): Validate กรณีเลือก "Other" แผนก
                # ถ้าไม่กรอกชื่อแผนกจะแจ้งเตือนแทนที่จะบันทึก "Other" เฉย ๆ
                # =========================================================
                if dept_choice == "Other" and not department.strip():
                    st.error("❌ กรุณาระบุชื่อแผนกของคุณในช่อง 'กรุณาระบุแผนกของคุณ'")
                elif user_name and description and department.strip():
                    insert_data("tickets", {
                        "id": ticket_id, 
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"), 
                        "user": user_name, 
                        "dept": department.strip(), 
                        "category": category, 
                        "equipment_type": eq_type,
                        "desc": description, 
                        "status": "รอตรวจสอบ", 
                        "urgency": urgency, 
                        "image_path": image_data, 
                        "asset_id": asset_id_input,
                        "location": loc_input
                    })
                    st.toast('ส่งเรื่องแจ้งซ่อมเรียบร้อยแล้ว!', icon='✅')
                    st.success(f"🎉 บันทึกข้อมูลสำเร็จ! หมายเลขอ้างอิง: **{ticket_id}**")
                else: 
                    st.error("❌ กรุณาระบุชื่อผู้แจ้ง, แผนก และรายละเอียดปัญหา")

        st.divider()
        st.subheader("📋 ตรวจสอบสถานะงานซ่อม")
        df_tickets = load_table("tickets")
        if not df_tickets.empty:
            df_view = df_tickets[['id', 'date', 'user', 'category', 'urgency', 'status', 'rating']].copy()
            sort_map = {'รอตรวจสอบ': 1, 'ดำเนินการ': 2, 'ส่งซ่อม': 3, 'สำเร็จ': 4}
            df_view['sort'] = df_view['status'].map(sort_map)
            df_view = df_view.sort_values(by=['sort', 'date'], ascending=[True, False]).drop('sort', axis=1)
            df_view.rename(columns={'id':'รหัสงาน', 'date':'วันที่แจ้ง', 'user':'ผู้แจ้ง', 'category':'ประเภท', 'urgency':'ความเร่งด่วน', 'status':'สถานะ', 'rating':'คะแนนเฉลี่ย'}, inplace=True)
            df_view['คะแนนเฉลี่ย'] = df_view['คะแนนเฉลี่ย'].apply(lambda x: "⭐" * int(round(float(x))) if pd.notna(x) else "รอประเมิน")
            def color_status(val):
                if val == 'รอตรวจสอบ': return 'background-color: #ffebee; color: #c62828'
                elif val == 'ดำเนินการ': return 'background-color: #fff8e1; color: #f57f17'
                elif val == 'สำเร็จ': return 'background-color: #e8f5e9; color: #2e7d32'
                return ''
            st.dataframe(df_view.style.map(color_status, subset=['สถานะ']), use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("งานซ่อมที่รอการประเมิน")
        df_all = load_table("tickets")
        if not df_all.empty:
            ready_to_rate = df_all[(df_all['status'] == 'สำเร็จ') & (df_all['q1'].isna())]
            if not ready_to_rate.empty:
                selected_job = st.selectbox("เลือกงานซ่อมที่คุณต้องการประเมิน", ready_to_rate['id'].tolist())
                with st.form("detailed_csat_form"):
                    q1 = st.radio("1. ความพอใจการสนับสนุนจากทีมงาน?", scale_options, horizontal=True)
                    q2 = st.radio("2. คุณภาพการบริการ HW/SW?", scale_options, horizontal=True)
                    q3 = st.radio("3. ความมืออาชีพของทีมงาน?", scale_options, horizontal=True)
                    q4 = st.radio("4. การบริการที่ตรงต่อเวลา?", scale_options, horizontal=True)
                    q5 = st.radio("5. ความพึงพอใจในภาพรวม?", scale_options, horizontal=True)
                    fback = st.text_area("ข้อเสนอแนะเพิ่มเติม")
                    if st.form_submit_button("บันทึกการประเมิน"):
                        update_csat_full(selected_job, rating_scale[q1], rating_scale[q2], rating_scale[q3], rating_scale[q4], rating_scale[q5], fback)
                        st.success("ขอบคุณสำหรับคะแนนครับ!")
                        st.rerun()
            else: st.info("ไม่มีงานซ่อมที่รอการประเมิน")

# ==========================================
# หน้าที่ 2: จัดการงานซ่อม (ช่าง)
# ==========================================
elif page == "💻 จัดการงานซ่อม (ช่าง)" and st.session_state.is_admin:
    st.header("💻 จัดการงานซ่อม (เฉพาะงานที่รอดำเนินการ)")
    df_tickets = load_table("tickets")
    
    if not df_tickets.empty:
        df_pending = df_tickets[df_tickets['status'] != 'สำเร็จ'].copy()
        
        if not df_pending.empty:
            view_cols = ['id', 'date', 'user', 'dept', 'category', 'status']
            rename_dict = {'id': 'รหัสงาน', 'date': 'วันที่แจ้ง', 'user': 'ผู้แจ้ง', 'dept': 'แผนก', 'category': 'ประเภท', 'status': 'สถานะ'}
            
            if 'location' in df_pending.columns:
                view_cols.insert(4, 'location')
                rename_dict['location'] = 'สถานที่ตั้ง'
            
            df_manage_view = df_pending[view_cols].copy()
            df_manage_view.rename(columns=rename_dict, inplace=True)

            def color_status(val):
                if val == 'รอตรวจสอบ': return 'background-color: #ffebee; color: #c62828; font-weight: bold'
                elif val == 'ดำเนินการ': return 'background-color: #fff8e1; color: #f57f17; font-weight: bold'
                elif val == 'ส่งซ่อม': return 'background-color: #f3e5f5; color: #6a1b9a; font-weight: bold'
                return ''

            st.dataframe(df_manage_view.style.map(color_status, subset=['สถานะ']), use_container_width=True, hide_index=True)
            
            st.divider()
            
            st.subheader("🔧 อัปเดตรายละเอียดและปิดงาน")
            selected_id = st.selectbox("เลือกรหัสงานที่ต้องการจัดการ", df_pending['id'].tolist())
            tk = df_pending[df_pending['id'] == selected_id].iloc[0]
            
            # =========================================================
            # แก้ไขข้อ 4: ดึงรูปภาพเพียงครั้งเดียว แล้วเก็บใน img_path
            # ใช้ตัวแปรเดียวกันทั้งสำหรับปุ่มดาวน์โหลด PDF และแสดงในฟอร์ม
            # (เดิมดึง 2 ครั้ง: ก่อนฟอร์ม 1 รอบ และในฟอร์มอีก 1 รอบ)
            # =========================================================
            try:
                img_res = supabase.table("tickets").select("image_path").eq("id", selected_id).execute()
                img_path = img_res.data[0].get('image_path', '') if img_res.data else ''
            except Exception:
                img_path = ''

            # ปุ่มดาวน์โหลด PDF — ใช้ img_path ที่ดึงมาแล้วด้านบน
            pdf_bytes = generate_repair_pdf(tk, img_path)
            st.download_button(
                label="📥 ดาวน์โหลดใบงานซ่อม (PDF)",
                data=pdf_bytes,
                file_name=f"Service_Report_{selected_id}.pdf",
                mime="application/pdf"
            )
            
            with st.form("edit_job_form"):
                c1, c2 = st.columns(2)
                
                with c1:
                    st.info(f"**📍 สถานที่ตั้ง:** {tk.get('location', 'ไม่ได้ระบุ')}")
                    st.info(f"**อาการที่แจ้ง:** {tk.get('desc', '')}")
                    st.info(f"**ประเภทอุปกรณ์:** {tk.get('equipment_type', 'ไม่ได้ระบุ')}")
                    st.info(f"**ประเภทงาน:** {tk.get('category', '')}")
                    
                    # แสดงรูปภาพจาก img_path ที่ดึงมาแล้วครั้งเดียว (ไม่ดึงซ้ำ)
                    if img_path and str(img_path).startswith('data:image'):
                        try: st.image(img_path, caption="รูปประกอบ", width=400)
                        except: st.error("ไม่สามารถแสดงรูปภาพได้")
                    
                    n_status = st.selectbox("สถานะปัจจุบัน", ticket_statuses, index=ticket_statuses.index(tk['status']))
                    assignee = st.text_input("ช่างผู้รับผิดชอบ", value=tk.get('assignee') or "")
                
                with c2:
                    root = st.text_area("สาเหตุของปัญหา", value=tk.get('root_cause') or "")
                    sol = st.text_area("วิธีการแก้ไข", value=tk.get('solution') or "")
                    cost = st.number_input("ค่าใช้จ่าย (บาท)", value=float(tk.get('cost') or 0.0))
                
                submitted = st.form_submit_button("บันทึกข้อมูลงานซ่อม")
                if submitted:
                    update_ticket_full(selected_id, n_status, assignee, root, sol, cost)
                    st.toast(f"บันทึกงาน {selected_id} สำเร็จ!", icon="✅")
                    st.success("อัปเดตสถานะเรียบร้อยแล้ว")
                    st.rerun()
        else:
            st.success("🎉 ยอดเยี่ยม! ขณะนี้ไม่มีงานซ่อมค้างในระบบ")
    else:
        st.info("ยังไม่มีข้อมูลงานซ่อมในระบบ")

# ==========================================
# หน้าที่ 3: Dashboard
# ==========================================
elif page == "📊 Dashboard" and st.session_state.is_admin:
    st.title("📈 IT Performance Overview")
    df = load_table("tickets")
    
    if not df.empty:
        df['date_dt'] = pd.to_datetime(df['date'])
        df['month_year'] = df['date_dt'].dt.strftime('%m-%Y')
        selected_month = st.selectbox("📅 เลือกเดือนที่ต้องการดู", ["ทั้งหมด"] + sorted(df['month_year'].unique(), reverse=True))
        
        if selected_month != "ทั้งหมด":
            df_filtered = df[df['month_year'] == selected_month].copy()
            st.info(f"🔎 แสดงข้อมูลเฉพาะเดือน: **{selected_month}**")
        else:
            df_filtered = df.copy()
            st.info("🔎 แสดงข้อมูลภาพรวมทั้งหมด")
        
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("งานแจ้งซ่อม", len(df_filtered))
        with m2:
            resolved = len(df_filtered[df_filtered['status'] == 'สำเร็จ'])
            success_rate = (resolved/len(df_filtered)*100) if len(df_filtered) > 0 else 0
            st.metric("ปิดงานสำเร็จ", f"{resolved} งาน", f"{success_rate:.1f}%")
        with m3:
            avg_csat = df_filtered['rating'].mean()
            st.metric("คะแนนเฉลี่ย", f"{avg_csat:.2f} ⭐" if not pd.isna(avg_csat) else "0.00 ⭐")
        with m4:
            pending = len(df_filtered[df_filtered['status'] == 'รอตรวจสอบ'])
            st.metric("งานค้าง", pending, delta=f"{pending} งาน", delta_color="inverse")

        st.markdown("---")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🏢 ปริมาณงานแยกตามแผนก")
            if not df_filtered.empty: st.bar_chart(df_filtered['dept'].value_counts(), color="#0046ad")
        with c2:
            st.subheader("🛠️ ประเภทปัญหาที่พบบ่อย")
            if not df_filtered.empty: st.bar_chart(df_filtered['category'].value_counts(), color="#ff4b4b")

        st.divider()

        with st.expander("📊 รายละเอียดคะแนนประเมิน (CSAT)", expanded=True):
            def to_percent(val):
                return f"{(val / 5 * 100):.1f}%" if pd.notna(val) else "0.0%"
            
            csat_stats = pd.DataFrame({
                "หัวข้อการประเมิน": [
                    "1. การสนับสนุนจากทีมงาน", 
                    "2. คุณภาพการบริการ HW/SW", 
                    "3. ความเป็นมืออาชีพ", 
                    "4. ความตรงต่อเวลา", 
                    "5. ความพึงพอใจในภาพรวม"
                ],
                "คะแนนความพึงพอใจ (%)": [
                    to_percent(df_filtered['q1'].mean()), 
                    to_percent(df_filtered['q2'].mean()), 
                    to_percent(df_filtered['q3'].mean()), 
                    to_percent(df_filtered['q4'].mean()), 
                    to_percent(df_filtered['q5'].mean())
                ]
            })
            csat_stats.set_index("หัวข้อการประเมิน", inplace=True)
            st.table(csat_stats)

        st.subheader("💬 ข้อเสนอแนะล่าสุด")
        if 'feedback' in df_filtered.columns:
            feedback_list = df_filtered[(df_filtered['feedback'].notna()) & (df_filtered['feedback'].str.strip() != "")][['date', 'user', 'rating', 'feedback']].sort_values(by='date', ascending=False)
            if not feedback_list.empty:
                feedback_list.rename(columns={'date': 'วันที่', 'user': 'ผู้แจ้ง', 'rating': 'คะแนน', 'feedback': 'ความคิดเห็น'}, inplace=True)
                st.dataframe(feedback_list, use_container_width=True, hide_index=True)
            else: st.write("ไม่มีข้อเสนอแนะเพิ่มเติม")
            
        st.divider()
        st.subheader("🔧 สรุปผลการบำรุงรักษา (PM Coverage)")
        df_pm_all = load_table("pm_schedules")
        
        if not df_pm_all.empty:
            df_pm_all['date_dt'] = pd.to_datetime(df_pm_all['next_due_date'])
            df_pm_all['month_year'] = df_pm_all['date_dt'].dt.strftime('%m-%Y')
            
            pm_filtered = df_pm_all[df_pm_all['month_year'] == selected_month] if selected_month != "ทั้งหมด" else df_pm_all
            
            if not pm_filtered.empty:
                total_pm = len(pm_filtered)
                done_pm = len(pm_filtered[pm_filtered['status'] == 'Completed'])
                pending_pm = total_pm - done_pm
                
                p_done = (done_pm / total_pm) * 100 if total_pm > 0 else 0
                p_pending = (pending_pm / total_pm) * 100 if total_pm > 0 else 0
                
                cp1, cp2, cp3 = st.columns(3)
                cp1.metric("แผน PM ทั้งหมด", f"{total_pm} รายการ")
                cp2.metric("ดำเนินการแล้ว (%)", f"{p_done:.1f}%", delta=f"{done_pm} งาน")
                cp3.metric("รอดำเนินการ (%)", f"{p_pending:.1f}%", delta=f"-{pending_pm} งาน", delta_color="inverse")
                
                pm_chart_data = pd.DataFrame({
                    'สถานะ': ['เสร็จสิ้น', 'ค้างดำเนินการ'],
                    'จำนวน': [done_pm, pending_pm]
                })
                st.bar_chart(pm_chart_data.set_index('สถานะ'))
            else:
                st.write("ไม่มีแผนงาน PM ในเดือนนี้")
        else:
            st.info("ยังไม่มีการสร้างแผนงานบำรุงรักษา (PM) ในระบบ")

    else:
        st.warning("⚠️ ยังไม่มีข้อมูลงานแจ้งซ่อมในฐานข้อมูล")

# ==========================================
# หน้าที่ 4: Assets
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
                    insert_data("assets", {
                        "id": aid, "model": amod, "dept": adept, 
                        "warranty_expire": str(awarranty), 
                        "location": aloc, "assigned_user": auser, 
                        "status": "Active"
                    })
                    st.success(f"ลงทะเบียน {aid} สำเร็จ"); st.rerun()
                else: st.error("กรุณาระบุรหัสอุปกรณ์")

    df_a = load_table("assets")
    df_t = load_table("tickets")
    st.divider()
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
                    w_status = "🔴 **หมดอายุการรับประกัน**"
                else:
                    days_left = (w_date - today).days
                    w_status = f"🟢 **อยู่ในประกัน** (เหลือ {days_left} วัน)"
            else:
                w_status = "⚪ ไม่ระบุข้อมูลประกัน"
                w_date = "N/A"

            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid {('#d32f2f' if 'หมดอายุ' in w_status else '#2e7d32')};">
                <h4 style="margin-top:0;">ข้อมูลอุปกรณ์: {target_asset['id']}</h4>
                <p><b>รุ่น:</b> {target_asset.get('model', 'N/A')} | <b>แผนก:</b> {target_asset.get('dept', 'N/A')}</p>
                <p><b>สถานที่ตั้ง:</b> {target_asset.get('location', 'N/A')} | <b>ผู้รับผิดชอบ:</b> {target_asset.get('assigned_user', 'N/A')}</p>
                <p style="font-size: 1.1em;">สถานะประกัน: {w_status}</p>
                <p>วันที่หมดประกัน: 📅 {w_date}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("---")
            st.write("### 🛠️ ประวัติการซ่อมและบำรุงรักษา (PM)")
            
            tab_repair, tab_pm_hist = st.tabs(["🔧 ประวัติการแจ้งซ่อม", "📅 ประวัติการทำ PM"])
            
            with tab_repair:
                if 'asset_id' in df_t.columns:
                    history = df_t[df_t['asset_id'] == target_asset['id']]
                    if not history.empty:
                        total_cost = pd.to_numeric(history['cost'], errors='coerce').sum()
                        st.metric("💸 ยอดค่าซ่อมสะสม", f"฿{total_cost:,.2f}")
                        h_view = history[['date', 'user', 'root_cause', 'solution', 'cost', 'status']].copy()
                        h_view.columns = ['วันที่', 'ผู้แจ้ง', 'สาเหตุ', 'วิธีแก้', 'ค่าใช้จ่าย', 'สถานะ']
                        st.dataframe(h_view, use_container_width=True, hide_index=True)
                    else: st.info("✨ อุปกรณ์นี้ยังไม่มีประวัติการซ่อม")
                else: st.warning("⚠️ ไม่พบคอลัมน์ 'asset_id' ในฐานข้อมูล")

            with tab_pm_hist:
                df_pm_hist = load_table("pm_schedules")
                if not df_pm_hist.empty and 'asset_id' in df_pm_hist.columns:
                    asset_pm_hist = df_pm_hist[df_pm_hist['asset_id'] == target_asset['id']]
                    if not asset_pm_hist.empty:
                        pm_view = asset_pm_hist[['next_due_date', 'task_name', 'assignee', 'status', 'pm_result']].copy()
                        pm_view.columns = ['วันที่กำหนดทำ', 'ชื่องาน', 'ผู้รับผิดชอบ', 'สถานะ', 'ผลการตรวจสอบ']
                        st.dataframe(pm_view, use_container_width=True, hide_index=True)
                    else: st.info("ยังไม่มีประวัติการทำ PM สำหรับอุปกรณ์นี้")
                else: st.info("ยังไม่มีประวัติการทำ PM สำหรับอุปกรณ์นี้")
        else: st.error("❌ ไม่พบรหัสอุปกรณ์")

# ==========================================
# หน้าที่ 5: แผนบำรุงรักษา (PM)
# ==========================================
elif page == "🔧 แผนบำรุงรักษา (PM)" and st.session_state.is_admin:
    st.title("🔧 IT Preventive Maintenance System")
    tab_cal, tab_list, tab_add = st.tabs(["📅 ปฏิทินงาน PM", "📋 รายการและบันทึกผล", "➕ ลงทะเบียนแผนใหม่"])
    
    df_pm = load_table("pm_schedules")

    with tab_cal:
        st.subheader("📅 ตารางงานบำรุงรักษาประจำเดือน")
        if not df_pm.empty:
            calendar_events = []
            for _, row in df_pm.iterrows():
                try:
                    due_date = pd.to_datetime(row['next_due_date']).strftime('%Y-%m-%d')
                    calendar_events.append({
                        "id": str(row['id']),
                        "title": f"🛠️ {row['task_name']}",
                        "start": due_date, "end": due_date,
                        "color": "#2e7d32" if row['status'] == "Completed" else "#0046ad",
                        "allDay": True
                    })
                except Exception: continue

            calendar_options = {
                "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,dayGridWeek"},
                "initialView": "dayGridMonth", "selectable": True,
            }
            
            cal_action = calendar(events=calendar_events, options=calendar_options, key=f"pm_calendar_{len(calendar_events)}")
            
            if cal_action and "callback" in cal_action and cal_action["callback"] == "eventClick":
                event_id = cal_action["eventClick"]["event"]["id"]
                clicked_event = df_pm[df_pm['id'] == event_id]
                
                if not clicked_event.empty:
                    target = clicked_event.iloc[0]
                    st.markdown("---")
                    st.markdown(f"### 📌 รายละเอียดงาน: {target['task_name']}")
                    ci1, ci2 = st.columns(2)
                    with ci1:
                        st.write(f"**รหัสอุปกรณ์:** {target.get('asset_id', 'N/A')}")
                        st.write(f"**วันที่กำหนด:** {target['next_due_date']}")
                    with ci2:
                        st.write(f"**ผู้รับผิดชอบ:** {target.get('assignee', 'N/A')}")
                        st.write(f"**สถานะ:** {'🟢 เสร็จสิ้น' if target['status'] == 'Completed' else '🟡 รอทำ'}")
                    st.info(f"**📝 Checklist:**\n\n{target.get('checklist', 'ไม่มีข้อมูล')}")
                    if target['status'] == "Completed" and pd.notna(target.get('pm_result')):
                        st.success(f"**✅ ผลตรวจสอบ:**\n\n{target['pm_result']}")
        else:
            st.info("💡 ยังไม่มีข้อมูลแผนงาน PM")

    with tab_list:
        if not df_pm.empty:
            st.dataframe(df_pm[['id', 'task_name', 'next_due_date', 'assignee', 'status']], use_container_width=True, hide_index=True)
            pending = df_pm[df_pm['status'] != 'Completed']
            
            if not pending.empty:
                st.divider()
                st.subheader("📝 บันทึกผลการตรวจเช็ค")
                sel = st.selectbox("เลือกงาน PM เพื่อบันทึกผล", pending['id'].tolist())
                target_pm = pending[pending['id'] == sel].iloc[0]
                
                with st.expander(f"📌 รายการ Checklist สำหรับ: {target_pm['task_name']}", expanded=True):
                    st.info(f"**สิ่งที่ต้องตรวจสอบ:**\n\n{target_pm.get('checklist', 'ไม่มีข้อมูล Checklist')}")
                
                with st.form("pm_finish_form"):
                    res = st.text_area("บันทึกผลการตรวจสอบ / ปัญหาที่พบ")
                    if st.form_submit_button("✅ บันทึกและปิดงาน PM"):
                        update_pm_full(sel, "Completed", res)
                        st.success(f"บันทึกผลงาน {sel} เรียบร้อยแล้ว"); st.rerun()
            else:
                st.success("🎉 ทุกแผนงานดำเนินการเสร็จสิ้นแล้ว!")

    with tab_add:
        st.subheader("➕ เพิ่มแผนบำรุงรักษาและจัดตารางอัตโนมัติ")
        with st.form("pm_auto_form"):
            asset_id_pm = st.text_input("รหัสอุปกรณ์ (Asset ID)*", placeholder="เช่น CCTV-001")
            
            eq_type = st.selectbox("ประเภทอุปกรณ์", [
                "Computer PC", "Notebook", "TEC Printer", "Laser Printer", 
                "IPDS Printer", "TV", "CCTV", "Server room", "Other"
            ])

            c1, c2 = st.columns(2)
            with c1:
                s_date = st.date_input("เริ่มตั้งแต่วันที่")
                freq = st.selectbox("ความถี่", ["รายวัน", "รายสัปดาห์", "รายเดือน", "รายปี"])
            with c2:
                assign = st.text_input("ช่างผู้รับผิดชอบ")
                count = st.number_input("จำนวนครั้งที่ต้องการวางแผนล่วงหน้า", min_value=1, value=12)
            
            check = st.text_area("รายการ Checklist")
            
            if st.form_submit_button("📅 บันทึกและจัดตารางลงปฏิทิน"):
                if asset_id_pm and assign and check:
                    curr_date = s_date
                    current_year = datetime.now().year
                    
                    for i in range(count):
                        # =========================================================
                        # แก้ไขข้อ 2 (PM ID): เพิ่ม UUID suffix ป้องกัน ID ซ้ำ
                        # กรณีสร้างแผนเดิมซ้ำในปีเดียวกัน
                        # =========================================================
                        unique_suffix = uuid.uuid4().hex[:6].upper()
                        unique_id = f"PM-{asset_id_pm}-{eq_type}({i+1}/{count}){current_year}-{unique_suffix}"
                        
                        insert_data("pm_schedules", {
                            "id": unique_id, 
                            "task_name": f"PM {eq_type}: {asset_id_pm} ({i+1}/{count})", 
                            "next_due_date": str(curr_date), 
                            "status": "Scheduled", 
                            "assignee": assign, 
                            "checklist": check, 
                            "frequency": freq,
                            "asset_id": asset_id_pm,
                            "equipment_type": eq_type
                        })
                        
                        if freq == "รายวัน": curr_date += relativedelta(days=1)
                        elif freq == "รายสัปดาห์": curr_date += relativedelta(weeks=1)
                        elif freq == "รายเดือน": curr_date += relativedelta(months=1)
                        elif freq == "รายปี": curr_date += relativedelta(years=1)
                    
                    st.success(f"✅ สร้างแผนงานสำเร็จ! จำนวน {count} รายการสำหรับ {asset_id_pm}")
                    st.rerun()
                else:
                    st.error("❌ กรุณากรอกข้อมูลให้ครบถ้วน (Asset ID, ผู้รับผิดชอบ, Checklist)")
