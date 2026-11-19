"""
Scheduled Report Script
ส่งรายงานสรุป Telegram ตามเวลา (เรียกจาก GitHub Actions)

วิธีใช้ (ทดสอบใน local):
  python scripts/scheduled_report.py daily
  python scripts/scheduled_report.py weekly
  python scripts/scheduled_report.py pm_overdue

Environment variables ที่ต้องตั้ง (ใน GitHub Secrets):
  SUPABASE_URL
  SUPABASE_KEY
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
"""
import os
import sys
import requests
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from supabase import create_client

# ── Read env ──
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
TG_TOKEN     = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

if not all([SUPABASE_URL, SUPABASE_KEY, TG_TOKEN, TG_CHAT_ID]):
    print("❌ Missing env vars (SUPABASE_URL, SUPABASE_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Keep-alive ping — ยืดอายุ Supabase free tier (ป้องกัน auto-pause) ──
def _keepalive():
    """ยิง query เล็กๆ ไว้ให้ Supabase รู้ว่า project ยัง active"""
    try:
        supabase.table("tickets").select("id").limit(1).execute()
    except Exception as e:
        print(f"⚠️  Keep-alive failed (project อาจ pause): {e}")

# ── Helpers ──
def _esc(t):
    if t is None: return "—"
    s = str(t)
    for ch in ['_','*','`','[']:
        s = s.replace(ch, '\\' + ch)
    return s

def send_tg(message, silent=False):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_notification": silent,
        "disable_web_page_preview": True
    }, timeout=10)
    print(f"Status: {r.status_code} | {r.text[:200]}")
    return r.status_code == 200

def load_df(table):
    res = supabase.table(table).select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

# ── Reports ──
def daily_report():
    df = load_df("tickets")
    df_pm = load_df("pm_schedules")
    today_str = datetime.now().strftime("%d %b %Y")
    if df.empty:
        return send_tg(f"📊 *รายงานประจำวัน — {today_str}*\nยังไม่มีข้อมูลในระบบ")
    pending = len(df[df['status'] == 'รอตรวจสอบ'])
    inprog  = len(df[df['status'] == 'ดำเนินการ'])
    sending = len(df[df['status'] == 'ส่งซ่อม'])
    done    = len(df[df['status'] == 'สำเร็จ'])
    urgent  = len(df[(df['status'] != 'สำเร็จ') & (df['urgency'] == 'ด่วนมาก')])

    pm_txt = ""
    if not df_pm.empty:
        df_pm['_due'] = pd.to_datetime(df_pm['next_due_date']).dt.date
        today_d = datetime.now().date()
        tomorrow_d = today_d + relativedelta(days=1)
        overdue  = df_pm[(df_pm['_due'] < today_d) & (df_pm['status'] != 'Completed')]
        upcoming = df_pm[((df_pm['_due'] == today_d) | (df_pm['_due'] == tomorrow_d)) & (df_pm['status'] != 'Completed')]
        if len(overdue) > 0 or len(upcoming) > 0:
            pm_txt = f"\n🔧 *PM:* เลยกำหนด {len(overdue)} | ใกล้ครบ {len(upcoming)}"

    urgent_txt = f"\n🚨 *งานด่วนมากค้าง:* {urgent}" if urgent > 0 else ""

    msg = (
        f"📊 *รายงานสรุปประจำวัน*\n"
        f"📅 {today_str}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔴 *รอตรวจสอบ:* {pending}\n"
        f"🟡 *ดำเนินการ:* {inprog}\n"
        f"🟣 *ส่งซ่อม:* {sending}\n"
        f"🟢 *สำเร็จ:* {done}"
        f"{urgent_txt}"
        f"{pm_txt}"
    )
    return send_tg(msg, silent=True)

def weekly_report():
    df = load_df("tickets")
    today_d = datetime.now().date()
    week_ago = today_d + relativedelta(days=-7)
    if df.empty:
        return send_tg("📈 *รายงานประจำสัปดาห์*\nยังไม่มีข้อมูล")
    df['_date'] = pd.to_datetime(df['date']).dt.date
    df_week = df[df['_date'] >= week_ago]
    total_week = len(df_week)
    done_week  = len(df_week[df_week['status'] == 'สำเร็จ'])
    rate = (done_week/total_week*100) if total_week > 0 else 0
    avg_csat = df_week['rating'].mean() if 'rating' in df_week.columns else None
    csat_txt = f"\n⭐ *คะแนนเฉลี่ย:* {avg_csat:.2f}/5.0" if pd.notna(avg_csat) else ""
    total_cost = pd.to_numeric(df_week['cost'], errors='coerce').sum()
    top_dept = df_week['dept'].value_counts().head(3) if not df_week.empty else None
    dept_txt = ""
    if top_dept is not None and len(top_dept) > 0:
        dept_txt = "\n\n🏢 *Top แผนกที่แจ้งซ่อม:*\n" + "\n".join(
            [f"  • {_esc(d)}: {n} งาน" for d, n in top_dept.items()]
        )
    msg = (
        f"📈 *รายงานสรุปประจำสัปดาห์*\n"
        f"📅 {week_ago.strftime('%d %b')} → {today_d.strftime('%d %b %Y')}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *งานทั้งหมด:* {total_week}\n"
        f"✅ *ปิดงานสำเร็จ:* {done_week} ({rate:.1f}%)\n"
        f"💰 *ค่าซ่อมรวม:* {total_cost:,.2f} บาท"
        f"{csat_txt}"
        f"{dept_txt}"
    )
    return send_tg(msg, silent=True)

def pm_overdue_report():
    df_pm = load_df("pm_schedules")
    if df_pm.empty:
        print("ไม่มีข้อมูล PM"); return True
    df_pm['_due'] = pd.to_datetime(df_pm['next_due_date']).dt.date
    today_d = datetime.now().date()
    overdue = df_pm[(df_pm['_due'] < today_d) & (df_pm['status'] != 'Completed')].sort_values('_due')
    if overdue.empty:
        print("ไม่มี PM เลยกำหนด"); return True
    items = ""
    for _, ov in overdue.head(10).iterrows():
        days = (today_d - ov['_due']).days
        items += f"\n• `{_esc(ov.get('task_name','—'))[:40]}` — เลย {days} วัน ({_esc(ov.get('assignee','—'))})"
    more = f"\n\n_...และอีก {len(overdue)-10} งาน_" if len(overdue) > 10 else ""
    msg = (
        f"🚨 *แจ้งเตือน PM เลยกำหนด*\n"
        f"📅 {datetime.now().strftime('%d %b %Y')}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"พบงาน PM เลยกำหนด *{len(overdue)} รายการ*\n"
        f"{items}{more}"
    )
    return send_tg(msg, silent=False)

# ── Main ──
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    print(f"▶ Running: {mode}")
    # ping Supabase ก่อนทุกครั้งเพื่อป้องกัน auto-pause (free tier)
    _keepalive()
    if mode == "daily":       ok = daily_report()
    elif mode == "weekly":    ok = weekly_report()
    elif mode == "pm_overdue":ok = pm_overdue_report()
    else:
        print(f"❌ Unknown mode: {mode}"); sys.exit(1)
    sys.exit(0 if ok else 1)
