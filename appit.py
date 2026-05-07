import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- ตั้งค่าหน้าเว็บ (ต้องอยู่บรรทัดแรกสุดของ Streamlit) ---
st.set_page_config(page_title="IT Helpdesk Online", layout="wide")

# --- DATABASE SETUP (Supabase) ---
# ดึงค่า URL และ Key จากไฟล์ .streamlit/secrets.toml
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

def save_ticket(ticket_id, date, user, dept, cat, desc, status):
    # บันทึกข้อมูลลงตาราง tickets ใน Supabase
    data, count = supabase.table("tickets").insert({
        "id": ticket_id, 
        "date": date, 
        "user": user, 
        "dept": dept, 
        "category": cat, 
        "desc": desc, 
        "status": status
    }).execute()

def update_ticket_status(ticket_id, new_status):
    # อัปเดตสถานะงาน
    data, count = supabase.table("tickets").update({"status": new_status}).eq("id", ticket_id).execute()

def load_data():
    # ดึงข้อมูลทั้งหมดมาแสดงผล
    response = supabase.table("tickets").select("*").execute()
    # แปลงข้อมูลที่ได้จาก Supabase เป็น Pandas DataFrame เพื่อให้แสดงตารางสวยงาม
    if response.data:
        return pd.DataFrame(response.data)
    else:
        return pd.DataFrame()

# --- STREAMLIT UI ---
st.title("🛠️ IT Task Management System")

page = st.sidebar.radio("เมนู", ["📝 แจ้งเรื่อง (User)", "💻 จัดการงาน (IT Admin)"])

if page == "📝 แจ้งเรื่อง (User)":
    st.header("ฟอร์มแจ้งปัญหา")
    with st.form("ticket_form"):
        col1, col2 = st.columns(2)
        with col1:
            user_name = st.text_input("ชื่อผู้แจ้ง")
            department = st.selectbox("แผนก", ["MAT", "KD1", "QC", "Office", "Other"]) 
        with col2:
            category = st.selectbox("ประเภทปัญหา", ["Hardware", "Software", "Network", "Account", "Other"])
            
        description = st.text_area("รายละเอียดปัญหา")
        submitted = st.form_submit_button("ส่งข้อมูลแจ้ง IT")

        if submitted and user_name and description:
            df_existing = load_data()
            # คำนวณ Ticket ID ถัดไป
            current_count = len(df_existing) if not df_existing.empty else 0
            ticket_id = f"IT-{current_count + 1:04d}"
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            save_ticket(ticket_id, date_str, user_name, department, category, description, "Pending")
            st.success(f"✅ บันทึกสำเร็จ! หมายเลขงานของคุณคือ {ticket_id}")

elif page == "💻 จัดการงาน (IT Admin)":
    st.header("Dashboard จัดการงาน IT")
    
    # โหลดข้อมูลจาก Supabase
    df = load_data()
    
    if df.empty:
        st.info("🎉 เยี่ยมมาก! ยังไม่มีงานในระบบ")
    else:
        # จัดเรียงคอลัมน์ให้ดูง่ายขึ้น
        df = df[['id', 'date', 'user', 'dept', 'category', 'desc', 'status']]
        st.dataframe(df, use_container_width=True)
        st.divider()
        
        st.subheader("🔄 อัปเดตสถานะงาน")
        col_a, col_b = st.columns(2)
        with col_a:
            tid = st.selectbox("เลือก Ticket ID", df['id'].tolist())
        with col_b:
            new_st = st.selectbox("สถานะใหม่", ["Pending", "In Progress", "Resolved"])
        
        if st.button("อัปเดตสถานะ"):
            update_ticket_status(tid, new_st)
            st.success(f"อัปเดตงาน {tid} เป็น {new_st} เรียบร้อย!")
            st.rerun()
