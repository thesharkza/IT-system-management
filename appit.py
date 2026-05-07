import streamlit as st
import pandas as pd
import base64
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

def update_status(table_name, record_id, new_status):
    supabase.table(table_name).update({"status": new_status}).eq("id", record_id).execute()

def update_ticket_full(record_id, status, assignee, root_cause, solution, cost):
    supabase.table("tickets").update({
        "status": status, "assignee": assignee, "root_cause": root_cause,
        "solution": solution, "cost": cost
    }).eq("id", record_id).execute()

def update_pm_full(record_id, status, pm_result):
    supabase.table("pm_schedules").update({
        "status": status, "pm_result": pm_result
    }).eq("id", record_id).execute()

# ==========================================
# ระบบ LOGIN
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
        "📝 แจ้งซ่อม (User)", "💻 จัดการงานซ่อม (ช่าง)", 
        "📊 Dashboard", "🗄️ ทะเบียนอุปกรณ์", "🔧 แผนบำรุงรักษา (PM)"
    ]
else:
    menu_options = ["📝 แจ้งซ่อม (User)"]

page = st.sidebar.radio("เลือกหน้าต่างการทำงาน", menu_options)
depts = ["MAT", "KD1", "QC", "Office", "Other"]
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
            asset_id_input = st.text_input("รหัสอุปกรณ์ (เช่น PC-001) *ถ้ามี") 
            urgency = st.selectbox("ระดับความเร่งด่วน", ["ปกติ", "ด่วน", "ด่วนมาก"])
            uploaded_file = st.file_uploader("แนบไฟล์รูปภาพปัญหา (ถ้ามี)", type=['png', 'jpg', 'jpeg'])
            
        description = st.text_area("รายละเอียดปัญหา")
        submitted = st.form_submit_button("ส่งเรื่องแจ้งซ่อม")

        if submitted and user_name and description:
            df_existing = load_table("tickets")
            ticket_id = f"JOB-{len(df_existing) + 1:04d}"
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # แปลงไฟล์รูปภาพเป็น Base64 เพื่อเก็บลง Database (ถ้ามีการแนบไฟล์)
            if uploaded_file is not None:
                img_bytes = uploaded_file.getvalue()
                encoded_img = base64.b64encode(img_bytes).decode('utf-8')
                image_data = f"data:{uploaded_file.type};base64,{encoded_img}"
            else:
                image_data = ""
            
            insert_data("tickets", {
                "id": ticket_id, "date": date_str, "user": user_name, 
                "dept": department, "category": category, "desc": description, 
                "status": "รอตรวจสอบ", "urgency": urgency, "image_path": image_data,
                "asset_id": asset_id_input 
            })
            st.success(f"✅ บันทึกสำเร็จ! หมายเลขงาน: {ticket_id}")
            st.rerun()

    st.divider()
    st.subheader("📋 ตรวจสอบสถานะงานซ่อม")
    df_tickets = load_table("tickets")
    if not df_tickets.empty:
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
    st.header("สถิติและประสิทธิภาพการทำงาน")
    df_tickets = load_table("tickets")
    if not df_tickets.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("งานทั้งหมด", len(df_tickets))
        col2.metric("สำเร็จแล้ว", len(df_tickets[df_tickets['status'] == 'สำเร็จ']))
        col3.metric("รอตรวจสอบ", len(df_tickets[df_tickets['status'] == 'รอตรวจสอบ']))
        st.divider()
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.subheader("จำนวนงานแยกตามแผนก")
            st.bar_chart(df_tickets['dept'].value_counts())
        with col_chart2:
            st.subheader("จำนวนงานแยกตามประเภท")
            st.bar_chart(df_tickets['category'].value_counts())

# ==========================================
# หน้าที่ 4: ทะเบียนอุปกรณ์ (Assets)
# ==========================================
elif page == "🗄️ ทะเบียนอุปกรณ์" and st.session_state.is_admin:
    st.header("ทะเบียนอุปกรณ์ และประวัติการซ่อม")
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
                        "id": asset_id, "type": asset_type, "model": asset_model, "dept": asset_dept, "status": "Active",
                        "location": asset_location, "assigned_user": assigned_user, "warranty_expire": str(warranty_expire)
                    })
                    st.success("✅ ลงทะเบียนอุปกรณ์สำเร็จ")
                    st.rerun()

    df_assets = load_table("assets")
    if not df_assets.empty:
        st.subheader("📋 รายการทรัพย์สินทั้งหมด")
        df_display = df_assets[['id', 'type', 'model', 'assigned_user', 'location', 'warranty_expire', 'status']].copy()
        df_display.rename(columns={'id': 'รหัสอุปกรณ์', 'type': 'ประเภท', 'model': 'รุ่น', 'assigned_user': 'ผู้ใช้งาน', 'location': 'สถานที่ตั้ง', 'warranty_expire': 'วันหมดประกัน'}, inplace=True)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("🔍 ตรวจสอบประวัติการซ่อมและต้นทุน")
        selected_asset = st.selectbox("เลือกรหัสอุปกรณ์เพื่อดูประวัติ", df_assets['id'].tolist())
        if selected_asset:
            asset_info = df_assets[df_assets['id'] == selected_asset].iloc[0]
            df_tickets = load_table("tickets")
            if not df_tickets.empty and 'asset_id' in df_tickets.columns:
                df_asset_history = df_tickets[df_tickets['asset_id'] == selected_asset]
                total_repair_cost = pd.to_numeric(df_asset_history['cost'], errors='coerce').sum()
                c_info, c_stat1, c_stat2 = st.columns([2, 1, 1])
                with c_info: st.info(f"**รุ่น:** {asset_info['model']} | **ผู้ใช้:** {asset_info['assigned_user']} | **หมดประกัน:** {asset_info['warranty_expire']}")
                with c_stat1: st.metric("จำนวนครั้งที่ซ่อม", f"{len(df_asset_history)} ครั้ง")
                with c_stat2: st.metric("ยอดค่าซ่อมสะสม", f"฿{total_repair_cost:,.2f}")

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
