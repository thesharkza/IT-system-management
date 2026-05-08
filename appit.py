import streamlit as st
import pandas as pd
import base64
from datetime import datetime
from supabase import create_client, Client
from streamlit_calendar import calendar
from dateutil.relativedelta import relativedelta

# --- CUSTOM UI STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500&display=swap');
    html, body, [class*="css"]  { font-family: 'Prompt', sans-serif; }

    /* จัดตารางให้อยู่ตรงกลางเสมอ */
    .stTable td, .stTable th {
        text-align: center !important;
    }
    
    /* ส่วน Sidebar Menu (ที่แก้ไขไปก่อนหน้า) */
    div[data-testid="stSidebar"] .st-bo { display: none !important; }
    div[data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 15px 20px !important;
        border-radius: 12px !important;
        margin-bottom: 8px !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label p { font-size: 20px !important; font-weight: 500 !important; }
    div[data-testid="stSidebar"] div[role="radiogroup"] [data-checked="true"] { background-color: #0046ad !important; }
    div[data-testid="stSidebar"] div[role="radiogroup"] [data-checked="true"] p { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

st.set_page_config(page_title="Enterprise CMMS & CSAT", layout="wide", initial_sidebar_state="expanded")

# --- DATABASE SETUP ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- HELPER FUNCTIONS ---
def load_table(table_name):
    response = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

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

st.sidebar.title("🔐 IT Authorization")
if not st.session_state.is_admin:
    admin_pass = st.sidebar.text_input("Admin Password", type="password")
    if st.sidebar.button("Login"):
        if admin_pass == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.rerun()
        else: st.sidebar.error("รหัสผ่านไม่ถูกต้อง")
else:
    st.sidebar.success("IT Admin Mode Active")
    if st.sidebar.button("Logout"):
        st.session_state.is_admin = False
        st.rerun()

st.sidebar.divider()
st.sidebar.title("🛠️ Menu")
menu_options = ["📝 แจ้งซ่อม (User)", "💻 จัดการงานซ่อม (ช่าง)", "📊 Dashboard", "🗄️ ทะเบียนอุปกรณ์", "🔧 แผนบำรุงรักษา (PM)"] if st.session_state.is_admin else ["📝 แจ้งซ่อม (User)"]
page = st.sidebar.radio("ไปที่หน้า", menu_options)

# ==========================================
# หน้าที่ 1: แจ้งซ่อม (User) - เพิ่มช่องประเภทอุปกรณ์
# ==========================================
if page == "📝 แจ้งซ่อม (User)":
    st.header("ระบบแจ้งซ่อมและติดตามงานออนไลน์")
    tab1, tab2 = st.tabs(["🆕 ส่งใบแจ้งซ่อม", "⭐ ประเมินความพึงพอใจ"])
    
    with tab1:
        with st.form("ticket_form"):
            c1, c2 = st.columns(2)
            with c1:
                user_name = st.text_input("ชื่อผู้แจ้ง")
                
                # ส่วนที่แก้ไข: การเลือกแผนกแบบมีช่องกรอกเพิ่ม
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
                # ... (รหัสอุปกรณ์, ความเร่งด่วน, อัปโหลดรูป เหมือนเดิม) ...
                asset_id_input = st.text_input("รหัสอุปกรณ์ (Asset ID)") 
                urgency = st.selectbox("ระดับความเร่งด่วน", ["ปกติ", "ด่วน", "ด่วนมาก"])
                uploaded_file = st.file_uploader("แนบรูปภาพประกอบ", type=['png', 'jpg', 'jpeg'])
            
            description = st.text_area("รายละเอียดปัญหา")
            submitted = st.form_submit_button("ส่งเรื่องแจ้งซ่อม")
            
            if submitted:
                # สร้าง ticket_id
                df_existing = load_table("tickets")
                ticket_id = f"JOB-{len(df_existing) + 1:04d}"
                
                # จัดการรูปภาพ
                image_data = ""
                if uploaded_file:
                    encoded_img = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                    image_data = f"data:{uploaded_file.type};base64,{encoded_img}"

                final_dept = department if department else "Other"
                
                if user_name and description and final_dept:
                    # บันทึกเพียงครั้งเดียว
                    insert_data("tickets", {
                        "id": ticket_id, 
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"), 
                        "user": user_name, 
                        "dept": final_dept, 
                        "category": category, 
                        "equipment_type": eq_type,
                        "desc": description, 
                        "status": "รอตรวจสอบ", 
                        "urgency": urgency, 
                        "image_path": image_data, 
                        "asset_id": asset_id_input 
                    })
                    st.toast('ส่งเรื่องแจ้งซ่อมเรียบร้อยแล้ว!', icon='✅')
                    st.success(f"🎉 บันทึกข้อมูลสำเร็จ! หมายเลขอ้างอิง: **{ticket_id}**")
                else: 
                    st.error("❌ กรุณาระบุชื่อผู้แจ้งและรายละเอียดปัญหา")

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
# หน้าที่ 2: จัดการงานซ่อม (ช่าง) - ปรับปรุงให้โชว์เฉพาะงานไม่เสร็จ
# ==========================================
elif page == "💻 จัดการงานซ่อม (ช่าง)" and st.session_state.is_admin:
    st.header("💻 จัดการงานซ่อม (เฉพาะงานที่รอดำเนินการ)")
    df_tickets = load_table("tickets")
    
    if not df_tickets.empty:
        # --- จุดสำคัญ: กรองเฉพาะงานที่ยังไม่สำเร็จ ---
        df_pending = df_tickets[df_tickets['status'] != 'สำเร็จ'].copy()
        
        if not df_pending.empty:
            # 1. เตรียมตารางสำหรับแสดงผลเฉพาะงานที่ยังไม่เสร็จ
            df_manage_view = df_pending[['id', 'date', 'user', 'dept', 'category', 'urgency', 'status']].copy()
            
            # เรียงลำดับงานตามความเร่งด่วน/วันที่
            df_manage_view.rename(columns={
                'id': 'รหัสงาน', 'date': 'วันที่แจ้ง', 'user': 'ผู้แจ้ง',
                'dept': 'แผนก', 'category': 'ประเภท', 'urgency': 'ความเร่งด่วน', 'status': 'สถานะ'
            }, inplace=True)

            # ฟังก์ชันลงสีสถานะ (คงเดิมตาม UX ที่ตั้งไว้)
            def color_status(val):
                if val == 'รอตรวจสอบ': return 'background-color: #ffebee; color: #c62828; font-weight: bold'
                elif val == 'ดำเนินการ': return 'background-color: #fff8e1; color: #f57f17; font-weight: bold'
                elif val == 'ส่งซ่อม': return 'background-color: #f3e5f5; color: #6a1b9a; font-weight: bold'
                return ''

            st.dataframe(df_manage_view.style.map(color_status, subset=['สถานะ']), use_container_width=True, hide_index=True)
            
            st.divider()
            
            # 2. ส่วนฟอร์มแก้ไข (ตัวเลือกใน selectbox จะมีเฉพาะงานที่ยังไม่เสร็จ)
            st.subheader("🔧 อัปเดตรายละเอียดและปิดงาน")
            selected_id = st.selectbox("เลือกรหัสงานที่ต้องการจัดการ", df_pending['id'].tolist())
            tk = df_pending[df_pending['id'] == selected_id].iloc[0]
            
            with st.form("edit_job_form"):
                c1, c2 = st.columns(2)
                with c1:
                    st.info(f"**อาการที่แจ้ง:** {tk['desc']}")
                    st.info(f"**ประเภทอุปกรณ์:** {tk.get('equipment_type', 'ไม่ได้ระบุ')}")
                    st.info(f"**ประเภทงาน:** {tk['category']}")
                    img_path = tk.get('image_path', '')
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
            # กรณีไม่มีงานค้างเลย
            st.success("🎉 ยอดเยี่ยม! ขณะนี้ไม่มีงานซ่อมค้างในระบบ")
    else:
        st.info("ยังไม่มีข้อมูลงานซ่อมในระบบ")

# ==========================================
# หน้าที่ 3: Dashboard (คะแนนเป็น % และกรองข้อเสนอแนะ)
# ==========================================
elif page == "📊 Dashboard" and st.session_state.is_admin:
    st.title("📈 IT Performance Overview")
    df = load_table("tickets")
    
    if not df.empty:
        df['date_dt'] = pd.to_datetime(df['date'])
        df['month_year'] = df['date_dt'].dt.strftime('%m-%Y')
        selected_month = st.selectbox("📅 เลือกเดือนที่ต้องการดู", ["ทั้งหมด"] + sorted(df['month_year'].unique(), reverse=True))
        df_filtered = df[df['month_year'] == selected_month] if selected_month != "ทั้งหมด" else df
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("งานแจ้งซ่อม", len(df_filtered))
        resolved = len(df_filtered[df_filtered['status'] == 'สำเร็จ'])
        m2.metric("ปิดงานสำเร็จ", f"{resolved} งาน", f"{(resolved/len(df_filtered)*100):.1f}%" if len(df_filtered) > 0 else "0%")
        m3.metric("คะแนนเฉลี่ย", f"{df_filtered['rating'].mean():.2f} ⭐" if not df_filtered['rating'].isna().all() else "0.00 ⭐")
        pending = len(df_filtered[df_filtered['status'] == 'รอตรวจสอบ'])
        m4.metric("งานค้าง", pending, delta=f"{pending} งาน", delta_color="inverse")
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1: 
            st.subheader("🏢 ปริมาณงานตามแผนก")
            st.bar_chart(df_filtered['dept'].value_counts(), color="#0046ad")
        with c2: 
            st.subheader("🛠️ ประเภทปัญหาที่พบ")
            st.bar_chart(df_filtered['category'].value_counts(), color="#ff4b4b")

        st.divider()

        with st.expander("📊 รายละเอียดคะแนนประเมิน (CSAT)", expanded=True):
            def to_percent(val):
                return f"{(val / 5 * 100):.1f}%" if pd.notna(val) else "0.0%"
            csat_stats = pd.DataFrame({
                "หัวข้อการประเมิน": ["1. การสนับสนุนจากทีมงาน", "2. คุณภาพการบริการ HW/SW", "3. ความเป็นมืออาชีพ", "4. ความตรงต่อเวลา", "5. ความพึงพอใจในภาพรวม"],
                "คะแนนความพึงพอใจ (%)": [to_percent(df_filtered['q1'].mean()), to_percent(df_filtered['q2'].mean()), to_percent(df_filtered['q3'].mean()), to_percent(df_filtered['q4'].mean()), to_percent(df_filtered['q5'].mean())]
            })
            st.table(csat_stats)

        st.subheader("💬 ข้อเสนอแนะล่าสุด")
        if 'feedback' in df_filtered.columns:
            feedback_list = df_filtered[(df_filtered['feedback'].notna()) & (df_filtered['feedback'].str.strip() != "")][['date', 'user', 'rating', 'feedback']].sort_values(by='date', ascending=False)
            if not feedback_list.empty:
                feedback_list.rename(columns={'date': 'วันที่', 'user': 'ผู้แจ้ง', 'rating': 'คะแนน', 'feedback': 'ความคิดเห็น'}, inplace=True)
                st.dataframe(feedback_list, use_container_width=True, hide_index=True)
            else: st.write("ไม่มีข้อเสนอแนะเพิ่มเติม")

# ==========================================
# หน้าที่ 4: Assets (ทะเบียนอุปกรณ์ - อัปเดต Location & Assigned User)
# ==========================================
elif page == "🗄️ ทะเบียนอุปกรณ์" and st.session_state.is_admin:
    st.title("🗄️ IT Asset Management")
    
    # --- ส่วนที่ 1: ลงทะเบียน (เพิ่มช่อง Location และ Assigned User) ---
    with st.expander("➕ ลงทะเบียนอุปกรณ์ใหม่"):
        with st.form("new_asset_form"):
            a1, a2 = st.columns(2)
            with a1:
                aid = st.text_input("รหัสอุปกรณ์ (Asset ID)*")
                awarranty = st.date_input("วันที่หมดประกัน")
                aloc = st.text_input("สถานที่ตั้ง (Location)") # เพิ่มใหม่
            with a2:
                amod = st.text_input("ยี่ห้อ/รุ่น")
                adept = st.selectbox("แผนกที่ใช้งาน", depts)
                auser = st.text_input("ผู้ถือครอง/ผู้รับผิดชอบ (Assigned User)") # เพิ่มใหม่
                
            if st.form_submit_button("บันทึกทะเบียน"):
                if aid:
                    insert_data("assets", {
                        "id": aid, 
                        "model": amod, 
                        "dept": adept, 
                        "warranty_expire": str(awarranty), 
                        "location": aloc,          # บันทึกลง DB
                        "assigned_user": auser,    # บันทึกลง DB
                        "status": "Active"
                    })
                    st.success(f"ลงทะเบียน {aid} สำเร็จ")
                    st.rerun()
                else:
                    st.error("กรุณาระบุรหัสอุปกรณ์")

    # --- ส่วนที่ 2: ระบบค้นหา (โชว์ Location และ Assigned User ในการแสดงผล) ---
    df_a = load_table("assets")
    df_t = load_table("tickets")
    st.divider()
    search_query = st.text_input("🔍 ตรวจสอบประวัติเครื่องรายอุปกรณ์", placeholder="พิมพ์ Asset ID...")
    
    if search_query and not df_a.empty:
        match = df_a[df_a['id'].str.contains(search_query, case=False, na=False)]
        if not match.empty:
            target = match.iloc[0]
            today = datetime.now().date()
            w_date_str = target.get('warranty_expire')
            w_date = pd.to_datetime(w_date_str).date() if pd.notna(w_date_str) else None
            
            if w_date:
                w_status = "🔴 **หมดอายุการรับประกัน**" if w_date < today else f"🟢 **อยู่ในประกัน** (เหลือ {(w_date - today).days} วัน)"
            else: 
                w_status = "⚪ ไม่ระบุข้อมูลประกัน"

            # ปรับปรุงการแสดงผล Card ให้มี Location และ Assigned User
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #0046ad;">
                <h4 style="margin-top:0;">ข้อมูลอุปกรณ์: {target['id']}</h4>
                <p><b>รุ่น:</b> {target.get('model', 'N/A')} | <b>แผนก:</b> {target.get('dept', 'N/A')}</p>
                <p><b>สถานที่ตั้ง:</b> {target.get('location', 'N/A')} | <b>ผู้รับผิดชอบ:</b> {target.get('assigned_user', 'N/A')}</p>
                <p style="font-size: 1.1em;">สถานะประกัน: {w_status}</p>
                <p>วันที่หมดประกัน: 📅 {w_date if w_date else 'N/A'}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # แสดงประวัติการซ่อม (คงเดิม)
            if 'asset_id' in df_t.columns:
                hist = df_t[df_t['asset_id'] == target['id']]
                if not hist.empty:
                    st.metric("💸 ยอดค่าซ่อมสะสม", f"฿{pd.to_numeric(hist['cost'], errors='coerce').sum():,.2f}")
                    st.dataframe(hist[['date', 'user', 'root_cause', 'solution', 'cost', 'status']], use_container_width=True, hide_index=True)
                else: 
                    st.info("✨ ยังไม่มีประวัติการซ่อม")
        else: 
            st.error("❌ ไม่พบรหัสอุปกรณ์")

# ==========================================
# หน้าที่ 5: แผนบำรุงรักษา (PM) - ปฏิทินคลิกได้ & แสดง Checklist
# ==========================================
elif page == "🔧 แผนบำรุงรักษา (PM)" and st.session_state.is_admin:
    st.title("🔧 IT Preventive Maintenance System")
    tab_cal, tab_list, tab_add = st.tabs(["📅 ปฏิทินงาน PM", "📋 รายการและบันทึกผล", "➕ ลงทะเบียนแผนใหม่"])
    
    # โหลดข้อมูล PM ล่าสุด
    df_pm = load_table("pm_schedules")

    # --- Tab 1: ปฏิทินงาน PM ---
    with tab_cal:
        st.subheader("📅 ตารางงานบำรุงรักษาประจำเดือน")
        if not df_pm.empty:
            calendar_events = []
            for _, row in df_pm.iterrows():
                # 1. บังคับแปลงวันที่ให้เป็นรูปแบบ YYYY-MM-DD เพื่อป้องกันปฏิทินค้าง
                try:
                    due_date = pd.to_datetime(row['next_due_date']).strftime('%Y-%m-%d')
                    calendar_events.append({
                        "id": str(row['id']),
                        "title": f"🛠️ {row['task_name']}",
                        "start": due_date,
                        "end": due_date,
                        "color": "#2e7d32" if row['status'] == "Completed" else "#0046ad",
                        "allDay": True
                    })
                except Exception:
                    continue # ข้ามแถวที่ข้อมูลวันที่เสีย

            calendar_options = {
                "headerToolbar": {
                    "left": "prev,next today",
                    "center": "title",
                    "right": "dayGridMonth,dayGridWeek"
                },
                "initialView": "dayGridMonth",
                "selectable": True,
            }
            
            # 2. แสดงผลปฏิทินและรับค่าการคลิกมาเก็บในตัวแปร cal_action
            cal_action = calendar(
                events=calendar_events,
                options=calendar_options,
                key="it_pm_calendar_v2" # เปลี่ยน key เพื่อบังคับวาดใหม่
            )
            
            # 3. ระบบแสดงรายละเอียดเมื่อคลิก/แตะ ที่ปฏิทิน
            if cal_action and "callback" in cal_action and cal_action["callback"] == "eventClick":
                event_id = cal_action["eventClick"]["event"]["id"]
                
                # ดึงข้อมูลงานที่ถูกคลิก
                clicked_event = df_pm[df_pm['id'] == event_id]
                if not clicked_event.empty:
                    target = clicked_event.iloc[0]
                    st.markdown("---")
                    st.markdown(f"### 📌 รายละเอียดงาน: {target['task_name']}")
                    
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.write(f"**รหัสงาน:** {target['id']}")
                        st.write(f"**วันที่กำหนดทำ:** {target['next_due_date']}")
                        st.write(f"**ความถี่:** {target.get('frequency', 'ไม่ได้ระบุ')}")
                    with col_info2:
                        st.write(f"**ผู้รับผิดชอบ:** {target.get('assignee', 'ไม่ได้ระบุ')}")
                        status_text = "🟢 เสร็จสิ้นแล้ว" if target['status'] == "Completed" else "🟡 รอดำเนินการ"
                        st.write(f"**สถานะ:** {status_text}")
                        
                    # แสดง Checklist
                    st.info(f"**📝 รายการ Checklist:**\n\n{target.get('checklist', 'ไม่มีข้อมูล')}")
                    
                    # ถ้างานเสร็จแล้ว ให้โชว์ผลการตรวจสอบด้วย
                    if target['status'] == "Completed" and pd.notna(target.get('pm_result')):
                        st.success(f"**✅ ผลการตรวจสอบ:**\n\n{target['pm_result']}")

        else:
            st.info("💡 ยังไม่มีข้อมูลแผนงาน PM ในฐานข้อมูล (กรุณาเพิ่มแผนใหม่ในแท็บ 'ลงทะเบียนแผนใหม่')")

    # --- Tab 2: รายการและบันทึกผล ---
    with tab_list:
        if not df_pm.empty:
            st.dataframe(df_pm[['id', 'task_name', 'next_due_date', 'assignee', 'status']], use_container_width=True, hide_index=True)
            pending = df_pm[df_pm['status'] != 'Completed']
            
            if not pending.empty:
                st.divider()
                st.subheader("📝 บันทึกผลการตรวจเช็ค")
                
                # เลือกงาน PM
                sel = st.selectbox("เลือกงาน PM เพื่อบันทึกผล", pending['id'].tolist())
                
                # 4. แสดง Checklist ทันทีตามงานที่เลือก
                target_pm = pending[pending['id'] == sel].iloc[0]
                with st.expander(f"📌 ดูรายละเอียด Checklist: {target_pm['task_name']}", expanded=True):
                    st.info(f"**รายการที่ต้องตรวจ:**\n\n{target_pm.get('checklist', 'ไม่มีข้อมูล Checklist หรือไม่ได้ระบุไว้')}")
                
                # ฟอร์มบันทึกผล
                with st.form("pm_finish_form"):
                    res = st.text_area("บันทึกผลการตรวจสอบ / ปัญหาที่พบ")
                    if st.form_submit_button("✅ บันทึกและปิดงาน PM"):
                        update_pm_full(sel, "Completed", res)
                        st.success(f"บันทึกผลงาน {sel} เรียบร้อยแล้ว")
                        st.rerun()
            else:
                st.success("🎉 ทุกแผนงานในระบบดำเนินการเสร็จสิ้นแล้ว!")

    # --- Tab 3: ลงทะเบียนแผนใหม่ ---
    with tab_add:
        st.subheader("➕ เพิ่มแผนบำรุงรักษาและจัดตารางอัตโนมัติ")
        with st.form("pm_auto_form"):
            name = st.text_input("ชื่องาน PM (เช่น CCTV)*")
            c1, c2 = st.columns(2)
            with c1:
                s_date = st.date_input("เริ่มตั้งแต่วันที่")
                freq = st.selectbox("ความถี่", ["รายวัน", "รายสัปดาห์", "รายเดือน", "รายปี"])
            with c2:
                assign = st.text_input("ช่างผู้รับผิดชอบ")
                count = st.number_input("จำนวนครั้งที่ต้องการวางแผนล่วงหน้า", min_value=1, value=12)
            
            check = st.text_area("รายการ Checklist")
            
            if st.form_submit_button("📅 บันทึกและจัดตารางลงปฏิทิน"):
                if name and assign and check:
                    curr_date = s_date
                    current_year = datetime.now().year
                    
                    for i in range(count):
                        unique_id = f"PM-{name}({i+1}/{count}){current_year}"
                        
                        insert_data("pm_schedules", {
                            "id": unique_id, 
                            "task_name": f"{name} ({i+1}/{count})", 
                            "next_due_date": str(curr_date), 
                            "status": "Scheduled", 
                            "assignee": assign, 
                            "checklist": check, 
                            "frequency": freq
                        })
                        
                        if freq == "รายวัน": curr_date += relativedelta(days=1)
                        elif freq == "รายสัปดาห์": curr_date += relativedelta(weeks=1)
                        elif freq == "รายเดือน": curr_date += relativedelta(months=1)
                        elif freq == "รายปี": curr_date += relativedelta(years=1)
                    
                    st.success(f"✅ สร้างแผนงานเรียบร้อย! (รหัสเริ่มต้น: PM-{name}(1/{count}){current_year})")
                    st.rerun()
                else:
                    st.error("❌ กรุณากรอกข้อมูลให้ครบถ้วนก่อนบันทึก")
