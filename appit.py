import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="IT Management System", layout="wide", initial_sidebar_state="expanded")

# --- DATABASE SETUP (Supabase) ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

def load_table(table_name):
    response = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def insert_data(table_name, data_dict):
    supabase.table(table_name).insert(data_dict).execute()

def update_status(table_name, record_id, new_status):
    supabase.table(table_name).update({"status": new_status}).eq("id", record_id).execute()

# ==========================================
# ระบบ LOGIN (ซ่อนเมนู Admin)
# ==========================================
ADMIN_PASSWORD = "itpassword123"

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

st.sidebar.title("🔐 สำหรับเจ้าหน้าที่ IT")
if not st.session_state.is_admin:
    admin_pass = st.sidebar.text_input("ใส่รหัสผ่านเพื่อเข้าโหมดจัดการ", type="password")
    if st.sidebar.button("เข้าสู่ระบบ"):
        if admin_pass == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.rerun()
        else:
            st.sidebar.error("❌ รหัสผ่านไม่ถูกต้อง")
else:
    st.sidebar.success("✅ โหมด IT Admin ทำงาน")
    if st.sidebar.button("ออกจากระบบ (Logout)"):
        st.session_state.is_admin = False
        st.rerun()

st.sidebar.divider()

# ==========================================
# จัดการเมนูที่แสดงผลตามสิทธิ์
# ==========================================
st.sidebar.title("🛠️ IT System Menu")

if st.session_state.is_admin:
    menu_options = [
        "📝 แจ้งปัญหา (User)", 
        "💻 จัดการตั๋วงาน (Helpdesk)", 
        "📊 สรุปภาพรวม (Dashboard)", 
        "🗄️ ฐานข้อมูลอุปกรณ์ (Assets)", 
        "🔧 แผนบำรุงรักษา (PM)"
    ]
else:
    menu_options = ["📝 แจ้งปัญหา (User)"]

page = st.sidebar.radio("เลือกหน้าต่างการทำงาน", menu_options)

depts = ["MAT", "KD1", "QC", "Office", "Other"]

# ==========================================
# หน้าที่ 1: แจ้งปัญหา (User) - ทุกคนเข้าถึงได้
# ==========================================
if page == "📝 แจ้งปัญหา (User)":
    st.header("ฟอร์มแจ้งปัญหาการใช้งาน / ขอรับบริการ")
    with st.form("ticket_form"):
        col1, col2 = st.columns(2)
        with col1:
            user_name = st.text_input("ชื่อผู้แจ้ง")
            department = st.selectbox("แผนก", depts) 
        with col2:
            category = st.selectbox("ประเภทปัญหา", ["Hardware", "Software (เช่น MS Office)", "Network", "Account/Access", "Other"])
            asset_id = st.text_input("รหัสอุปกรณ์ที่มีปัญหา (ถ้าทราบ)")
            
        description = st.text_area("รายละเอียดปัญหา")
        submitted = st.form_submit_button("ส่งข้อมูลแจ้ง IT")

        if submitted and user_name and description:
            df_existing = load_table("tickets")
            ticket_id = f"IT-{len(df_existing) + 1:04d}"
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            full_desc = f"[Asset: {asset_id}] {description}" if asset_id else description
            
            insert_data("tickets", {
                "id": ticket_id, "date": date_str, "user": user_name, 
                "dept": department, "category": category, "desc": full_desc, "status": "Pending"
            })
            st.success(f"✅ บันทึกสำเร็จ! หมายเลขงาน: {ticket_id} (โปรดแคปหน้าจอไว้เป็นหลักฐาน)")
            st.rerun()

    # --- เพิ่มส่วน Dashboard ติดตามสถานะให้ User ---
    st.divider()
    st.subheader("📋 กระดานติดตามสถานะงาน (Ticket Tracking)")
    
    df_tickets = load_table("tickets")
    if not df_tickets.empty:
        # เลือกข้อมูลมาแสดง (ซ่อนรายละเอียดเชิงลึกเพื่อความสะอาดตา)
        df_user_view = df_tickets[['id', 'date', 'user', 'dept', 'category', 'status']].copy()
        
        # กำหนดความสำคัญในการเรียงลำดับ (Pending ขึ้นก่อน -> In Progress -> Resolved)
        sort_mapping = {'Pending': 1, 'In Progress': 2, 'Resolved': 3}
        df_user_view['sort_order'] = df_user_view['status'].map(sort_mapping)
        
        # เรียงข้อมูลตามสถานะ และวันที่แจ้งล่าสุด
        df_user_view = df_user_view.sort_values(by=['sort_order', 'date'], ascending=[True, False]).drop('sort_order', axis=1)
        
        # ฟังก์ชันกำหนดสีตามสถานะงาน
        def color_status(val):
            if val == 'Pending':
                return 'background-color: #ffebee; color: #c62828; font-weight: bold' # สีแดงอ่อน
            elif val == 'In Progress':
                return 'background-color: #fff8e1; color: #f57f17; font-weight: bold' # สีเหลืองส้ม
            elif val == 'Resolved':
                return 'background-color: #e8f5e9; color: #2e7d32; font-weight: bold' # สีเขียว
            return ''
            
        # สร้างตารางพร้อมลงสีด้วยฟังก์ชัน .applymap (หรือ .map สำหรับ pandas เวอร์ชันใหม่)
        try:
            styled_df = df_user_view.style.applymap(color_status, subset=['status'])
        except AttributeError:
            styled_df = df_user_view.style.map(color_status, subset=['status'])
            
        # แสดงผลตาราง (ซ่อน Index ด้านหน้า)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีงานซ่อมในระบบขณะนี้")

# ==========================================
# หน้าที่ 2-5: เฉพาะ IT Admin เท่านั้น
# ==========================================
if st.session_state.is_admin:
    
    if page == "💻 จัดการตั๋วงาน (Helpdesk)":
        st.header("กระดานจัดการงาน IT")
        df_tickets = load_table("tickets")
        
        if df_tickets.empty:
            st.info("ไม่มีงานค้างในระบบ")
        else:
            df_tickets = df_tickets[['id', 'date', 'user', 'dept', 'category', 'desc', 'status']]
            st.dataframe(df_tickets, use_container_width=True)
            st.divider()
            
            st.subheader("🔄 อัปเดตสถานะงาน")
            col_a, col_b = st.columns(2)
            with col_a:
                tid = st.selectbox("เลือก Ticket ID", df_tickets['id'].tolist())
            with col_b:
                new_st = st.selectbox("สถานะใหม่", ["Pending", "In Progress", "Resolved"])
            if st.button("บันทึกสถานะงาน"):
                update_status("tickets", tid, new_st)
                st.success("อัปเดตเรียบร้อย!")
                st.rerun()

    elif page == "📊 สรุปภาพรวม (Dashboard)":
        st.header("สถิติและประสิทธิภาพการทำงาน")
        df_tickets = load_table("tickets")
        
        if df_tickets.empty:
            st.warning("ยังไม่มีข้อมูลเพียงพอสำหรับแสดงกราฟ")
        else:
            col1, col2, col3 = st.columns(3)
            total_tickets = len(df_tickets)
            resolved = len(df_tickets[df_tickets['status'] == 'Resolved'])
            pending = len(df_tickets[df_tickets['status'] == 'Pending'])
            
            col1.metric("งานทั้งหมด", total_tickets)
            col2.metric("เสร็จสิ้นแล้ว", resolved)
            col3.metric("รอดำเนินการ", pending)
            
            st.divider()
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.subheader("จำนวนงานแยกตามแผนก")
                dept_counts = df_tickets['dept'].value_counts()
                st.bar_chart(dept_counts)
                
            with col_chart2:
                st.subheader("จำนวนงานแยกตามประเภท")
                cat_counts = df_tickets['category'].value_counts()
                st.bar_chart(cat_counts)

    elif page == "🗄️ ฐานข้อมูลอุปกรณ์ (Assets)":
        st.header("ทะเบียนทรัพย์สิน IT")
        with st.expander("➕ เพิ่มอุปกรณ์ใหม่"):
            with st.form("asset_form"):
                a1, a2 = st.columns(2)
                with a1:
                    asset_id = st.text_input("รหัสทรัพย์สิน (เช่น PC-001)")
                    asset_type = st.selectbox("ประเภท", ["PC/Laptop", "Printer/Scanner", "Network Switch", "UPS", "Other"])
                with a2:
                    asset_model = st.text_input("ยี่ห้อ / รุ่น")
                    asset_dept = st.selectbox("ประจำแผนก", depts)
                
                if st.form_submit_button("บันทึกอุปกรณ์"):
                    if asset_id:
                        insert_data("assets", {
                            "id": asset_id, "type": asset_type, "model": asset_model, 
                            "dept": asset_dept, "status": "Active"
                        })
                        st.success("✅ เพิ่มอุปกรณ์ลงระบบแล้ว")
                        st.rerun()

        df_assets = load_table("assets")
        if not df_assets.empty:
            st.dataframe(df_assets[['id', 'type', 'model', 'dept', 'status']], use_container_width=True)

    elif page == "🔧 แผนบำรุงรักษา (PM)":
        st.header("ระบบแผนงาน Preventive Maintenance")
        with st.expander("➕ เพิ่มแผน PM ใหม่"):
            with st.form("pm_form"):
                p1, p2 = st.columns(2)
                with p1:
                    pm_name = st.text_input("หัวข้องาน")
                    pm_freq = st.selectbox("ความถี่", ["รายสัปดาห์", "รายเดือน", "รายไตรมาส", "รายปี"])
                with p2:
                    pm_date = st.date_input("วันที่ต้องดำเนินการครั้งถัดไป")
                
                if st.form_submit_button("สร้างแผน PM"):
                    if pm_name:
                        df_pm = load_table("pm_schedules")
                        pm_id = f"PM-{len(df_pm) + 1:03d}"
                        insert_data("pm_schedules", {
                            "id": pm_id, "task_name": pm_name, "frequency": pm_freq, 
                            "next_due_date": str(pm_date), "status": "Scheduled"
                        })
                        st.success("✅ สร้างแผนเรียบร้อย")
                        st.rerun()

        df_pm = load_table("pm_schedules")
        if not df_pm.empty:
            st.dataframe(df_pm[['id', 'task_name', 'frequency', 'next_due_date', 'status']], use_container_width=True)
            
            st.divider()
            st.subheader("✔️ อัปเดตสถานะงาน PM")
            c1, c2 = st.columns(2)
            with c1:
                pm_update_id = st.selectbox("เลือก PM ID", df_pm['id'].tolist())
            with c2:
                pm_new_st = st.selectbox("อัปเดตสถานะ", ["Scheduled", "Completed", "Overdue"])
            if st.button("อัปเดต PM"):
                update_status("pm_schedules", pm_update_id, pm_new_st)
                st.success("อัปเดตสถานะ PM เรียบร้อย!")
                st.rerun()
