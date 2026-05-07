import streamlit as st
import pandas as pd
import base64
from datetime import datetime
from supabase import create_client, Client

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
    # คำนวณค่าเฉลี่ย
    avg_score = (q1 + q2 + q3 + q4 + q5) / 5
    
    # ปรับปรุง: ใช้ round() เพื่อให้มั่นใจว่าเป็นตัวเลขที่เหมาะสม
    supabase.table("tickets").update({
        "q1": int(q1), 
        "q2": int(q2), 
        "q3": int(q3), 
        "q4": int(q4), 
        "q5": int(q5),
        "feedback": feedback, 
        "rating": round(avg_score, 2) # เก็บเป็นทศนิยม 2 ตำแหน่ง
    }).eq("id", record_id).execute()

def update_pm_full(record_id, status, pm_result):
    supabase.table("pm_schedules").update({
        "status": status, "pm_result": pm_result
    }).eq("id", record_id).execute()

# --- CSAT CONFIG ---
rating_scale = {"พอใจมากที่สุด": 5, "พอใจ": 4, "ปานกลาง": 3, "ไม่พอใจ": 2, "ไม่พอใจอย่างมาก": 1}
scale_options = list(rating_scale.keys())

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

depts = ["MAT", "KD1", "QC", "Office", "Other"]
ticket_statuses = ["รอตรวจสอบ", "ดำเนินการ", "ส่งซ่อม", "สำเร็จ"]

# ==========================================
# หน้าที่ 1: แจ้งซ่อม & ประเมิน & ตารางติดตาม (User)
# ==========================================
if page == "📝 แจ้งซ่อม (User)":
    st.header("ระบบแจ้งซ่อมและติดตามงานออนไลน์")
    
    tab1, tab2 = st.tabs(["🆕 ส่งใบแจ้งซ่อม", "⭐ ประเมินความพึงพอใจ"])
    
    with tab1:
        with st.form("ticket_form"):
            c1, c2 = st.columns(2)
            with c1:
                user_name = st.text_input("ชื่อผู้แจ้ง")
                department = st.selectbox("แผนก", depts) 
                category = st.selectbox("ประเภทงานซ่อม", ["Hardware", "Software", "Network", "Other"])
            with c2:
                asset_id_input = st.text_input("รหัสอุปกรณ์ (Asset ID)") 
                urgency = st.selectbox("ระดับความเร่งด่วน", ["ปกติ", "ด่วน", "ด่วนมาก"])
                uploaded_file = st.file_uploader("แนบรูปภาพประกอบ", type=['png', 'jpg', 'jpeg'])
            description = st.text_area("รายละเอียดปัญหา")
            if st.form_submit_button("ส่งเรื่องแจ้งซ่อม"):
                df_existing = load_table("tickets")
                ticket_id = f"JOB-{len(df_existing) + 1:04d}"
                image_data = ""
                if uploaded_file:
                    encoded_img = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                    image_data = f"data:{uploaded_file.type};base64,{encoded_img}"
                
                insert_data("tickets", {
                    "id": ticket_id, "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "user": user_name, 
                    "dept": department, "category": category, "desc": description, 
                    "status": "รอตรวจสอบ", "urgency": urgency, "image_path": image_data, "asset_id": asset_id_input 
                })
                st.success(f"บันทึกสำเร็จ! รหัสงาน: {ticket_id}")
                st.rerun()

    with tab2:
        st.subheader("งานซ่อมที่รอการประเมิน")
        df_all = load_table("tickets")
        if not df_all.empty:
            ready_to_rate = df_all[(df_all['status'] == 'สำเร็จ') & (df_all['q1'].isna())]
            if not ready_to_rate.empty:
                selected_job = st.selectbox("เลือกงานซ่อมที่คุณต้องการประเมิน", ready_to_rate['id'].tolist())
                with st.form("detailed_csat_form"):
                    q1 = st.radio("1. คุณพอใจกับการสนับสนุนที่ทีมงานของเรามอบให้มากน้อยเพียงใด?", scale_options, horizontal=True)
                    q2 = st.radio("2. คุณจะให้คะแนนคุณภาพการบริการด้านฮาร์ดแวร์/ซอฟต์แวร์ของเราอย่างไร?", scale_options, horizontal=True)
                    q3 = st.radio("3. คุณจะให้คะแนนความมืออาชีพและความเชี่ยวชาญของทีมเราอย่างไร?", scale_options, horizontal=True)
                    q4 = st.radio("4. คุณจะให้คะแนนการบริการตรงเวลาของทีมของเราอย่างไร?", scale_options, horizontal=True)
                    q5 = st.radio("5. คุณมีความพึงพอใจในการบริการจากเจ้าหน้าที่ไอทีในครั้งนี้มากน้อยเพียงใด?", scale_options, horizontal=True)
                    fback = st.text_area("ข้อเสนอแนะเพิ่มเติม")
                    if st.form_submit_button("บันทึกการประเมิน"):
                        update_csat_full(selected_job, rating_scale[q1], rating_scale[q2], rating_scale[q3], rating_scale[q4], rating_scale[q5], fback)
                        st.success("ขอบคุณสำหรับคะแนนประเมินครับ!")
                        st.rerun()
            else: st.info("ไม่มีงานซ่อมที่รอการประเมิน")

   # --- ส่วนตารางติดตามสถานะหน้า User ---
    st.divider()
    st.subheader("📋 ตรวจสอบสถานะงานซ่อม")
    df_tickets = load_table("tickets")
    
    if not df_tickets.empty:
        df_view = df_tickets[['id', 'date', 'user', 'category', 'urgency', 'status', 'rating']].copy()
        
        # เรียงลำดับ (Pending ขึ้นก่อน)
        sort_map = {'รอตรวจสอบ': 1, 'ดำเนินการ': 2, 'ส่งซ่อม': 3, 'สำเร็จ': 4}
        df_view['sort'] = df_view['status'].map(sort_map)
        df_view = df_view.sort_values(by=['sort', 'date'], ascending=[True, False]).drop('sort', axis=1)
        
        df_view.rename(columns={
            'id':'รหัสงาน', 'date':'วันที่แจ้ง', 'user':'ผู้แจ้ง',
            'category':'ประเภท', 'urgency':'ความเร่งด่วน', 'status':'สถานะ', 'rating':'คะแนนเฉลี่ย'
        }, inplace=True)
        
        # --- ฟังก์ชันใหม่: แปลงตัวเลขเป็นดาว ---
        def display_stars(val):
            if pd.isna(val):  # ถ้าตารางว่างเปล่า (ยังไม่ประเมิน)
                return "รอประเมิน"
            else:
                star_count = int(round(float(val))) # ปัดเศษเป็นจำนวนเต็ม
                return "⭐" * star_count # สร้างดาวตามจำนวนตัวเลข
                
        # นำฟังก์ชันมาครอบคอลัมน์คะแนนเฉลี่ย
        df_view['คะแนนเฉลี่ย'] = df_view['คะแนนเฉลี่ย'].apply(display_stars)
        # -----------------------------------
        
        def color_status(val):
            if val == 'รอตรวจสอบ': return 'background-color: #ffebee; color: #c62828'
            elif val == 'ดำเนินการ': return 'background-color: #fff8e1; color: #f57f17'
            elif val == 'ส่งซ่อม': return 'background-color: #f3e5f5; color: #6a1b9a'
            elif val == 'สำเร็จ': return 'background-color: #e8f5e9; color: #2e7d32'
            return ''
        
        try: styled_df = df_view.style.applymap(color_status, subset=['สถานะ'])
        except: styled_df = df_view.style.map(color_status, subset=['สถานะ'])
            
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

# ==========================================
# หน้าที่ 2: จัดการงานซ่อม (ช่าง)
# ==========================================
elif page == "💻 จัดการงานซ่อม (ช่าง)" and st.session_state.is_admin:
    st.header("จัดการงานซ่อม")
    df_tickets = load_table("tickets")
    if not df_tickets.empty:
        st.dataframe(df_tickets[['id', 'date', 'user', 'dept', 'category', 'urgency', 'status']], use_container_width=True)
        st.divider()
        
        selected_id = st.selectbox("เลือกรหัสงาน", df_tickets['id'].tolist())
        tk = df_tickets[df_tickets['id'] == selected_id].iloc[0]
        
        # เริ่ม Form
        with st.form("edit_job_form"):
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"**อาการที่แจ้ง:** {tk['desc']}")
                
                # --- จุดที่แก้: ตรวจสอบรูปภาพก่อนแสดงผล เพื่อไม่ให้ Error ---
                img_path = tk.get('image_path', '')
                if img_path and str(img_path).startswith('data:image'):
                    try:
                        st.image(img_path, caption="รูปภาพประกอบปัญหา", width=400)
                    except Exception as e:
                        st.error("ไม่สามารถแสดงรูปภาพได้")
                elif img_path:
                    st.warning(f"📎 มีข้อมูลไฟล์แนบเดิม: {img_path} (ไม่สามารถแสดงผลเป็นรูปได้)")
                # -----------------------------------------------------

                n_status = st.selectbox("สถานะ", ticket_statuses, index=ticket_statuses.index(tk['status']))
                assignee = st.text_input("ช่างผู้รับผิดชอบ", value=tk.get('assignee') if pd.notna(tk.get('assignee')) else "")
            
            with c2:
                root = st.text_area("สาเหตุของปัญหา", value=tk.get('root_cause') if pd.notna(tk.get('root_cause')) else "")
                sol = st.text_area("วิธีการแก้ไข", value=tk.get('solution') if pd.notna(tk.get('solution')) else "")
                cost = st.number_input("ค่าใช้จ่าย (บาท)", value=float(tk.get('cost')) if pd.notna(tk.get('cost')) else 0.0)
            
            # --- จุดที่แก้: ย้ายปุ่ม Submit มาไว้ในฟอร์มให้ชัดเจน ---
            submitted = st.form_submit_button("บันทึกข้อมูลงานซ่อม")
            
            if submitted:
                update_ticket_full(selected_id, n_status, assignee, root, sol, cost)
                st.success("✅ บันทึกข้อมูลสำเร็จ!")
                st.rerun()

# ==========================================
# หน้าที่ 3: Dashboard (Full CSAT)
# ==========================================
elif page == "📊 Dashboard" and st.session_state.is_admin:
    st.header("สถิติและคะแนนความพึงพอใจ")
    df = load_table("tickets")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("งานทั้งหมด", len(df))
        c2.metric("สำเร็จ", len(df[df['status'] == 'สำเร็จ']))
        c3.metric("คะแนนเฉลี่ยรวม", f"{df['rating'].mean():.2f} / 5")
        
        st.divider()
        st.subheader("คะแนนเฉลี่ยแยกตามหัวข้อ")
        csat_stats = pd.DataFrame({
            "หัวข้อประเมิน": ["1. ทีมสนับสนุน", "2. คุณภาพ HW/SW", "3. ความเป็นมืออาชีพ", "4. ความตรงต่อเวลา", "5. ความพึงพอใจรวม"],
            "คะแนน": [df['q1'].mean(), df['q2'].mean(), df['q3'].mean(), df['q4'].mean(), df['q5'].mean()]
        })
        st.table(csat_stats)
        
        st.subheader("ข้อเสนอแนะล่าสุด")
        st.dataframe(df[df['feedback'].notna()][['date', 'user', 'rating', 'feedback']], hide_index=True)

# ==========================================
# หน้าที่ 4: Assets (Detailed History)
# ==========================================
elif page == "🗄️ ทะเบียนอุปกรณ์" and st.session_state.is_admin:
    st.header("ทะเบียนอุปกรณ์")
    with st.expander("ลงทะเบียนใหม่"):
        with st.form("new_asset"):
            a1, a2 = st.columns(2)
            with a1:
                aid = st.text_input("รหัสอุปกรณ์*")
                atyp = st.selectbox("ประเภท", ["PC/Laptop", "Printer", "UPS", "Network", "Other"])
            with a2:
                amod = st.text_input("รุ่น")
                adept = st.selectbox("แผนก", depts)
            if st.form_submit_button("บันทึก"):
                insert_data("assets", {"id":aid, "type":atyp, "model":amod, "dept":adept, "status":"Active"})
                st.rerun()

    df_a = load_table("assets")
    df_t = load_table("tickets")
    if not df_a.empty:
        st.dataframe(df_a, use_container_width=True, hide_index=True)
        st.divider()
        st.subheader("🔍 ตรวจสอบประวัติเครื่อง")
        sel_a = st.selectbox("เลือกรหัสเครื่อง", df_a['id'].tolist())
        history = df_t[df_t['asset_id'] == sel_a]
        if not history.empty:
            st.metric("ยอดค่าซ่อมสะสม", f"฿{pd.to_numeric(history['cost']).sum():,.2f}")
            st.dataframe(history[['date', 'user', 'root_cause', 'solution', 'cost', 'status']], hide_index=True)
        else: st.info("ไม่มีประวัติการซ่อม")

# ==========================================
# หน้าที่ 5: PM (Checklist)
# ==========================================
elif page == "🔧 แผนบำรุงรักษา (PM)" and st.session_state.is_admin:
    st.header("Preventive Maintenance")
    with st.expander("เพิ่มแผน PM"):
        with st.form("new_pm"):
            pm_n = st.text_input("ชื่องาน")
            pm_d = st.date_input("กำหนดวันทำ")
            pm_c = st.text_area("Checklist")
            if st.form_submit_button("บันทึก"):
                insert_data("pm_schedules", {"id":f"PM-{datetime.now().microsecond}","task_name":pm_n,"next_due_date":str(pm_d),"status":"Scheduled","checklist":pm_c})
                st.rerun()
    
    df_p = load_table("pm_schedules")
    if not df_p.empty:
        st.dataframe(df_p, use_container_width=True, hide_index=True)
        st.divider()
        sel_pm = st.selectbox("บันทึกผล PM", df_p[df_p['status']!='Completed']['id'].tolist())
        pm_target = df_p[df_p['id']==sel_pm].iloc[0]
        st.warning(f"**Checklist:** {pm_target['checklist']}")
        with st.form("pm_fin"):
            res = st.text_area("ผลการตรวจ")
            if st.form_submit_button("ปิดงาน PM"):
                update_pm_full(sel_pm, "Completed", res)
                st.rerun()
