import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('it_tickets.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tickets
                 (id TEXT, date TEXT, user TEXT, dept TEXT, category TEXT, desc TEXT, status TEXT)''')
    conn.commit()
    conn.close()

def save_ticket(id, date, user, dept, cat, desc, status):
    conn = sqlite3.connect('it_tickets.db')
    c = conn.cursor()
    c.execute("INSERT INTO tickets VALUES (?,?,?,?,?,?,?)", (id, date, user, dept, cat, desc, status))
    conn.commit()
    conn.close()

def update_ticket_status(id, new_status):
    conn = sqlite3.connect('it_tickets.db')
    c = conn.cursor()
    c.execute("UPDATE tickets SET status = ? WHERE id = ?", (new_status, id))
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect('it_tickets.db')
    df = pd.read_sql_query("SELECT * FROM tickets", conn)
    conn.close()
    return df

# เริ่มต้นฐานข้อมูล
init_db()

# --- STREAMLIT UI ---
st.set_page_config(page_title="IT Helpdesk Online", layout="wide")
st.title("🛠️ IT Task Management System (Online)")

page = st.sidebar.radio("เมนู", ["📝 แจ้งเรื่อง (User)", "💻 จัดการงาน (IT Admin)"])

if page == "📝 แจ้งเรื่อง (User)":
    st.header("ฟอร์มแจ้งปัญหา (MAT / KD1 / QC)")
    with st.form("ticket_form"):
        col1, col2 = st.columns(2)
        with col1:
            user_name = st.text_input("ชื่อผู้แจ้ง")
            department = st.selectbox("แผนก", ["MAT", "KD1", "QC", "Office", "Other"]) 
        with col2:
            category = st.selectbox("ประเภทปัญหา", ["Hardware", "Software", "Network", "Account", "Other"])
            
        description = st.text_area("รายละเอียด")
        submitted = st.form_submit_button("ส่งข้อมูล")

        if submitted and user_name and description:
            df_existing = load_data()
            ticket_id = f"IT-{len(df_existing) + 1:04d}"
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            save_ticket(ticket_id, date_str, user_name, department, category, description, "Pending")
            st.success(f"✅ บันทึกสำเร็จ! หมายเลขงานคือ {ticket_id}")

elif page == "💻 จัดการงาน (IT Admin)":
    st.header("Dashboard สำหรับ IT")
    df = load_data()
    
    if df.empty:
        st.info("ยังไม่มีงานในระบบ")
    else:
        st.dataframe(df, use_container_width=True)
        st.divider()
        
        col_a, col_b = st.columns(2)
        with col_a:
            tid = st.selectbox("เลือก Ticket ID", df['id'].tolist())
        with col_b:
            new_st = st.selectbox("สถานะใหม่", ["Pending", "In Progress", "Resolved"])
        
        if st.button("อัปเดตสถานะ"):
            update_ticket_status(tid, new_st)
            st.success("อัปเดตเรียบร้อย!")
            st.rerun()