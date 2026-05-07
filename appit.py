import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Enterprise CMMS", layout="wide", initial_sidebar_state="expanded")

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

def update_ticket_full(record_id, status, assignee, root_cause, solution, cost):
    supabase.table("tickets").update({
        "status": status,
        "assignee": assignee,
        "root_cause": root_cause,
        "solution": solution,
        "cost": cost
    }).eq("id", record_id).execute()

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
    st.sidebar.success("✅ โหมดช่าง/IT ทำงาน")
    if st.sidebar.button("ออกจากระบบ (Logout)"):
        st.session_state.is_admin = False
        st.rerun()

st.sidebar.divider()

st.sidebar.title("🛠️ ระบบจัดการงานซ่อม")

if st.session_state.is_admin:
    menu_options = [
        "📝 แจ้งซ่อม (User)", 
        "💻 จัดการงานซ่อม (ช่าง)", 
        "📊 Dashboard", 
        "🗄️ ทะเบียนอุปกรณ์", 
        "🔧 แผนบำรุงรักษา (PM)"
    ]
else:
    menu_options = ["📝 แจ้งซ่อม (User)"]

page = st.sidebar.radio("เลือกหน้าต่างการทำงาน", menu_options)

depts = ["MAT", "KD1", "QC", "Office", "Other"]
# สถานะงานแบบใหม่ตามสเปค
ticket_statuses = ["รอตรวจสอบ", "ดำเนินการ", "ส่งซ่อม", "สำเร็จ"]

# ==========================================
# หน้าที่ 1: แจ้งซ่อม (User)
# ==========================================
if page == "📝 แจ้งซ่อม (User)":
    st.header("ฟอร์มแจ้งซ่อมออนไลน์")
    with st.form("ticket_form"):
        col1, col2 = st.columns(2)
        with col1:
            user_name = st.text_input("ชื่อผู้แจ้ง")
            department = st.selectbox("แผนก", depts) 
            category = st.selectbox("ประเภทงานซ่อม", ["Hardware", "Software", "Network", "Other"])
        with col2:
            asset_id = st.text_input("รหัส/ชื่ออุปกรณ์ (ถ้าทราบ)")
            urgency = st.selectbox("ระดับความเร่งด่วน", ["ปกติ", "ด่วน", "ด่วนมาก"])
            uploaded_file = st.file_uploader("แนบไฟล์รูปภาพปัญหา (ถ้ามี)", type=['png', 'jpg', 'jpeg'])
            
        description = st.text_area("รายละเอียดปัญหา")
        submitted = st.form_submit_button("ส่งเรื่องแจ้งซ่อม")

        if submitted and user_name and description:
            df_existing = load_table("tickets")
            ticket_id = f"JOB-{len(df_existing) + 1:04d}" # เปลี่ยน prefix ให้ดูเป็นงานซ่อมมากขึ้น
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            full_desc = f"[อุปกรณ์: {asset_id}] {description}" if asset_id else description
            file_name = uploaded_file.name if uploaded_file else ""
            
            insert_data("tickets", {
                "id": ticket_id, "date": date_str, "user": user_name, 
                "dept": department, "category": category, "desc": full_desc, 
                "status": "รอตรวจสอบ", "urgency": urgency, "image_path": file_name
            })
            st.success(f"✅ บันทึกสำเร็จ! หมายเลขงานของคุณคือ: {ticket_id}")
            st.rerun()

    # --- Dashboard ติดตามสถานะให้ User ---
    st.divider()
    st.subheader("📋 ตรวจสอบสถานะงานซ่อม")
    
    df_tickets = load_table("tickets")
    if not df_tickets.empty:
        # ดึงมาเฉพาะคอลัมน์ที่จำเป็นสำหรับ User
        df_user_view = df_tickets[['id', 'date', 'user', 'category', 'urgency', 'status']].copy()
        
        sort_mapping = {'รอตรวจสอบ': 1, 'ดำเนินการ': 2, 'ส่งซ่อม': 3, 'สำเร็จ': 4}
        df_user_view['sort_order'] = df_user_view['status'].map(sort_mapping)
        df_user_view = df_user_view.sort_values(by=['sort_order', 'date'], ascending=[True, False]).drop('sort_order', axis=1)
        
        df_user_view.rename(columns={
            'id': 'รหัสงาน', 'date': 'เวลาที่แจ้ง', 'user': 'ผู้แจ้ง',
            'category': 'ประเภท', 'urgency': 'ความเร่งด่วน', 'status': 'สถานะ'
        }, inplace=True)
        
        def color_status(val):
            if val == 'รอตรวจสอบ': return 'background-color: #ffebee; color: #c62828'
            elif val == 'ดำเนินการ': return 'background-color: #fff8e1; color: #f57f17'
            elif val == 'ส่งซ่อม': return 'background-color: #f3e5f5; color: #6a1b9a'
            elif val == 'สำเร็จ': return 'background-color: #e8f5e9; color: #2e7d32'
            return ''
            
        try:
            styled_df = df_user_view.style.applymap(color_status, subset=['สถานะ'])
        except AttributeError:
            styled_df = df_user_view.style.map(color_status, subset=['สถานะ'])
            
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

# ==========================================
# หน้าที่ 2: จัดการงานซ่อม (ช่าง / Admin)
# ==========================================
elif page == "💻 จัดการงานซ่อม (ช่าง)":
    st.header("บันทึกข้อมูลและอัปเดตสถานะงานซ่อม")
    df_tickets = load_table("tickets")
    
    if df_tickets.empty:
        st.info("ไม่มีงานในระบบ")
    else:
        # แสดงตารางงานทั้งหมด (ซ่อนคอลัมน์รายละเอียดเชิงลึกไว้ก่อน เพื่อไม่ให้ตารางรก)
        st.dataframe(df_tickets[['id', 'date', 'user', 'dept', 'category', 'urgency', 'status']], use_container_width=True)
        st.divider()
        
        st.subheader("🔧 อัปเดตรายละเอียดงานและปิดจ๊อบ")
        
        # เลือกงานที่ต้องการอัปเดต
        selected_id = st.selectbox("เลือกรหัสงานที่ต้องการจัดการ", df_tickets['id'].tolist())
        
        # ดึงข้อมูลของงานที่เลือกมาแสดงเป็นค่าเริ่มต้น
        ticket_data = df_tickets[df_tickets['id'] == selected_id].iloc[0]
        
        with st.form("update_ticket_form"):
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"**รายละเอียดที่แจ้ง:** {ticket_data['desc']}")
                new_status = st.selectbox("อัปเดตสถานะ", ticket_statuses, index=ticket_statuses.index(ticket_data['status']))
                assignee = st.text_input("ช่างผู้รับผิดชอบ", value=ticket_data.get('assignee', ''))
            with c2:
                root_cause = st.text_area("สาเหตุของปัญหา", value=ticket_data.get('root_cause', ''))
                solution = st.text_area("วิธีการแก้ไข", value=ticket_data.get('solution', ''))
                cost = st.number_input("ค่าใช้จ่ายในการซ่อม (บาท)", min_value=0.0, value=float(ticket_data.get('cost', 0.0)))
                
            if st.form_submit_button("บันทึกข้อมูลงานซ่อม"):
                update_ticket_full(selected_id, new_status, assignee, root_cause, solution, cost)
                st.success(f"อัปเดตข้อมูลงาน {selected_id} เรียบร้อยแล้ว!")
                st.rerun()

# (หมายเหตุ: หน้า Dashboard, Assets, PM คงโค้ดเดิมไว้ด้านล่างนี้ได้เลยครับ เพื่อประหยัดพื้นที่แสดงผล)
