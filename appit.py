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

def load_table(table_name):
    response = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def insert_data(table_name, data_dict):
    supabase.table(table_name).insert(data_dict).execute()

def update_status(table_name, record_id, new_status):
    supabase.table(table_name).update({"status": new_status}).eq("id", record_id).execute()

def update_ticket_full(record_id, status, assignee, root_cause, solution, cost):
    supabase.table("tickets").update({
        "status": status, "assignee": assignee, "root_cause": root_cause,
        "solution": solution, "cost": cost
    }).eq("id", record_id).execute()

def update_csat(record_id, rating, feedback):
    supabase.table("tickets").update({
        "rating": rating, "feedback": feedback
    }).eq("id", record_id).execute()

def update_pm_full(record_id, status, pm_result):
    supabase.table("pm_schedules").update({
        "status": status, "pm_result": pm_result
    }).eq("id", record_id).execute()

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
        else: st.sidebar.error("Incorrect Password")
else:
    st.sidebar.success("IT Admin Mode Active")
    if st.sidebar.button("Logout"):
        st.session_state.is_admin = False
        st.rerun()

st.sidebar.divider()
st.sidebar.title("🛠️ Menu")
menu_options = ["📝 แจ้งซ่อม (User)", "💻 จัดการงานซ่อม (ช่าง)", "📊 Dashboard", "🗄️ ทะเบียนอุปกรณ์", "🔧 แผนบำรุงรักษา (PM)"] if st.session_state.is_admin else ["📝 แจ้งซ่อม (User)"]
page = st.sidebar.radio("Go to", menu_options)

depts = ["MAT", "KD1", "QC", "Office", "Other"]
ticket_statuses = ["รอตรวจสอบ", "ดำเนินการ", "ส่งซ่อม", "สำเร็จ"]

# ==========================================
# หน้าที่ 1: แจ้งซ่อม & ประเมินผล (User)
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
                uploaded_file = st.file_uploader("แนบรูปภาพ", type=['png', 'jpg', 'jpeg'])
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
            # กรองเฉพาะงานที่สำเร็จ แต่ยังไม่มีคะแนน
            ready_to_rate = df_all[(df_all['status'] == 'สำเร็จ') & (df_all['rating'].isna())]
            if not ready_to_rate.empty:
                selected_job = st.selectbox("เลือกงานซ่อมที่คุณต้องการประเมิน", ready_to_rate['id'].tolist())
                job_info = ready_to_rate[ready_to_rate['id'] == selected_job].iloc[0]
                
                st.info(f"**ช่างผู้ดูแล:** {job_info.get('assignee', 'ไม่ระบุ')} | **วิธีแก้ไข:** {job_info.get('solution', '-')}")
                
                with st.form("csat_form"):
                    rating = st.select_slider("คะแนนความพึงพอใจ (1-5)", options=[1, 2, 3, 4, 5], value=5)
                    feedback = st.text_area("ข้อเสนอแนะเพิ่มเติม")
                    if st.form_submit_button("บันทึกการประเมิน"):
                        update_csat(selected_job, rating, feedback)
                        st.success("ขอบคุณสำหรับคำแนะนำครับ!")
                        st.rerun()
            else:
                st.write("ไม่มีงานซ่อมที่รอการประเมินในขณะนี้")

    st.divider()
    st.subheader("📋 สถานะงานซ่อมปัจจุบัน")
    df_tickets = load_table("tickets")
    if not df_tickets.empty:
        df_view = df_tickets[['id', 'date', 'user', 'category', 'status', 'rating']].copy()
        df_view.rename(columns={'id':'รหัสงาน','date':'วันที่แจ้ง','user':'ผู้แจ้ง','category':'ประเภท','status':'สถานะ','rating':'คะแนน'}, inplace=True)
        st.dataframe(df_view, use_container_width=True, hide_index=True)

# ==========================================
# หน้าที่ 2: จัดการงานซ่อม (ช่าง)
# ==========================================
elif page == "💻 จัดการงานซ่อม (ช่าง)" and st.session_state.is_admin:
    st.header("บันทึกข้อมูลและอัปเดตสถานะงานซ่อม")
    df_tickets = load_table("tickets")
    if not df_tickets.empty:
        st.dataframe(df_tickets[['id', 'date', 'user', 'dept', 'category', 'asset_id', 'urgency', 'status']], use_container_width=True)
        st.divider()
        st.subheader("🔧 อัปเดตรายละเอียดงานและปิดจ๊อบ")
        selected_id = st.selectbox("เลือกรหัสงานที่ต้องการจัดการ", df_tickets['id'].tolist())
        ticket_data = df_tickets[df_tickets['id'] == selected_id].iloc[0]
        
        with st.form("update_ticket_form"):
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"**อาการที่แจ้ง:** {ticket_data['desc']}")
                
                # --- ส่วนแสดงรูปภาพ ---
                img_data = ticket_data.get('image_path', '')
                if img_data and str(img_data).startswith('data:image'):
                    st.image(img_data, caption="รูปภาพประกอบปัญหา", use_container_width=True)
                elif img_data:
                    # กรณีเป็นไฟล์ที่แจ้งซ่อมมาก่อนหน้านี้ (เวอร์ชันเก่าที่บันทึกแค่ชื่อไฟล์)
                    st.caption(f"📎 มีไฟล์แนบ (เวอร์ชันเก่า): {img_data}")
                else:
                    st.caption("ไม่มีรูปภาพแนบ")
                # ----------------------
                
                new_status = st.selectbox("อัปเดตสถานะ", ticket_statuses, index=ticket_statuses.index(ticket_data['status']))
                assignee = st.text_input("ช่างผู้รับผิดชอบ", value=ticket_data.get('assignee', '') if pd.notna(ticket_data.get('assignee')) else '')
            with c2:
                root_cause = st.text_area("สาเหตุของปัญหา", value=ticket_data.get('root_cause', '') if pd.notna(ticket_data.get('root_cause')) else '')
                solution = st.text_area("วิธีการแก้ไข", value=ticket_data.get('solution', '') if pd.notna(ticket_data.get('solution')) else '')
                cost = st.number_input("ค่าซ่อม (บาท)", min_value=0.0, value=float(ticket_data.get('cost', 0.0)) if pd.notna(ticket_data.get('cost')) else 0.0)
                
            if st.form_submit_button("บันทึกข้อมูล"):
                update_ticket_full(selected_id, new_status, assignee, root_cause, solution, cost)
                st.success(f"อัปเดตข้อมูลงาน {selected_id} เรียบร้อย!")
                st.rerun()

# ==========================================
# หน้าที่ 3: สรุปภาพรวม (Dashboard)
# ==========================================
elif page == "📊 Dashboard" and st.session_state.is_admin:
    st.header("สรุปภาพรวมและประสิทธิภาพการบริการ")
    df_tickets = load_table("tickets")
    if not df_tickets.empty:
        # สรุป CSAT
        avg_rating = df_tickets['rating'].mean()
        total_rated = df_tickets['rating'].count()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("งานทั้งหมด", len(df_tickets))
        c2.metric("สำเร็จแล้ว", len(df_tickets[df_tickets['status'] == 'สำเร็จ']))
        c3.metric("คะแนนเฉลี่ย CSAT", f"{avg_rating:.2f} / 5" if not pd.isna(avg_rating) else "-")
        c4.metric("ผู้ประเมิน", f"{total_rated} ท่าน")
        
        st.divider()
        st.subheader("ความคิดเห็นจากผู้ใช้งาน")
        feedback_list = df_tickets[df_tickets['feedback'].notna()][['date', 'user', 'rating', 'feedback']].sort_values(by='date', ascending=False)
        st.dataframe(feedback_list, use_container_width=True, hide_index=True)

# ==========================================
# หน้าที่ 4: ทะเบียนอุปกรณ์ และประวัติการซ่อม (Asset Management)
# ==========================================
elif page == "🗄️ ทะเบียนอุปกรณ์" and st.session_state.is_admin:
    st.header("ทะเบียนอุปกรณ์ และประวัติการซ่อม")
    
    # --- ส่วนที่ 1: ลงทะเบียนอุปกรณ์ใหม่ ---
    with st.expander("➕ ลงทะเบียนอุปกรณ์ใหม่"):
        with st.form("asset_form"):
            a1, a2, a3 = st.columns(3)
            with a1:
                asset_id = st.text_input("รหัสทรัพย์สิน (ID)*")
                asset_type = st.selectbox("ประเภท", ["PC/Laptop", "Printer", "Network", "UPS", "Server", "Other"])
                asset_dept = st.selectbox("ประจำแผนก", depts)
            with a2:
                asset_model = st.text_input("ยี่ห้อ / รุ่น")
                asset_location = st.text_input("สถานที่ติดตั้ง")
            with a3:
                assigned_user = st.text_input("ผู้ใช้งานประจำเครื่อง")
                warranty_expire = st.date_input("วันหมดการรับประกัน")
            
            if st.form_submit_button("บันทึกข้อมูลอุปกรณ์"):
                if asset_id:
                    insert_data("assets", {
                        "id": asset_id, "type": asset_type, "model": asset_model, 
                        "dept": asset_dept, "status": "Active",
                        "location": asset_location, "assigned_user": assigned_user,
                        "warranty_expire": str(warranty_expire)
                    })
                    st.success("✅ ลงทะเบียนอุปกรณ์สำเร็จ")
                    st.rerun()

    # โหลดข้อมูล
    df_assets = load_table("assets")
    df_tickets = load_table("tickets")

    if not df_assets.empty:
        # --- ส่วนที่ 2: ตารางรายการทรัพย์สินทั้งหมด ---
        st.subheader("📋 รายการทรัพย์สินทั้งหมด")
        df_display = df_assets[['id', 'type', 'model', 'assigned_user', 'location', 'warranty_expire', 'status']].copy()
        df_display.rename(columns={
            'id': 'รหัสอุปกรณ์', 'type': 'ประเภท', 'model': 'รุ่น/ยี่ห้อ', 
            'assigned_user': 'ผู้ใช้งาน', 'location': 'สถานที่ตั้ง', 'warranty_expire': 'วันหมดประกัน'
        }, inplace=True)
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # --- ส่วนที่ 3: ระบบเจาะลึกประวัติ (Asset Profile) ---
        st.divider()
        st.subheader("🔍 เจาะลึกประวัติการซ่อมและต้นทุนสะสม")
        
        selected_asset = st.selectbox("เลือกรหัสอุปกรณ์เพื่อดูประวัติอย่างละเอียด", df_assets['id'].tolist())
        
        if selected_asset:
            asset_info = df_assets[df_assets['id'] == selected_asset].iloc[0]
            
            # กรองข้อมูลงานซ่อมที่ตรงกับรหัสอุปกรณ์นี้
            if not df_tickets.empty and 'asset_id' in df_tickets.columns:
                df_history = df_tickets[df_tickets['asset_id'] == selected_asset].copy()
                
                # คำนวณตัวเลขสำคัญ
                total_cost = pd.to_numeric(df_history['cost'], errors='coerce').sum()
                job_count = len(df_history)
                success_jobs = len(df_history[df_history['status'] == 'สำเร็จ'])
                
                # แสดงผลสรุปแบบ Card
                c1, c2, c3 = st.columns(3)
                c1.metric("จำนวนครั้งที่ซ่อม", f"{job_count} ครั้ง")
                c2.metric("ปิดงานสำเร็จ", f"{success_jobs} งาน")
                c3.metric("ยอดค่าซ่อมสะสม", f"฿{total_cost:,.2f}", delta_color="inverse")

                # แสดงตารางประวัติการซ่อมแบบละเอียด
                st.markdown(f"**ประวัติการซ่อมบำรุงของเครื่อง: {selected_asset}**")
                if not df_history.empty:
                    # เลือกคอลัมน์ที่จะแสดงให้ครบตามสเปคช่าง
                    history_display = df_history[['date', 'id', 'user', 'assignee', 'root_cause', 'solution', 'cost', 'status']].copy()
                    
                    # เรียงลำดับเอาวันที่ล่าสุดขึ้นก่อน
                    history_display = history_display.sort_values(by='date', ascending=False)
                    
                    history_display.rename(columns={
                        'date': 'วันที่แจ้ง',
                        'id': 'เลขที่ใบสั่งซ่อม',
                        'user': 'ผู้แจ้งซ่อม',
                        'assignee': 'ช่างผู้รับผิดชอบ',
                        'root_cause': 'สาเหตุของปัญหา',
                        'solution': 'วิธีแก้ไข',
                        'cost': 'ค่าใช้จ่าย (บาท)',
                        'status': 'สถานะ'
                    }, inplace=True)
                    
                    st.dataframe(history_display, use_container_width=True, hide_index=True)
                else:
                    st.success("✨ อุปกรณ์นี้ยังไม่มีประวัติการซ่อม (สภาพใหม่/ยังไม่เคยเสีย)")
            else:
                st.info("ยังไม่มีข้อมูลงานแจ้งซ่อมผูกกับรหัสอุปกรณ์นี้")

# ==========================================
# หน้าที่ 5: แผนบำรุงรักษา (PM) - แบบมี Check List
# ==========================================
elif page == "🔧 แผนบำรุงรักษา (PM)" and st.session_state.is_admin:
    st.header("ระบบแผนงาน Preventive Maintenance (PM)")
    df_assets = load_table("assets")
    asset_options = ["ไม่ระบุ"] + df_assets['id'].tolist() if not df_assets.empty else ["ไม่ระบุ"]

    with st.expander("➕ เพิ่มแผน PM ใหม่"):
        with st.form("pm_form"):
            p1, p2 = st.columns(2)
            with p1:
                pm_name = st.text_input("หัวข้องาน")
                asset_id = st.selectbox("ผูกกับอุปกรณ์ (ถ้ามี)", asset_options)
                assignee = st.text_input("ช่างผู้รับผิดชอบ")
            with p2:
                pm_freq = st.selectbox("ความถี่", ["รายวัน", "รายสัปดาห์", "รายเดือน", "รายไตรมาส", "รายปี"])
                pm_date = st.date_input("วันที่กำหนดทำ (Due Date)")
            checklist = st.text_area("📝 สร้าง Check List การตรวจสอบ (ขึ้นบรรทัดใหม่สำหรับแต่ละข้อ)", placeholder="- ตรวจสอบพัดลม\n- เช็คอุณหภูมิ")
            if st.form_submit_button("บันทึกแผน PM"):
                if pm_name:
                    df_pm = load_table("pm_schedules")
                    pm_id = f"PM-{len(df_pm) + 1:03d}"
                    insert_data("pm_schedules", {
                        "id": pm_id, "task_name": pm_name, "frequency": pm_freq, 
                        "next_due_date": str(pm_date), "status": "Scheduled",
                        "assignee": assignee, "asset_id": asset_id if asset_id != "ไม่ระบุ" else "",
                        "checklist": checklist, "pm_result": ""
                    })
                    st.success("✅ สร้างแผน PM พร้อม Check List เรียบร้อย!")
                    st.rerun()

    df_pm = load_table("pm_schedules")
    if not df_pm.empty:
        st.subheader("📅 ปฏิทิน/ตารางงาน PM")
        df_pm_sorted = df_pm.sort_values(by="next_due_date")
        df_display = df_pm_sorted[['id', 'next_due_date', 'task_name', 'asset_id', 'assignee', 'frequency', 'status']].copy()
        df_display.rename(columns={'id': 'รหัส PM', 'next_due_date': 'กำหนดทำ', 'task_name': 'ชื่องาน', 'asset_id': 'รหัสอุปกรณ์', 'assignee': 'ผู้รับผิดชอบ', 'frequency': 'ความถี่', 'status': 'สถานะ'}, inplace=True)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("✔️ บันทึกผลการทำ PM")
        pending_pms = df_pm[df_pm['status'] != 'Completed']['id'].tolist()
        if pending_pms:
            pm_update_id = st.selectbox("เลือกงาน PM ที่ดำเนินการแล้ว", pending_pms)
            pm_data = df_pm[df_pm['id'] == pm_update_id].iloc[0]
            c_info, c_check = st.columns(2)
            with c_info: st.info(f"**ชื่องาน:** {pm_data['task_name']}\n\n**อุปกรณ์:** {pm_data.get('asset_id', '-')}\n\n**ช่าง:** {pm_data.get('assignee', '-')}")
            with c_check: st.warning(f"**รายการ Check List ที่ต้องทำ:**\n\n{pm_data.get('checklist', 'ไม่มี Check List')}")
            
            with st.form("pm_result_form"):
                pm_new_st = st.selectbox("อัปเดตสถานะงาน", ["Scheduled", "Completed", "Overdue"], index=1)
                pm_result = st.text_area("บันทึกผลการตรวจสอบ", value=pm_data.get('pm_result', '') if pd.notna(pm_data.get('pm_result')) else '')
                if st.form_submit_button("บันทึกผลการทำ PM"):
                    update_pm_full(pm_update_id, pm_new_st, pm_result)
                    st.success("บันทึกผล PM และปิดจ๊อบเรียบร้อย!")
                    st.rerun()
        else:
            st.success("🎉 เยี่ยมมาก! ไม่มีงาน PM ค้างอยู่ในระบบเลย")
