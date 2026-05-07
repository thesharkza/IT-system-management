import streamlit as st
import pandas as pd
import base64
from datetime import datetime
from supabase import create_client, Client
from streamlit_calendar import calendar

# --- CUSTOM UI STYLING ---
st.markdown("""
    <style>
    /* ปรับแต่งฟอนต์ภาษาไทยให้ดูทันสมัย */
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Prompt', sans-serif;
    }

    /* ตกแต่ง Sidebar ให้ดูโปรเฟสชันนอล */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }

    /* ปรับแต่ง Card (Metric) ให้มีเงาและขอบโค้ง */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* ปรับแต่งปุ่มกด (Buttons) */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #0046ad;
        color: white;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #002d70;
        border: none;
        color: white;
    }

    /* ปรับแต่งตาราง (Dataframe) */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
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
            
            submitted = st.form_submit_button("ส่งเรื่องแจ้งซ่อม")
            
            if submitted:
                if user_name and description: # บังคับให้กรอกชื่อและรายละเอียด
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
                    
                    # --- สร้างการแจ้งเตือน 2 ระดับ ---
                    st.toast('ส่งเรื่องแจ้งซ่อมเรียบร้อยแล้ว!', icon='✅') # เด้งที่มุมขวาล่าง
                    st.success(f"🎉 บันทึกข้อมูลสำเร็จ! ทีมช่างได้รับเรื่องแล้ว หมายเลขอ้างอิงของคุณคือ: **{ticket_id}**")
                    # ----------------------------------
                    
                else:
                    st.error("❌ กรุณาระบุชื่อผู้แจ้งและรายละเอียดปัญหาให้ครบถ้วน")

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
    st.header("💻 รายการงานซ่อมและอัปเดตสถานะ")
    df_tickets = load_table("tickets")
    
    if not df_tickets.empty:
        # 1. เตรียมตารางสำหรับแสดงผล (เปลี่ยนชื่อหัวข้อให้เหมือนหน้า User)
        df_manage_view = df_tickets[['id', 'date', 'user', 'dept', 'category', 'urgency', 'status']].copy()
        
        # เรียงลำดับงาน (Pending ขึ้นก่อน)
        sort_map = {'รอตรวจสอบ': 1, 'ดำเนินการ': 2, 'ส่งซ่อม': 3, 'สำเร็จ': 4}
        df_manage_view['sort'] = df_manage_view['status'].map(sort_map)
        df_manage_view = df_manage_view.sort_values(by=['sort', 'date'], ascending=[True, False]).drop('sort', axis=1)

        df_manage_view.rename(columns={
            'id': 'รหัสงาน',
            'date': 'วันที่แจ้ง',
            'user': 'ผู้แจ้ง',
            'dept': 'แผนก',
            'category': 'ประเภท',
            'urgency': 'ความเร่งด่วน',
            'status': 'สถานะ'
        }, inplace=True)

        # 2. ฟังก์ชันลงสี (อ้างอิงจากฟังก์ชันเดิมของคุณ)
        def color_status(val):
            if val == 'รอตรวจสอบ': return 'background-color: #ffebee; color: #c62828; font-weight: bold'
            elif val == 'ดำเนินการ': return 'background-color: #fff8e1; color: #f57f17; font-weight: bold'
            elif val == 'ส่งซ่อม': return 'background-color: #f3e5f5; color: #6a1b9a; font-weight: bold'
            elif val == 'สำเร็จ': return 'background-color: #e8f5e9; color: #2e7d32; font-weight: bold'
            return ''

        try:
            styled_manage = df_manage_view.style.applymap(color_status, subset=['สถานะ'])
        except:
            styled_manage = df_manage_view.style.map(color_status, subset=['สถานะ'])

        # แสดงตารางแบบสวยงาม
        st.dataframe(styled_manage, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # --- ส่วนฟอร์มแก้ไขข้อมูล (ยังคงใช้ ID เดิมในการ Query) ---
        st.subheader("🔧 อัปเดตรายละเอียดงานและปิดจ๊อบ")
        selected_id = st.selectbox("เลือกรหัสงานที่ต้องการจัดการ", df_tickets['id'].tolist())
        tk = df_tickets[df_tickets['id'] == selected_id].iloc[0]
        
        with st.form("edit_job_form"):
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"**อาการที่แจ้ง:** {tk['desc']}")
                
                # เช็คและแสดงรูปภาพ
                img_path = tk.get('image_path', '')
                if img_path and str(img_path).startswith('data:image'):
                    try: st.image(img_path, caption="รูปภาพประกอบปัญหา", width=400)
                    except: st.error("ไม่สามารถแสดงรูปภาพได้")
                
                n_status = st.selectbox("สถานะปัจจุบัน", ticket_statuses, index=ticket_statuses.index(tk['status']))
                assignee = st.text_input("ช่างผู้รับผิดชอบ", value=tk.get('assignee') if pd.notna(tk.get('assignee')) else "")
            
            with c2:
                root = st.text_area("สาเหตุของปัญหา", value=tk.get('root_cause') if pd.notna(tk.get('root_cause')) else "")
                sol = st.text_area("วิธีการแก้ไข", value=tk.get('solution') if pd.notna(tk.get('solution')) else "")
                cost = st.number_input("ค่าใช้จ่าย (บาท)", value=float(tk.get('cost')) if pd.notna(tk.get('cost')) else 0.0)
            
            submitted = st.form_submit_button("บันทึกข้อมูลงานซ่อม")
            
            if submitted:
                update_ticket_full(selected_id, n_status, assignee, root, sol, cost)
                st.success(f"✅ บันทึกข้อมูลงาน {selected_id} สำเร็จ!")
                st.rerun()
    else:
        st.info("ยังไม่มีงานซ่อมในระบบ")

# ==========================================
# หน้าที่ 3: Dashboard (Full Analytics with Monthly Filter)
# ==========================================
elif page == "📊 Dashboard" and st.session_state.is_admin:
    st.title("📈 IT Performance Overview")
    
    # 1. โหลดข้อมูล
    df = load_table("tickets")

    if not df.empty:
        # --- ระบบคัดกรองรายเดือน (Monthly Filter) ---
        # แปลงคอลัมน์ date เป็น datetime object เพื่อให้ดึงเดือน/ปีง่ายขึ้น
        df['date_dt'] = pd.to_datetime(df['date'])
        
        # สร้างชื่อเดือนภาษาไทยหรือรูปแบบ "Month Year"
        df['month_year'] = df['date_dt'].dt.strftime('%m-%Y') # รูปแบบ 05-2026
        
        # สร้างรายการเดือนที่มีข้อมูลจริงในระบบเพื่อทำ Dropdown
        month_list = sorted(df['month_year'].unique(), reverse=True)
        month_options = ["ทั้งหมด"] + month_list
        
        # ส่วน UI สำหรับเลือกเดือน
        col_filter1, col_filter2 = st.columns([1, 3])
        with col_filter1:
            selected_month = st.selectbox("📅 เลือกเดือนที่ต้องการดู", month_options)
        
        # ทำการกรองข้อมูลตามเดือนที่เลือก
        if selected_month != "ทั้งหมด":
            df_filtered = df[df['month_year'] == selected_month].copy()
            st.info(f"🔎 แสดงข้อมูลเฉพาะเดือน: **{selected_month}**")
        else:
            df_filtered = df.copy()
            st.info("🔎 แสดงข้อมูลภาพรวมทั้งหมด")

        # --- ส่วนแสดงผล (ใช้ df_filtered แทน df ทั้งหมด) ---
        
        # สรุปตัวเลขสำคัญแบบการ์ด 4 ใบ
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("งานแจ้งซ่อม", len(df_filtered))
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
        
        # ส่วนแสดงกราฟสถิติ
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🏢 ปริมาณงานแยกตามแผนก")
            if not df_filtered.empty:
                st.bar_chart(df_filtered['dept'].value_counts(), color="#0046ad")
        with c2:
            st.subheader("🛠️ ประเภทปัญหาที่พบบ่อย")
            if not df_filtered.empty:
                st.bar_chart(df_filtered['category'].value_counts(), color="#ff4b4b")

        st.divider()

        # ส่วนคะแนน CSAT 5 หัวข้อ
        with st.expander("📊 รายละเอียดคะแนนประเมิน (CSAT)", expanded=True):
            csat_stats = pd.DataFrame({
                "หัวข้อการประเมิน": [
                    "1. การสนับสนุนจากทีมงาน", 
                    "2. คุณภาพการบริการ HW/SW", 
                    "3. ความเป็นมืออาชีพ", 
                    "4. ความตรงต่อเวลา", 
                    "5. ความพึงพอใจในภาพรวม"
                ],
                "คะแนนเฉลี่ย": [
                    df_filtered['q1'].mean(), df_filtered['q2'].mean(), 
                    df_filtered['q3'].mean(), df_filtered['q4'].mean(), df_filtered['q5'].mean()
                ]
            })
            st.table(csat_stats)

        # ส่วนข้อเสนอแนะล่าสุด
        st.subheader("💬 ข้อเสนอแนะในเดือนนี้")
        feedback_list = df_filtered[df_filtered['feedback'].notna()][['date', 'user', 'rating', 'feedback']].sort_values(by='date', ascending=False)
        
        if not feedback_list.empty:
            feedback_list.rename(columns={'date': 'วันที่', 'user': 'ผู้แจ้ง', 'rating': 'คะแนน', 'feedback': 'ความคิดเห็น'}, inplace=True)
            st.dataframe(feedback_list, use_container_width=True, hide_index=True)
        else:
            st.write("ไม่มีข้อเสนอแนะเพิ่มเติม")

    else:
        st.warning("⚠️ ยังไม่มีข้อมูลงานแจ้งซ่อมในฐานข้อมูล")
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
# หน้าที่ 5: แผนบำรุงรักษา (PM) + Calendar View
# ==========================================
elif page == "🔧 แผนบำรุงรักษา (PM)" and st.session_state.is_admin:
    st.title("🔧 Preventive Maintenance Planner")
    
    tab_cal, tab_list, tab_add = st.tabs(["📅 ปฏิทินงาน PM", "📋 รายการทั้งหมด", "➕ เพิ่มแผนใหม่"])

    # โหลดข้อมูล PM
    df_pm = load_table("pm_schedules")

    # --- Tab 1: ปฏิทินงาน PM ---
    with tab_cal:
        if not df_pm.empty:
            # แปลงข้อมูลในตารางให้เป็นรูปแบบ Events ของปฏิทิน
            calendar_events = []
            for _, row in df_pm.iterrows():
                # กำหนดสีตามสถานะ
                event_color = "#2e7d32" if row['status'] == "Completed" else "#0046ad"
                
                calendar_events.append({
                    "title": f"🛠️ {row['task_name']}",
                    "start": row['next_due_date'],
                    "end": row['next_due_date'],
                    "color": event_color,
                    "id": row['id']
                })

            # ตั้งค่าปฏิทิน
            calendar_options = {
                "headerToolbar": {
                    "left": "prev,next today",
                    "center": "title",
                    "right": "dayGridMonth,timeGridWeek"
                },
                "initialView": "dayGridMonth",
                "selectable": True,
            }

            # แสดงผลปฏิทิน
            state = calendar(
                events=calendar_events,
                options=calendar_options,
                key="pm_calendar",
            )
            
            if state.get("eventClick"):
                st.toast(f"งานที่เลือก: {state['eventClick']['event']['title']}")
        else:
            st.info("ยังไม่มีแผนงาน PM ในระบบ")

    # --- Tab 2: รายการทั้งหมด (ตารางเดิมที่คุณมี) ---
    with tab_list:
        if not df_pm.empty:
            st.dataframe(df_pm, use_container_width=True, hide_index=True)
            st.divider()
            # ส่วนบันทึกผลการตรวจ (อ้างอิงจากโค้ดเดิม)
            pending_pm = df_pm[df_pm['status'] != 'Completed']
            if not pending_pm.empty:
                sel_pm = st.selectbox("เลือกงาน PM เพื่อบันทึกผล", pending_pm['id'].tolist())
                pm_target = df_pm[df_pm['id'] == sel_pm].iloc[0]
                st.warning(f"**Checklist:** {pm_target['checklist']}")
                with st.form("pm_completion_form"):
                    res = st.text_area("บันทึกผลการตรวจสอบ")
                    if st.form_submit_button("บันทึกและปิดงาน PM"):
                        update_pm_full(sel_pm, "Completed", res)
                        st.success("บันทึกผลสำเร็จ")
                        st.rerun()

    # --- Tab 3: เพิ่มแผนใหม่ (กลับมาใช้รูปแบบเดิมที่คุณคุ้นเคย) ---
    with tab_add:
        st.subheader("➕ ลงทะเบียนแผนการบำรุงรักษา")
        with st.form("new_pm_original_style"):
            # กลับมาใช้ตัวแปรและการวางรูปแบบเดิม
            pm_n = st.text_input("ชื่องาน (Task Name)")
            pm_d = st.date_input("กำหนดวันทำ (Next Due Date)")
            pm_c = st.text_area("รายการ Checklist / รายละเอียด")
            
            if st.form_submit_button("บันทึกแผนงาน"):
                if pm_n and pm_c:
                    # สร้าง ID แบบสั้นเพื่อให้ระบบทำงานได้
                    pm_id = f"PM-{datetime.now().strftime('%M%S')}"
                    
                    insert_data("pm_schedules", {
                        "id": pm_id,
                        "task_name": pm_n,
                        "next_due_date": str(pm_d),
                        "status": "Scheduled",
                        "checklist": pm_c
                    })
                    st.toast("บันทึกแผนงานสำเร็จ!", icon="✅")
                    st.success(f"เพิ่มแผนงาน: {pm_n} เรียบร้อยแล้ว")
                    st.rerun()
                else:
                    st.error("กรุณากรอกชื่องานและรายการ Checklist ให้ครบถ้วน")
