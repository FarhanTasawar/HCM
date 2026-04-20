"""
main.py — Cortex Flow HR Management System
Flask Web App | SQLite | Windows + Android + iPhone
Run: python main.py
"""

from flask import (Flask, render_template_string, request, redirect,
                   url_for, session, flash, jsonify, make_response)
import database as db
import calendar, base64, os, io
from datetime import date, datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "CortexFlow_2025_S3cr3t#Key"

# ─────────────────────────────────────────────────────────────────
# DECORATORS
# ─────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def dec(*a, **k):
        if "user" not in session: return redirect(url_for("login"))
        return f(*a, **k)
    return dec

def admin_only(f):
    @wraps(f)
    def dec(*a, **k):
        if "user" not in session: return redirect(url_for("login"))
        if session["user"]["role"] != "admin": return redirect(url_for("emp_dashboard"))
        return f(*a, **k)
    return dec

# ─────────────────────────────────────────────────────────────────
# SHARED HTML BASE
# ─────────────────────────────────────────────────────────────────
CSS = """
<style>
:root{
  --navy:#0F2A4A; --blue:#1565C0; --accent:#2196F3;
  --success:#2E7D32; --warn:#E65100; --danger:#C62828;
  --bg:#EEF2F7; --card:#fff; --text:#1A202C; --muted:#64748B;
  --border:#CBD5E0; --sidebar:230px;
}
*{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',Arial,sans-serif;}
body{background:var(--bg);color:var(--text);min-height:100vh;}
a{text-decoration:none;color:inherit;}

/* ── Top Bar ── */
.topbar{
  background:linear-gradient(135deg,var(--navy) 0%,#1a3a5c 100%);
  color:#fff;height:58px;display:flex;align-items:center;
  justify-content:space-between;padding:0 20px;
  position:sticky;top:0;z-index:1000;
  box-shadow:0 2px 12px rgba(0,0,0,.35);
}
.topbar .brand{display:flex;align-items:center;gap:10px;font-size:20px;font-weight:900;letter-spacing:.5px;}
.topbar .brand .dot{width:10px;height:10px;background:var(--accent);border-radius:50%;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.6;transform:scale(.8)}}
.topbar .right{display:flex;align-items:center;gap:14px;font-size:13px;}
.topbar .user-chip{background:rgba(255,255,255,.12);padding:6px 14px;border-radius:20px;
  display:flex;align-items:center;gap:7px;}
.topbar .logout-btn{background:rgba(231,76,60,.8);color:#fff;border:none;padding:6px 14px;
  border-radius:6px;cursor:pointer;font-size:12px;font-weight:700;}

/* ── Layout ── */
.layout{display:flex;min-height:calc(100vh - 58px);}

/* ── Sidebar ── */
.sidebar{
  width:var(--sidebar);background:var(--navy);
  min-height:calc(100vh - 58px);padding:12px 0;
  flex-shrink:0;position:sticky;top:58px;
  height:calc(100vh - 58px);overflow-y:auto;
}
.sidebar .section-label{
  font-size:10px;font-weight:800;color:#4A6FA5;letter-spacing:1.5px;
  padding:14px 18px 5px;text-transform:uppercase;
}
.sidebar a{
  display:flex;align-items:center;gap:10px;
  padding:11px 18px;color:#94A3B8;font-size:13px;font-weight:500;
  border-left:3px solid transparent;transition:.15s;
}
.sidebar a:hover{background:rgba(255,255,255,.06);color:#fff;border-left-color:var(--accent);}
.sidebar a.active{background:rgba(33,150,243,.15);color:#64B5F6;
  border-left-color:var(--accent);font-weight:700;}
.sidebar .ico{font-size:16px;width:22px;text-align:center;}

/* ── Content ── */
.content{flex:1;padding:22px;overflow-x:hidden;}

/* ── Page header ── */
.page-header{display:flex;align-items:center;justify-content:space-between;
  margin-bottom:20px;flex-wrap:wrap;gap:10px;}
.page-header h1{font-size:22px;font-weight:800;color:var(--navy);display:flex;align-items:center;gap:8px;}
.page-header .sub{font-size:12px;color:var(--muted);margin-top:2px;}

/* ── KPI Cards ── */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-bottom:22px;}
.kpi{background:var(--card);border-radius:12px;padding:18px;
  border:1px solid var(--border);position:relative;overflow:hidden;}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:var(--kcolor,var(--accent));}
.kpi .k-label{font-size:11px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:.8px;}
.kpi .k-value{font-size:32px;font-weight:900;color:var(--navy);margin:4px 0;}
.kpi .k-sub{font-size:11px;color:var(--muted);}
.kpi .k-icon{position:absolute;right:14px;top:50%;transform:translateY(-50%);font-size:32px;opacity:.15;}

/* ── Cards ── */
.card{background:var(--card);border-radius:12px;border:1px solid var(--border);
  padding:20px;margin-bottom:18px;}
.card-header{display:flex;align-items:center;justify-content:space-between;
  margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--border);}
.card-title{font-size:15px;font-weight:800;color:var(--navy);display:flex;align-items:center;gap:8px;}

/* ── Tables ── */
.tbl-wrap{overflow-x:auto;border-radius:8px;border:2px solid #1A202C;}
table{width:100%;border-collapse:collapse;font-size:13px;background:var(--card);}
thead tr{background:var(--navy);}
th{color:#fff;padding:10px 12px;text-align:left;font-weight:700;font-size:12px;
  border-right:1px solid rgba(255,255,255,.15);white-space:nowrap;}
th:last-child{border-right:none;}
td{padding:9px 12px;border-bottom:1px solid #E2E8F0;border-right:1px solid #E2E8F0;
  vertical-align:middle;}
td:last-child{border-right:none;}
tbody tr:nth-child(even) td{background:#F8FAFC;}
tbody tr:hover td{background:#EFF6FF;}
tfoot tr td{background:#F1F5F9;font-weight:700;border-top:2px solid var(--navy);}

/* ── Status badges ── */
.badge{padding:3px 10px;border-radius:14px;font-size:11px;font-weight:800;
  display:inline-block;white-space:nowrap;letter-spacing:.3px;}
.b-present{background:#E8F5E9;color:#1B5E20;border:1px solid #A5D6A7;}
.b-late{background:#FFF3E0;color:#E65100;border:1px solid #FFCC80;}
.b-absent{background:#FFEBEE;color:#B71C1C;border:1px solid #EF9A9A;}
.b-leave{background:#F3E5F5;color:#6A1B9A;border:1px solid #CE93D8;}
.b-halfday{background:#E3F2FD;color:#0D47A1;border:1px solid #90CAF9;}
.b-pending{background:#FFF8E1;color:#F57F17;border:1px solid #FFE082;}
.b-approved{background:#E8F5E9;color:#2E7D32;border:1px solid #A5D6A7;}
.b-rejected{background:#FFEBEE;color:#C62828;border:1px solid #EF9A9A;}

/* ── Attendance color rows ── */
.row-present td{background:#F0FFF4 !important;}
.row-late td{background:#FFFBEB !important;}
.row-absent td{background:#FFF5F5 !important;}
.row-leave td{background:#FAF5FF !important;}

/* ── Forms ── */
.form-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;}
.form-group{display:flex;flex-direction:column;gap:5px;}
.form-group label{font-size:11px;font-weight:800;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;}
.form-group input,.form-group select,.form-group textarea{
  border:1.5px solid var(--border);border-radius:8px;padding:10px 13px;
  font-size:13px;background:#fff;color:var(--text);outline:none;width:100%;
}
.form-group input:focus,.form-group select:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(33,150,243,.12);}
.form-group input[readonly]{background:#F8FAFC;cursor:default;}

/* ── Buttons ── */
.btn{display:inline-flex;align-items:center;gap:7px;padding:9px 20px;border:none;
  border-radius:8px;font-size:13px;font-weight:700;cursor:pointer;transition:.15s;white-space:nowrap;}
.btn-primary{background:var(--accent);color:#fff;}
.btn-primary:hover{background:#1976D2;}
.btn-success{background:var(--success);color:#fff;}
.btn-success:hover{background:#1B5E20;}
.btn-danger{background:var(--danger);color:#fff;}
.btn-danger:hover{background:#B71C1C;}
.btn-warn{background:var(--warn);color:#fff;}
.btn-warn:hover{background:#BF360C;}
.btn-gray{background:#607D8B;color:#fff;}
.btn-gray:hover{background:#455A64;}
.btn-sm{padding:5px 12px;font-size:11px;border-radius:6px;}
.btn-outline{background:transparent;border:1.5px solid var(--accent);color:var(--accent);}
.btn-outline:hover{background:var(--accent);color:#fff;}

/* ── Toolbar ── */
.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:16px;}
.toolbar form{display:flex;flex-wrap:wrap;gap:8px;align-items:center;}
.toolbar select,.toolbar input[type=text],.toolbar input[type=date]{
  border:1.5px solid var(--border);border-radius:7px;padding:8px 12px;font-size:13px;
  background:#fff;outline:none;
}

/* ── Alerts ── */
.alert{padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:16px;
  font-weight:600;display:flex;align-items:center;gap:10px;}
.alert-success{background:#E8F5E9;color:#2E7D32;border-left:4px solid var(--success);}
.alert-danger{background:#FFEBEE;color:#B71C1C;border-left:4px solid var(--danger);}
.alert-warning{background:#FFF8E1;color:#E65100;border-left:4px solid var(--warn);}
.alert-info{background:#E3F2FD;color:#0D47A1;border-left:4px solid var(--accent);}

/* ── Check-In Panel ── */
.ci-panel{text-align:center;padding:30px 20px;}
.ci-clock{font-size:58px;font-weight:900;color:var(--navy);line-height:1;
  font-variant-numeric:tabular-nums;}
.ci-date{font-size:15px;color:var(--muted);margin:6px 0 18px;}
.ci-duty{background:#EFF6FF;color:var(--blue);padding:7px 20px;
  border-radius:20px;font-size:13px;font-weight:700;display:inline-block;margin-bottom:20px;
  border:1px solid #BFDBFE;}
.ci-btns{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-top:10px;}
.ci-btn{font-size:17px;padding:16px 36px;border-radius:12px;min-width:180px;justify-content:center;}

/* ── Camera box ── */
.cam-box{background:#0a0a1a;border-radius:10px;overflow:hidden;position:relative;
  max-width:320px;margin:0 auto 14px;}
.cam-box video,.cam-box canvas{width:100%;display:block;border-radius:10px;}
.cam-overlay{position:absolute;bottom:0;left:0;right:0;background:rgba(0,0,0,.4);
  padding:8px;text-align:center;color:#fff;font-size:11px;}

/* ── Payslip ── */
.payslip{max-width:640px;margin:0 auto;border:2px solid var(--navy);border-radius:12px;overflow:hidden;}
.payslip-head{background:var(--navy);color:#fff;padding:24px;text-align:center;}
.payslip-head h2{font-size:24px;font-weight:900;letter-spacing:1px;}
.payslip-head .sub{font-size:13px;opacity:.7;margin-top:4px;}
.payslip-meta{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:18px 20px;
  background:#F8FAFC;border-bottom:1px solid var(--border);}
.payslip-meta .m-item{font-size:13px;}
.payslip-meta .m-item b{color:var(--navy);display:block;font-size:11px;text-transform:uppercase;}
.ps-table{width:100%;}
.ps-table td{padding:10px 20px;border-bottom:1px solid #EDF2F7;font-size:13px;}
.ps-table .ps-total{background:#F0FFF4;font-weight:900;font-size:16px;color:var(--success);
  border-top:2px solid var(--navy);}
.ps-table .ps-deduct{color:var(--danger);}
.ps-table .ps-gross{background:#EFF6FF;font-weight:700;color:var(--blue);}

/* ── Attendance grid ── */
.att-grid th,.att-grid td{font-size:11px;padding:5px 4px;text-align:center;
  border:1px solid #CBD5E0;}
.att-grid td:first-child{text-align:left;font-size:12px;font-weight:600;
  white-space:nowrap;min-width:120px;}
.att-grid .cell-P{background:#C8E6C9;color:#1B5E20;font-weight:700;}
.att-grid .cell-A{background:#FFCDD2;color:#B71C1C;font-weight:700;}
.att-grid .cell-L{background:#FFF9C4;color:#F57F17;font-weight:700;}
.att-grid .cell-T{background:#FFE0B2;color:#E65100;font-weight:700;}
.att-grid .cell-H{background:#E3F2FD;color:#0D47A1;font-weight:700;}

/* ── Mobile bottom nav ── */
.mobile-nav{display:none;position:fixed;bottom:0;left:0;right:0;
  background:var(--navy);z-index:500;border-top:1px solid rgba(255,255,255,.1);}
.mobile-nav a{display:flex;flex-direction:column;align-items:center;gap:3px;
  padding:10px 6px;color:#64748B;font-size:10px;flex:1;}
.mobile-nav a.active{color:#64B5F6;}
.mobile-nav .m-ico{font-size:20px;}

/* ── Misc ── */
.divider{height:1px;background:var(--border);margin:16px 0;}
.text-right{text-align:right!important;}
.text-center{text-align:center!important;}
.fw-bold{font-weight:800!important;}
.color-success{color:var(--success)!important;}
.color-danger{color:var(--danger)!important;}
.color-warn{color:var(--warn)!important;}
.photo-thumb{width:48px;height:48px;object-fit:cover;border-radius:6px;
  border:2px solid var(--border);cursor:pointer;}
.no-data{text-align:center;padding:30px;color:var(--muted);font-size:14px;}

/* ── Responsive ── */
@media(max-width:900px){
  :root{--sidebar:0px;}
  .sidebar{display:none;}
  .content{padding:14px;padding-bottom:72px;}
  .kpi-grid{grid-template-columns:repeat(2,1fr);}
  .ci-clock{font-size:44px;}
  .mobile-nav{display:flex;}
  .form-grid{grid-template-columns:1fr;}
}
@media print{
  .topbar,.sidebar,.toolbar,.mobile-nav,.no-print{display:none!important;}
  body,.layout,.content{background:#fff;padding:0;margin:0;}
  .card{border:none;box-shadow:none;padding:0;}
}
</style>
"""

def base_layout(content: str, active: str = "", page_title: str = "Dashboard",
                is_admin: bool = True) -> str:
    user    = session.get("user", {})
    role    = user.get("role","employee")
    name    = user.get("name", user.get("employee_id",""))
    is_adm  = role == "admin"

    admin_nav = f"""
    <div class="section-label">Main</div>
    <a href="/dashboard" class="{'active' if active=='dashboard' else ''}"><span class="ico">📊</span> Dashboard</a>
    <a href="/employees" class="{'active' if active=='employees' else ''}"><span class="ico">👥</span> Employees</a>
    <div class="section-label">Attendance</div>
    <a href="/attendance" class="{'active' if active=='attendance' else ''}"><span class="ico">📋</span> Monthly Grid</a>
    <a href="/attendance/manual" class="{'active' if active=='att-manual' else ''}"><span class="ico">✏️</span> Manual Entry</a>
    <div class="section-label">Payroll</div>
    <a href="/payroll" class="{'active' if active=='payroll' else ''}"><span class="ico">💰</span> Payroll</a>
    <div class="section-label">Leave</div>
    <a href="/leaves" class="{'active' if active=='leaves' else ''}"><span class="ico">📅</span> Leave Requests</a>
    <a href="/leaves/types" class="{'active' if active=='leave-types' else ''}"><span class="ico">⚙️</span> Leave Config</a>
    <div class="section-label">Reports</div>
    <a href="/reports" class="{'active' if active=='reports' else ''}"><span class="ico">📈</span> Reports</a>
    <div class="section-label">Admin</div>
    <a href="/admin/settings" class="{'active' if active=='settings' else ''}"><span class="ico">🔧</span> Settings</a>
    """

    emp_nav = f"""
    <div class="section-label">My Menu</div>
    <a href="/emp/dashboard" class="{'active' if active=='emp-dashboard' else ''}"><span class="ico">🏠</span> Home</a>
    <a href="/emp/attendance" class="{'active' if active=='emp-att' else ''}"><span class="ico">📋</span> My Attendance</a>
    <a href="/emp/leave" class="{'active' if active=='emp-leave' else ''}"><span class="ico">📅</span> Apply Leave</a>
    <a href="/emp/payslip" class="{'active' if active=='emp-pay' else ''}"><span class="ico">💰</span> My Payslip</a>
    """

    mobile_admin = f"""
    <a href="/dashboard" class="{'active' if active=='dashboard' else ''}"><span class="m-ico">📊</span>Home</a>
    <a href="/employees" class="{'active' if active=='employees' else ''}"><span class="m-ico">👥</span>Staff</a>
    <a href="/attendance" class="{'active' if active=='attendance' else ''}"><span class="m-ico">📋</span>Attend</a>
    <a href="/payroll" class="{'active' if active=='payroll' else ''}"><span class="m-ico">💰</span>Payroll</a>
    <a href="/reports" class="{'active' if active=='reports' else ''}"><span class="m-ico">📈</span>Reports</a>
    """
    mobile_emp = f"""
    <a href="/emp/dashboard" class="{'active' if active=='emp-dashboard' else ''}"><span class="m-ico">🏠</span>Home</a>
    <a href="/emp/attendance" class="{'active' if active=='emp-att' else ''}"><span class="m-ico">📋</span>Attend</a>
    <a href="/emp/leave" class="{'active' if active=='emp-leave' else ''}"><span class="m-ico">📅</span>Leave</a>
    <a href="/emp/payslip" class="{'active' if active=='emp-pay' else ''}"><span class="m-ico">💰</span>Payslip</a>
    """

    flashes = ""
    # Flask flash messages injected by render helper

    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<meta name="theme-color" content="#0F2A4A">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>Cortex Flow – {page_title}</title>
{CSS}
</head><body>
<div class="topbar">
  <div class="brand"><div class="dot"></div> Cortex Flow</div>
  <div class="right">
    <div class="user-chip">
      {'👑' if is_adm else '👤'} <b>{name}</b>
    </div>
    <form action="/logout" method="POST" style="margin:0;">
      <button class="logout-btn" type="submit">Logout</button>
    </form>
  </div>
</div>
<div class="layout">
  <nav class="sidebar">
    {''+admin_nav if is_adm else emp_nav}
  </nav>
  <div class="content">
    {content}
  </div>
</div>
<nav class="mobile-nav">
  {''+mobile_admin if is_adm else mobile_emp}
</nav>
<script>
function liveClock(){{
  var el=document.getElementById('live-clock');
  if(el)el.textContent=new Date().toLocaleTimeString('en-PK',{{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:true}});
}}
setInterval(liveClock,1000); liveClock();
</script>
</body></html>"""


def render_page(content: str, active: str = "", page_title: str = ""):
    from flask import get_flashed_messages
    msgs  = get_flashed_messages(with_categories=True)
    alert = ""
    for cat, msg in msgs:
        alert += f'<div class="alert alert-{cat}">{"✅" if cat=="success" else "⚠️" if cat=="warning" else "❌"} {msg}</div>'
    user   = session.get("user",{})
    is_adm = user.get("role","employee") == "admin"
    return base_layout(alert + content, active, page_title, is_adm)


# ═══════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════════════════════════════════
LOGIN_HTML = """<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0F2A4A">
<title>Cortex Flow – Login</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',Arial,sans-serif;}
body{background:linear-gradient(135deg,#0F2A4A 0%,#1565C0 100%);
  min-height:100vh;display:flex;align-items:center;justify-content:center;padding:16px;}
.box{background:#fff;border-radius:18px;width:100%;max-width:400px;
  box-shadow:0 25px 70px rgba(0,0,0,.4);overflow:hidden;}
.top{background:linear-gradient(135deg,#0F2A4A,#1565C0);padding:36px 28px;text-align:center;color:#fff;}
.brand{font-size:26px;font-weight:900;letter-spacing:1px;margin-bottom:4px;}
.brand .dot{display:inline-block;width:10px;height:10px;background:#2196F3;
  border-radius:50%;margin-right:8px;}
.tagline{font-size:13px;opacity:.7;}
.form{padding:32px 28px;}
.form label{display:block;font-size:11px;font-weight:800;color:#64748B;
  text-transform:uppercase;letter-spacing:.6px;margin-bottom:5px;}
.form input{width:100%;border:1.5px solid #CBD5E0;border-radius:9px;padding:12px 15px;
  font-size:14px;outline:none;margin-bottom:14px;}
.form input:focus{border-color:#2196F3;box-shadow:0 0 0 3px rgba(33,150,243,.12);}
.btn{width:100%;background:linear-gradient(135deg,#1565C0,#2196F3);color:#fff;
  border:none;border-radius:9px;padding:14px;font-size:15px;font-weight:800;
  cursor:pointer;letter-spacing:.5px;}
.btn:hover{background:linear-gradient(135deg,#0D47A1,#1976D2);}
.err{background:#FFEBEE;color:#C62828;border-radius:8px;padding:10px 14px;
  font-size:13px;margin-bottom:14px;font-weight:600;border-left:4px solid #C62828;}
.hint{text-align:center;font-size:11px;color:#94A3B8;margin-top:16px;}
</style></head><body>
<div class="box">
  <div class="top">
    <div class="brand"><span class="dot"></span>Cortex Flow</div>
    <div class="tagline">HR Management System</div>
  </div>
  <div class="form">
    {error_block}
    <form method="POST">
      <label>Employee / Admin ID</label>
      <input name="emp_id" placeholder="Enter your ID" required autofocus>
      <label>Password</label>
      <input name="password" type="password" placeholder="Enter your password" required>
      <button class="btn" type="submit">🔐 &nbsp; Sign In</button>
    </form>
    <div class="hint">Default admin: ADMIN001 / admin123</div>
  </div>
</div>
</body></html>"""

@app.route("/", methods=["GET","POST"])
@app.route("/login", methods=["GET","POST"])
def login():
    error = ""
    if request.method == "POST":
        eid = request.form.get("emp_id","").strip()
        pwd = request.form.get("password","")
        user = db.authenticate(eid, pwd)
        if user:
            emp = db.get_employee(eid)
            session["user"] = {
                "employee_id": user["employee_id"],
                "name": emp["name"] if emp else user["employee_id"],
                "role": user["role"]
            }
            return redirect("/dashboard" if user["role"]=="admin" else "/emp/dashboard")
        error = "Invalid ID or password. Please try again."
    err_block = f'<div class="err">❌ {error}</div>' if error else ""
    return LOGIN_HTML.replace("{error_block}", err_block)

@app.route("/logout", methods=["POST","GET"])
def logout():
    session.clear()
    return redirect("/login")


# ═══════════════════════════════════════════════════════════════════
# ADMIN – DASHBOARD
# ═══════════════════════════════════════════════════════════════════
@app.route("/dashboard")
@admin_only
def dashboard():
    stats   = db.get_dashboard_stats()
    att     = db.get_today_all_attendance()
    emps    = db.get_all_employees()
    not_marked = {e["employee_id"] for e in emps} - {r["employee_id"] for r in att}

    rows_html = ""
    for i, r in enumerate(att, 1):
        late_h = f"{r['late_minutes']//60}h {r['late_minutes']%60}m" if r.get("late_minutes") else "—"
        status_badge = {
            "present":f'<span class="badge b-present">✅ Present</span>',
            "late":   f'<span class="badge b-late">⏰ Late</span>',
            "absent": f'<span class="badge b-absent">❌ Absent</span>',
            "leave":  f'<span class="badge b-leave">🏖 Leave</span>',
        }.get(r.get("status","absent"), f'<span class="badge b-absent">❌ Absent</span>')
        row_cls = {"present":"row-present","late":"row-late","absent":"row-absent","leave":"row-leave"}.get(r.get("status",""),"")
        photo = f'<img src="/photo/{r["employee_id"]}/{r["att_date"]}/in" class="photo-thumb" onerror="this.style.display=\'none\'">' if r.get("photo_in") else "—"
        loc = f'<a href="https://maps.google.com/?q={r["location_in"]}" target="_blank" style="font-size:11px;color:#1565C0;">📍 Map</a>' if r.get("location_in") else "—"
        rows_html += f"""<tr class="{row_cls}">
            <td class="text-center">{i}</td>
            <td><b>{r.get('emp_name',r['employee_id'])}</b></td>
            <td>{r['employee_id']}</td>
            <td>{r.get('designation','—')}</td>
            <td>{r.get('check_in','—')}</td>
            <td>{r.get('check_out','—')}</td>
            <td>{status_badge}</td>
            <td class="text-center">{late_h}</td>
            <td class="text-center">{photo}</td>
            <td class="text-center">{loc}</td>
        </tr>"""

    for eid in list(not_marked)[:20]:
        emp = next((e for e in emps if e["employee_id"]==eid), None)
        if emp:
            rows_html += f"""<tr class="row-absent">
                <td class="text-center">—</td>
                <td><b>{emp['name']}</b></td>
                <td>{emp['employee_id']}</td>
                <td>{emp.get('designation','—')}</td>
                <td>—</td><td>—</td>
                <td><span class="badge b-absent">❌ Not Marked</span></td>
                <td class="text-center">—</td>
                <td class="text-center">—</td>
                <td class="text-center">—</td>
            </tr>"""

    content = f"""
<div class="page-header">
  <div>
    <h1>📊 Dashboard</h1>
    <div class="sub">Welcome back, {session['user']['name']} | {date.today().strftime('%A, %d %B %Y')}</div>
  </div>
</div>
<div class="kpi-grid">
  <div class="kpi" style="--kcolor:#1565C0"><span class="k-icon">👥</span>
    <div class="k-label">Total Employees</div>
    <div class="k-value">{stats['total']}</div>
    <div class="k-sub">Active staff</div>
  </div>
  <div class="kpi" style="--kcolor:#2E7D32"><span class="k-icon">✅</span>
    <div class="k-label">Present Today</div>
    <div class="k-value">{stats['present']}</div>
    <div class="k-sub">Checked in</div>
  </div>
  <div class="kpi" style="--kcolor:#C62828"><span class="k-icon">❌</span>
    <div class="k-label">Absent Today</div>
    <div class="k-value">{stats['absent']}</div>
    <div class="k-sub">Not present</div>
  </div>
  <div class="kpi" style="--kcolor:#E65100"><span class="k-icon">⏰</span>
    <div class="k-label">Late Arrivals</div>
    <div class="k-value">{stats['late']}</div>
    <div class="k-sub">Today</div>
  </div>
  <div class="kpi" style="--kcolor:#6A1B9A"><span class="k-icon">🏖</span>
    <div class="k-label">On Leave</div>
    <div class="k-value">{stats['on_leave']}</div>
    <div class="k-sub">Today</div>
  </div>
  <div class="kpi" style="--kcolor:#F57F17"><span class="k-icon">📋</span>
    <div class="k-label">Pending Leaves</div>
    <div class="k-value">{stats['pending_leaves']}</div>
    <div class="k-sub">Awaiting approval</div>
  </div>
</div>
<div class="card">
  <div class="card-header">
    <div class="card-title">📋 Today's Attendance — {date.today().strftime('%d %B %Y')}</div>
    <span style="font-size:12px;color:var(--muted);">Sorted by check-in time</span>
  </div>
  <div class="tbl-wrap">
  <table>
    <thead><tr>
      <th>#</th><th>Employee Name</th><th>Employee ID</th><th>Designation</th>
      <th>Check In</th><th>Check Out</th><th>Status</th>
      <th>Late</th><th>Photo</th><th>Location</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  </div>
</div>"""
    return render_page(content, "dashboard", "Dashboard")


# ═══════════════════════════════════════════════════════════════════
# ADMIN – EMPLOYEES
# ═══════════════════════════════════════════════════════════════════
@app.route("/employees")
@admin_only
def employees():
    emps = db.get_all_employees()
    q    = request.args.get("q","").lower()
    if q:
        emps = [e for e in emps if q in e["name"].lower() or q in e["employee_id"].lower()
                or q in e.get("department","").lower() or q in e.get("designation","").lower()]

    # Group by designation
    from collections import defaultdict
    grouped = defaultdict(list)
    for e in emps:
        grouped[e.get("designation","—")].append(e)

    rows = ""
    serial = 1
    for desig, emp_list in sorted(grouped.items()):
        rows += f'<tr><td colspan="9" style="background:#EFF6FF;font-weight:800;color:#1565C0;padding:8px 12px;border-top:2px solid #BFDBFE;">📂 {desig} ({len(emp_list)} employees)</td></tr>'
        for e in emp_list:
            rows += f"""<tr>
              <td class="text-center">{serial}</td>
              <td><b>{e['name']}</b></td>
              <td>{e['employee_id']}</td>
              <td>{e.get('designation','—')}</td>
              <td>{e.get('department','—')}</td>
              <td>{e.get('organization','—')}</td>
              <td>PKR {e.get('salary',0):,.0f}</td>
              <td>{e.get('duty_start','09:00')} – {e.get('duty_end','17:00')}</td>
              <td style="white-space:nowrap;">
                <a href="/employees/edit/{e['employee_id']}" class="btn btn-primary btn-sm">✏️ Edit</a>
                <a href="/employees/resign/{e['employee_id']}"
                   onclick="return confirm('Resign {e['name']}? This cannot be undone.')"
                   class="btn btn-danger btn-sm">🚪 Resign</a>
              </td>
            </tr>"""
            serial += 1

    content = f"""
<div class="page-header">
  <h1>👥 Employees</h1>
  <a href="/employees/add" class="btn btn-success">➕ Add Employee</a>
</div>
<div class="toolbar">
  <form method="GET">
    <input type="text" name="q" placeholder="🔍 Search name, ID, dept…" value="{q}" style="width:260px;">
    <button class="btn btn-primary btn-sm" type="submit">Search</button>
    {'<a href="/employees" class="btn btn-gray btn-sm">Clear</a>' if q else ''}
  </form>
  <span style="font-size:12px;color:var(--muted);">{len(emps)} employees found | Grouped by designation</span>
</div>
<div class="card">
  <div class="tbl-wrap">
  <table>
    <thead><tr>
      <th>#</th><th>Name</th><th>Employee ID</th><th>Designation</th>
      <th>Department</th><th>Organization</th><th>Salary</th>
      <th>Duty Time</th><th>Actions</th>
    </tr></thead>
    <tbody>{rows if rows else '<tr><td colspan="9" class="no-data">No employees found.</td></tr>'}</tbody>
  </table>
  </div>
</div>"""
    return render_page(content, "employees", "Employees")


EMP_FORM_FIELDS = """
<div class="form-grid">
  <div class="form-group">
    <label>Employee ID *</label>
    <input name="employee_id" value="{employee_id}" required
           {readonly} placeholder="e.g. EMP001">
  </div>
  <div class="form-group">
    <label>Full Name *</label>
    <input name="name" value="{name}" required placeholder="Full Name">
  </div>
  <div class="form-group">
    <label>Organization *</label>
    <input name="organization" list="org-list" value="{organization}" placeholder="e.g. Acme Corp">
    <datalist id="org-list">{org_options}</datalist>
  </div>
  <div class="form-group">
    <label>Department</label>
    <input name="department" list="dept-list" value="{department}" placeholder="e.g. IT">
    <datalist id="dept-list">{dept_options}</datalist>
  </div>
  <div class="form-group">
    <label>Designation</label>
    <input name="designation" list="desig-list" value="{designation}" placeholder="e.g. Engineer">
    <datalist id="desig-list">{desig_options}</datalist>
  </div>
  <div class="form-group">
    <label>Gross Salary (PKR) *</label>
    <input name="salary" type="number" value="{salary}" required placeholder="50000">
  </div>
  <div class="form-group">
    <label>Joining Date</label>
    <input name="joining_date" type="date" value="{joining_date}">
  </div>
  <div class="form-group">
    <label>Phone</label>
    <input name="phone" value="{phone}" placeholder="+92-xxx-xxxxxxx">
  </div>
  <div class="form-group">
    <label>Email</label>
    <input name="email" type="email" value="{email}" placeholder="email@company.com">
  </div>
  <div class="form-group">
    <label>Duty Start Time</label>
    <input name="duty_start" type="time" value="{duty_start}">
  </div>
  <div class="form-group">
    <label>Duty End Time</label>
    <input name="duty_end" type="time" value="{duty_end}">
  </div>
  <div class="form-group">
    <label>Password {pw_label}</label>
    <input name="password" type="password" {pw_required} placeholder="{pw_placeholder}">
  </div>
  <div class="form-group" style="grid-column:1/-1;">
    <label>Address</label>
    <input name="address" value="{address}" placeholder="Home Address">
  </div>
</div>
<div style="margin-top:18px;display:flex;gap:10px;flex-wrap:wrap;">
  <button class="btn btn-success" type="submit">💾 Save Employee</button>
  <a href="/employees" class="btn btn-gray">Cancel</a>
</div>
"""

def build_emp_form(emp=None, title="", action=""):
    orgs   = "".join(f"<option>{o}</option>" for o in db.get_organizations())
    depts  = "".join(f"<option>{d}</option>" for d in db.get_departments())
    desigs = "".join(f"<option>{d}</option>" for d in db.get_designations())
    e = emp or {}
    is_edit = bool(e.get("employee_id"))
    fields = EMP_FORM_FIELDS.format(
        employee_id=e.get("employee_id",""),
        name=e.get("name",""), organization=e.get("organization",""),
        department=e.get("department",""), designation=e.get("designation",""),
        salary=e.get("salary",""), joining_date=e.get("joining_date", date.today().isoformat()),
        phone=e.get("phone",""), email=e.get("email",""),
        duty_start=e.get("duty_start","09:00"), duty_end=e.get("duty_end","17:00"),
        address=e.get("address",""),
        readonly='readonly style="background:#F8FAFC"' if is_edit else "",
        org_options=orgs, dept_options=depts, desig_options=desigs,
        pw_label="(leave blank to keep)" if is_edit else "*",
        pw_required="" if is_edit else "required",
        pw_placeholder="Set login password" if not is_edit else "Change password (optional)"
    )
    return f"""
<div class="page-header"><h1>{title}</h1></div>
<div class="card">
  <form method="POST" action="{action}">{fields}</form>
</div>"""

@app.route("/employees/add", methods=["GET","POST"])
@admin_only
def emp_add():
    if request.method == "POST":
        try:
            db.add_employee(request.form.to_dict())
            flash("Employee added successfully!", "success")
            return redirect("/employees")
        except Exception as ex:
            flash(str(ex), "danger")
    content = build_emp_form(title="➕ Add New Employee", action="/employees/add")
    return render_page(content, "employees", "Add Employee")

@app.route("/employees/edit/<eid>", methods=["GET","POST"])
@admin_only
def emp_edit(eid):
    emp = db.get_employee(eid) or {}
    if request.method == "POST":
        data = request.form.to_dict()
        if not data.get("password"): data.pop("password", None)
        db.update_employee(eid, data)
        flash("Employee updated successfully.", "success")
        return redirect("/employees")
    content = build_emp_form(emp=emp, title=f"✏️ Edit — {emp.get('name',eid)}", action=f"/employees/edit/{eid}")
    return render_page(content, "employees", "Edit Employee")

@app.route("/employees/resign/<eid>")
@admin_only
def emp_resign(eid):
    db.resign_employee(eid)
    flash(f"Employee {eid} marked as resigned.", "warning")
    return redirect("/employees")


# ═══════════════════════════════════════════════════════════════════
# ATTENDANCE PHOTO ENDPOINT
# ═══════════════════════════════════════════════════════════════════
@app.route("/photo/<eid>/<att_date>/<which>")
@login_required
def get_photo(eid, att_date, which):
    if session["user"]["role"] != "admin" and session["user"]["employee_id"] != eid:
        return "", 403
    b64 = db.get_attendance_photo(eid, att_date, which)
    if not b64:
        return "", 404
    try:
        img_data = base64.b64decode(b64)
        resp = make_response(img_data)
        resp.headers["Content-Type"] = "image/jpeg"
        resp.headers["Cache-Control"] = "max-age=3600"
        return resp
    except Exception:
        return "", 404


# ═══════════════════════════════════════════════════════════════════
# ADMIN – ATTENDANCE MONTHLY GRID
# ═══════════════════════════════════════════════════════════════════
@app.route("/attendance")
@admin_only
def attendance():
    year  = int(request.args.get("year",  date.today().year))
    month = int(request.args.get("month", date.today().month))
    emps  = db.get_all_employees()
    recs  = db.get_all_attendance_month(year, month)
    days  = calendar.monthrange(year, month)[1]
    months_sel = "".join(
        f'<option value="{i}" {"selected" if i==month else ""}>{calendar.month_name[i]}</option>'
        for i in range(1,13))
    years_sel = "".join(
        f'<option {"selected" if y==year else ""}>{y}</option>'
        for y in range(2023, date.today().year+2))

    lookup = {}
    for r in recs:
        s = r.get("status","absent")
        code = {"present":"P","late":"T","absent":"A","leave":"L","half-day":"H"}.get(s,"A")
        lookup.setdefault(r["employee_id"], {})[r["att_date"]] = code

    header_days = "".join(f"<th>{d}</th>" for d in range(1, days+1))
    rows_html   = ""
    for emp in emps:
        eid  = emp["employee_id"]
        P=A=L=T=H=0
        cells = ""
        for d in range(1, days+1):
            dstr = f"{year}-{month:02d}-{d:02d}"
            code = lookup.get(eid,{}).get(dstr,"")
            cls  = {"P":"cell-P","A":"cell-A","L":"cell-L","T":"cell-T","H":"cell-H"}.get(code,"")
            cells += f'<td class="{cls}">{code}</td>'
            if code=="P": P+=1
            elif code=="A": A+=1
            elif code=="L": L+=1
            elif code=="T": T+=1;P+=1
            elif code=="H": H+=1
        rows_html += f"""<tr>
          <td><b>{emp['name']}</b><br><span style="font-size:10px;color:var(--muted);">{emp['employee_id']}</span></td>
          {cells}
          <td class="fw-bold color-success">{P}</td>
          <td class="fw-bold color-danger">{A}</td>
          <td class="fw-bold" style="color:#6A1B9A">{L}</td>
          <td class="fw-bold color-warn">{T}</td>
          <td class="fw-bold" style="color:#0D47A1">{H}</td>
        </tr>"""

    content = f"""
<div class="page-header">
  <h1>📋 Monthly Attendance Grid</h1>
  <a href="/attendance/manual" class="btn btn-warn">✏️ Manual Entry</a>
</div>
<div class="toolbar">
  <form method="GET" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
    <select name="year">{years_sel}</select>
    <select name="month">{months_sel}</select>
    <button class="btn btn-primary" type="submit">📅 Load</button>
  </form>
  <div style="display:flex;gap:8px;font-size:11px;flex-wrap:wrap;">
    <span style="background:#C8E6C9;padding:2px 8px;border-radius:4px;border:1px solid #A5D6A7;">P=Present</span>
    <span style="background:#FFCDD2;padding:2px 8px;border-radius:4px;border:1px solid #EF9A9A;">A=Absent</span>
    <span style="background:#FFF9C4;padding:2px 8px;border-radius:4px;border:1px solid #FFE082;">L=Leave</span>
    <span style="background:#FFE0B2;padding:2px 8px;border-radius:4px;border:1px solid #FFCC80;">T=Late</span>
    <span style="background:#E3F2FD;padding:2px 8px;border-radius:4px;border:1px solid #90CAF9;">H=Half-Day</span>
  </div>
</div>
<div class="card">
  <div class="card-title">📅 {calendar.month_name[month]} {year}</div>
  <div class="tbl-wrap">
  <table class="att-grid">
    <thead><tr>
      <th style="text-align:left;min-width:140px;">Employee</th>
      {header_days}
      <th>P</th><th>A</th><th>L</th><th>T</th><th>H</th>
    </tr></thead>
    <tbody>{rows_html if rows_html else '<tr><td colspan="40" class="no-data">No employees found.</td></tr>'}</tbody>
  </table>
  </div>
</div>"""
    return render_page(content, "attendance", "Attendance Grid")


@app.route("/attendance/manual", methods=["GET","POST"])
@admin_only
def manual_attendance():
    emps = db.get_all_employees()
    if request.method == "POST":
        db.mark_manual_attendance(
            employee_id=request.form["employee_id"],
            att_date=request.form["att_date"],
            status=request.form["status"],
            check_in=request.form.get("check_in",""),
            check_out=request.form.get("check_out",""),
            note=request.form.get("note","")
        )
        flash("Attendance saved successfully.", "success")
        return redirect("/attendance")

    opts = "".join(f'<option value="{e["employee_id"]}">{e["name"]} ({e["employee_id"]})</option>'
                   for e in emps)
    content = f"""
<div class="page-header"><h1>✏️ Manual Attendance Entry</h1></div>
<div class="card" style="max-width:540px;">
  <form method="POST">
    <div class="form-grid" style="grid-template-columns:1fr;">
      <div class="form-group">
        <label>Employee</label>
        <select name="employee_id" required><option value="">-- Select Employee --</option>{opts}</select>
      </div>
      <div class="form-group">
        <label>Date</label>
        <input name="att_date" type="date" value="{date.today().isoformat()}" required>
      </div>
      <div class="form-group">
        <label>Status</label>
        <select name="status">
          <option>present</option><option>absent</option>
          <option>leave</option><option>half-day</option>
        </select>
      </div>
      <div class="form-group">
        <label>Check-In Time</label>
        <input name="check_in" type="time" value="09:00">
      </div>
      <div class="form-group">
        <label>Check-Out Time</label>
        <input name="check_out" type="time" value="17:00">
      </div>
      <div class="form-group">
        <label>Note (optional)</label>
        <input name="note" placeholder="Any note about this entry">
      </div>
    </div>
    <div style="margin-top:16px;display:flex;gap:10px;">
      <button class="btn btn-success" type="submit">💾 Save</button>
      <a href="/attendance" class="btn btn-gray">Cancel</a>
    </div>
  </form>
</div>"""
    return render_page(content, "att-manual", "Manual Attendance")


# ═══════════════════════════════════════════════════════════════════
# ADMIN – PAYROLL
# ═══════════════════════════════════════════════════════════════════
@app.route("/payroll")
@admin_only
def payroll():
    year  = int(request.args.get("year",  date.today().year))
    month = int(request.args.get("month", date.today().month))
    rows  = db.get_all_payroll_month(year, month)
    months_sel = "".join(
        f'<option value="{i}" {"selected" if i==month else ""}>{calendar.month_name[i]}</option>'
        for i in range(1,13))
    years_sel = "".join(
        f'<option {"selected" if y==year else ""}>{y}</option>'
        for y in range(2023, date.today().year+2))

    trows = ""
    for r in rows:
        trows += f"""<tr>
          <td><b>{r.get('employee_name','')}</b></td>
          <td>{r['employee_id']}</td>
          <td>{r.get('designation','—')}</td>
          <td class="text-center">{r['working_days']}</td>
          <td class="text-center fw-bold color-success">{r['present_days']}</td>
          <td class="text-center fw-bold color-danger">{r['absent_days']}</td>
          <td class="text-center" style="color:#6A1B9A">{r['leave_days']}</td>
          <td class="text-center color-warn">{r['late_minutes']}</td>
          <td class="text-right">PKR {r['gross_salary']:,.0f}</td>
          <td class="text-right color-danger">PKR {r['total_deduct']:,.0f}</td>
          <td class="text-right fw-bold color-success" style="font-size:14px;">PKR {r['net_salary']:,.0f}</td>
          <td class="text-center">
            <a href="/payroll/slip/{r['employee_id']}/{year}/{month}" target="_blank"
               class="btn btn-primary btn-sm">🧾 Slip</a>
          </td>
        </tr>"""

    content = f"""
<div class="page-header">
  <h1>💰 Payroll Management</h1>
</div>
<div class="toolbar">
  <form method="GET" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
    <select name="year">{years_sel}</select>
    <select name="month">{months_sel}</select>
    <button class="btn btn-primary" type="submit">📅 Load</button>
    <a href="/payroll/generate?year={year}&month={month}"
       onclick="return confirm('Generate payroll for all employees for {calendar.month_name[month]} {year}?')"
       class="btn btn-warn">⚙️ Generate All</a>
  </form>
</div>
<div class="card">
  <div class="card-header">
    <div class="card-title">💰 {calendar.month_name[month]} {year} — Payroll</div>
    <span style="font-size:12px;color:var(--muted);">{len(rows)} records</span>
  </div>
  <div class="tbl-wrap">
  <table>
    <thead><tr>
      <th>Name</th><th>ID</th><th>Designation</th><th>Days</th>
      <th>Present</th><th>Absent</th><th>Leave</th><th>Late(min)</th>
      <th>Gross</th><th>Deductions</th><th>Net Salary</th><th>Action</th>
    </tr></thead>
    <tbody>{trows if trows else '<tr><td colspan="12" class="no-data">No payroll data. Click "Generate All" first.</td></tr>'}</tbody>
  </table>
  </div>
</div>"""
    return render_page(content, "payroll", "Payroll")


@app.route("/payroll/generate")
@admin_only
def payroll_generate():
    year  = int(request.args.get("year",  date.today().year))
    month = int(request.args.get("month", date.today().month))
    count = 0
    for emp in db.get_all_employees():
        try:
            db.generate_payroll(emp["employee_id"], year, month)
            count += 1
        except Exception:
            pass
    flash(f"Payroll generated for {count} employees — {calendar.month_name[month]} {year}.", "success")
    return redirect(f"/payroll?year={year}&month={month}")


@app.route("/payroll/slip/<eid>/<int:year>/<int:month>")
@login_required
def payslip(eid, year, month):
    if session["user"]["role"] != "admin" and session["user"]["employee_id"] != eid:
        return redirect("/emp/payslip")
    pr = db.get_payroll(eid, year, month)
    if not pr:
        return "<h2 style='padding:40px;color:#C62828;font-family:Arial'>No payroll found. Ask admin to generate payroll.</h2>"
    mn = calendar.month_name[pr["month"]]
    return f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Payslip – {pr.get('employee_name','')}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',Arial,sans-serif;}}
body{{background:#f0f4f8;padding:20px;}}
.wrap{{max-width:620px;margin:auto;}}
.ps{{background:#fff;border:2px solid #0F2A4A;border-radius:12px;overflow:hidden;}}
.ps-head{{background:linear-gradient(135deg,#0F2A4A,#1565C0);color:#fff;padding:26px;text-align:center;}}
.ps-head h2{{font-size:24px;font-weight:900;letter-spacing:1px;}}
.ps-head p{{opacity:.75;font-size:13px;margin-top:5px;}}
.ps-meta{{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:18px 20px;
  background:#F8FAFC;border-bottom:2px solid #0F2A4A;}}
.ps-meta .m{{font-size:13px;}} .ps-meta .m b{{color:#0F2A4A;font-size:10px;text-transform:uppercase;display:block;}}
.ps-body table{{width:100%;border-collapse:collapse;}}
.ps-body td{{padding:11px 20px;border-bottom:1px solid #EDF2F7;font-size:13px;}}
.ps-body tr:last-child td{{border-bottom:none;}}
.row-gross{{background:#EFF6FF;font-weight:700;color:#1565C0;}}
.row-deduct{{color:#C62828;}}
.row-total-d{{background:#FFF5F5;color:#C62828;font-weight:800;}}
.row-net{{background:#0F2A4A;color:#fff;font-size:17px;font-weight:900;border-top:2px solid #0F2A4A;}}
.print-btn{{display:block;text-align:center;margin:16px auto;background:#1565C0;color:#fff;
  border:none;padding:13px 32px;border-radius:8px;font-size:14px;font-weight:800;cursor:pointer;}}
@media print{{.print-btn{{display:none;}}body{{background:#fff;padding:0;}}}}
</style></head><body>
<div class="wrap">
<div class="ps">
  <div class="ps-head"><h2>SALARY PAYSLIP</h2><p>{mn} {pr['year']} | Cortex Flow HR</p></div>
  <div class="ps-meta">
    <div class="m"><b>Employee ID</b>{pr['employee_id']}</div>
    <div class="m"><b>Name</b>{pr.get('employee_name','—')}</div>
    <div class="m"><b>Designation</b>{pr.get('designation','—')}</div>
    <div class="m"><b>Department</b>{pr.get('department','—')}</div>
    <div class="m"><b>Organization</b>{pr.get('organization','—')}</div>
    <div class="m"><b>Generated</b>{pr.get('generated_at','—')}</div>
  </div>
  <div class="ps-body">
  <table>
    <tr><td>Working Days</td><td style="text-align:right">{pr['working_days']}</td></tr>
    <tr><td>Present Days</td><td style="text-align:right;color:#2E7D32;font-weight:700">{pr['present_days']}</td></tr>
    <tr><td>Absent Days</td><td style="text-align:right;color:#C62828">{pr['absent_days']}</td></tr>
    <tr><td>Leave Days</td><td style="text-align:right">{pr['leave_days']}</td></tr>
    <tr><td>Late Count</td><td style="text-align:right">{pr['late_count']} times ({pr['late_minutes']} min)</td></tr>
    <tr class="row-gross"><td>Gross Salary</td><td style="text-align:right">PKR {pr['gross_salary']:,.2f}</td></tr>
    <tr class="row-deduct"><td>Absent Deduction</td><td style="text-align:right">– PKR {pr['absent_deduct']:,.2f}</td></tr>
    <tr class="row-deduct"><td>Late Penalty</td><td style="text-align:right">– PKR {pr['late_deduct']:,.2f}</td></tr>
    <tr><td>Bonus</td><td style="text-align:right;color:#2E7D32">+ PKR {pr.get('bonus',0):,.2f}</td></tr>
    <tr class="row-total-d"><td><b>Total Deductions</b></td><td style="text-align:right"><b>– PKR {pr['total_deduct']:,.2f}</b></td></tr>
    <tr class="row-net"><td>NET SALARY</td><td style="text-align:right">PKR {pr['net_salary']:,.2f}</td></tr>
  </table>
  </div>
</div>
<button class="print-btn" onclick="window.print()">🖨️ Print Payslip</button>
</div></body></html>"""


# ═══════════════════════════════════════════════════════════════════
# ADMIN – LEAVES
# ═══════════════════════════════════════════════════════════════════
@app.route("/leaves")
@admin_only
def leaves():
    status_f = request.args.get("status","pending")
    reqs = db.get_leave_requests(status=status_f if status_f != "all" else None)
    tabs = "".join(
        f'<a href="/leaves?status={s}" class="btn {"btn-primary" if status_f==s else "btn-outline"} btn-sm">{s.title()}</a>'
        for s in ["all","pending","approved","rejected"])

    rows = ""
    for r in reqs:
        rows += f"""<tr>
          <td><b>{r.get('emp_name','')}</b><br><span style="font-size:10px;color:var(--muted);">{r['employee_id']}</span></td>
          <td>{r['leave_type']}</td>
          <td>{r['from_date']}</td><td>{r['to_date']}</td>
          <td class="text-center">{r['days']}</td>
          <td>{r.get('reason','—')}</td>
          <td><span class="badge b-{r['status']}">{r['status'].title()}</span></td>
          <td style="white-space:nowrap;">
            {f'<a href="/leaves/approve/{r["id"]}" class="btn btn-success btn-sm">✅ Approve</a> <a href="/leaves/reject/{r["id"]}" class="btn btn-danger btn-sm">❌ Reject</a>' if r['status']=='pending' else '—'}
          </td>
        </tr>"""

    content = f"""
<div class="page-header"><h1>📅 Leave Requests</h1></div>
<div class="toolbar">{tabs}</div>
<div class="card">
  <div class="tbl-wrap"><table>
    <thead><tr><th>Employee</th><th>Leave Type</th><th>From</th><th>To</th>
      <th>Days</th><th>Reason</th><th>Status</th><th>Action</th></tr></thead>
    <tbody>{rows if rows else '<tr><td colspan="8" class="no-data">No leave requests.</td></tr>'}</tbody>
  </table></div>
</div>"""
    return render_page(content, "leaves", "Leave Requests")


@app.route("/leaves/approve/<int:rid>")
@admin_only
def leave_approve(rid):
    db.approve_leave(rid)
    flash("Leave approved and attendance updated.", "success")
    return redirect("/leaves")

@app.route("/leaves/reject/<int:rid>")
@admin_only
def leave_reject(rid):
    db.reject_leave(rid)
    flash("Leave request rejected.", "warning")
    return redirect("/leaves")


@app.route("/leaves/types", methods=["GET","POST"])
@admin_only
def leave_types():
    emps = db.get_all_employees()
    lts  = db.get_leave_types()
    yr   = date.today().year

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_type":
            db.add_leave_type(request.form["name"], request.form.get("desc",""))
            flash("Leave type added.", "success")
        elif action == "set_alloc":
            db.set_leave_allocation(
                request.form["employee_id"],
                request.form["leave_type"],
                int(request.form["year"]),
                int(request.form["days"])
            )
            flash("Leave allocation saved.", "success")
        return redirect("/leaves/types")

    lt_opts  = "".join(f"<option>{t}</option>" for t in lts)
    emp_opts = "".join(f'<option value="{e["employee_id"]}">{e["name"]}</option>' for e in emps)
    lt_rows  = "".join(
        f"<tr><td>{t}</td><td><a href=\"{url_for('delete_leave_type', lt=t)}\" onclick=\"return confirm('Delete?')\" class='btn btn-danger btn-sm'>Delete</a></td></tr>"
        for t in lts)

    content = f"""
<div class="page-header"><h1>⚙️ Leave Configuration</h1></div>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px;">
  <div class="card">
    <div class="card-title">➕ Add Leave Type</div>
    <form method="POST">
      <input type="hidden" name="action" value="add_type">
      <div class="form-group" style="margin-bottom:10px;">
        <label>Leave Type Name</label>
        <input name="name" placeholder="e.g. Maternity Leave" required>
      </div>
      <div class="form-group" style="margin-bottom:12px;">
        <label>Description</label>
        <input name="desc" placeholder="Brief description">
      </div>
      <button class="btn btn-success" type="submit">Add Type</button>
    </form>
    <div class="divider"></div>
    <div class="tbl-wrap"><table>
      <thead><tr><th>Leave Type</th><th>Action</th></tr></thead>
      <tbody>{lt_rows}</tbody>
    </table></div>
  </div>
  <div class="card">
    <div class="card-title">🎯 Set Leave Allocation per Employee</div>
    <form method="POST">
      <input type="hidden" name="action" value="set_alloc">
      <div class="form-group" style="margin-bottom:10px;">
        <label>Employee</label>
        <select name="employee_id" required><option value="">-- Select --</option>{emp_opts}</select>
      </div>
      <div class="form-group" style="margin-bottom:10px;">
        <label>Leave Type</label>
        <select name="leave_type" required><option value="">-- Select --</option>{lt_opts}</select>
      </div>
      <div class="form-group" style="margin-bottom:10px;">
        <label>Year</label>
        <input name="year" type="number" value="{yr}" required>
      </div>
      <div class="form-group" style="margin-bottom:12px;">
        <label>Total Days Allowed</label>
        <input name="days" type="number" min="0" value="10" required>
      </div>
      <button class="btn btn-success" type="submit">Save Allocation</button>
    </form>
  </div>
</div>"""
    return render_page(content, "leave-types", "Leave Config")


@app.route("/leaves/types/delete/<lt>")
@admin_only
def delete_leave_type(lt):
    db.delete_leave_type(lt)
    flash("Leave type deleted.", "success")
    return redirect("/leaves/types")


# ═══════════════════════════════════════════════════════════════════
# ADMIN – REPORTS
# ╔══════════════════════════════════════════════════════════════════
@app.route("/reports")
@admin_only
def reports():
    year  = int(request.args.get("year",  date.today().year))
    month = int(request.args.get("month", date.today().month))
    eid   = request.args.get("emp_id","all")
    emps  = db.get_all_employees()
    recs  = db.get_all_attendance_month(year, month)
    if eid != "all":
        recs = [r for r in recs if r["employee_id"] == eid]

    months_sel = "".join(
        f'<option value="{i}" {"selected" if i==month else ""}>{calendar.month_name[i]}</option>'
        for i in range(1,13))
    years_sel = "".join(
        f'<option {"selected" if y==year else ""}>{y}</option>'
        for y in range(2023, date.today().year+2))
    emp_opts = f'<option value="all" {"selected" if eid=="all" else ""}>-- All Employees --</option>'
    emp_opts += "".join(
        f'<option value="{e["employee_id"]}" {"selected" if e["employee_id"]==eid else ""}>{e["name"]}</option>'
        for e in emps)

    rows = ""
    for i, r in enumerate(recs, 1):
        late_str = f"{r.get('late_minutes',0)} min" if r.get('late_minutes') else "—"
        loc_str  = f'<a href="https://maps.google.com/?q={r["location_in"]}" target="_blank" style="color:#1565C0;font-size:11px;">📍 View</a>' if r.get("location_in") else "—"
        photo_in  = f'<img src="/photo/{r["employee_id"]}/{r["att_date"]}/in" class="photo-thumb" onerror="this.style.display=\'none\'">' if r.get("photo_in") else "—"
        status_b  = f'<span class="badge b-{r.get("status","absent")}">{r.get("status","—").upper()}</span>'
        row_cls   = {"present":"row-present","late":"row-late","absent":"row-absent","leave":"row-leave"}.get(r.get("status",""),"")
        rows += f"""<tr class="{row_cls}">
          <td>{i}</td><td>{r['att_date']}</td>
          <td><b>{r.get('emp_name','')}</b></td>
          <td>{r['employee_id']}</td>
          <td>{r.get('check_in','—')}</td>
          <td>{r.get('check_out','—')}</td>
          <td>{status_b}</td>
          <td>{late_str}</td>
          <td>{photo_in}</td>
          <td>{loc_str}</td>
        </tr>"""

    content = f"""
<div class="page-header"><h1>📈 Attendance Reports</h1></div>
<div class="toolbar">
  <form method="GET" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
    <select name="emp_id">{emp_opts}</select>
    <select name="year">{years_sel}</select>
    <select name="month">{months_sel}</select>
    <button class="btn btn-primary" type="submit">📊 Generate</button>
  </form>
  <span style="font-size:12px;color:var(--muted);">{len(recs)} records</span>
</div>
<div class="card">
  <div class="card-title">📋 {calendar.month_name[month]} {year}</div>
  <div class="tbl-wrap"><table>
    <thead><tr>
      <th>#</th><th>Date</th><th>Employee</th><th>ID</th>
      <th>Check-In</th><th>Check-Out</th><th>Status</th>
      <th>Late</th><th>Photo</th><th>Location</th>
    </tr></thead>
    <tbody>{rows if rows else '<tr><td colspan="10" class="no-data">No records found.</td></tr>'}</tbody>
  </table></div>
</div>"""
    return render_page(content, "reports", "Reports")


# ═══════════════════════════════════════════════════════════════════
# ADMIN – SETTINGS
# ═══════════════════════════════════════════════════════════════════
@app.route("/admin/settings", methods=["GET","POST"])
@admin_only
def admin_settings():
    if request.method == "POST":
        old = request.form.get("old_password","")
        new = request.form.get("new_password","")
        confirm = request.form.get("confirm_password","")
        if new != confirm:
            flash("New passwords do not match.", "danger")
        elif len(new) < 6:
            flash("Password must be at least 6 characters.", "danger")
        elif db.change_admin_password(old, new):
            flash("Admin password changed successfully.", "success")
        else:
            flash("Old password is incorrect.", "danger")
        return redirect("/admin/settings")

    content = """
<div class="page-header"><h1>🔧 Admin Settings</h1></div>
<div class="card" style="max-width:460px;">
  <div class="card-title">🔒 Change Admin Password</div>
  <form method="POST">
    <div class="form-group" style="margin-bottom:12px;">
      <label>Current Password</label>
      <input name="old_password" type="password" required placeholder="Current password">
    </div>
    <div class="form-group" style="margin-bottom:12px;">
      <label>New Password</label>
      <input name="new_password" type="password" required placeholder="New password (min 6 chars)">
    </div>
    <div class="form-group" style="margin-bottom:16px;">
      <label>Confirm New Password</label>
      <input name="confirm_password" type="password" required placeholder="Repeat new password">
    </div>
    <button class="btn btn-success" type="submit">🔒 Update Password</button>
  </form>
</div>"""
    return render_page(content, "settings", "Settings")


# ═══════════════════════════════════════════════════════════════════
# EMPLOYEE – DASHBOARD
# ═══════════════════════════════════════════════════════════════════
@app.route("/emp/dashboard")
@login_required
def emp_dashboard():
    if session["user"]["role"] == "admin":
        return redirect("/dashboard")
    eid    = session["user"]["employee_id"]
    emp    = db.get_employee(eid)
    today  = db.get_today_attendance(eid)
    yr, mo = date.today().year, date.today().month
    hist   = db.get_monthly_attendance(eid, yr, mo)
    bal    = db.get_leave_balance(eid, yr)

    P = sum(1 for r in hist if r["status"] in ("present","late"))
    A = sum(1 for r in hist if r["status"] == "absent")
    L = sum(1 for r in hist if r["status"] == "leave")

    bal_html = "".join(
        f'<div class="kpi" style="--kcolor:#6A1B9A"><div class="k-label">{b["leave_type"]}</div>'
        f'<div class="k-value" style="font-size:22px;">{b["total_days"]-b["used_days"]}</div>'
        f'<div class="k-sub">{b["used_days"]} used of {b["total_days"]}</div></div>'
        for b in bal)

    ci_status = ""
    if today:
        st = today.get("status","")
        ci_status = f'<div class="alert alert-{"warning" if st=="late" else "success" if st in ("present","late") else "info"}">Today: Check-In {today.get("check_in","—")} | Check-Out {today.get("check_out","—") or "—"} | <b>{st.upper()}</b></div>'

    content = f"""
<div class="page-header">
  <div><h1>🏠 Welcome, {emp['name'] if emp else eid}</h1>
  <div class="sub">{emp.get('designation','') if emp else ''} | {date.today().strftime('%A, %d %B %Y')}</div></div>
  <a href="/emp/attendance" class="btn btn-success">📋 Mark Attendance</a>
</div>
{ci_status}
<div class="kpi-grid">
  <div class="kpi" style="--kcolor:#2E7D32"><div class="k-label">Present This Month</div>
    <div class="k-value">{P}</div></div>
  <div class="kpi" style="--kcolor:#C62828"><div class="k-label">Absent This Month</div>
    <div class="k-value">{A}</div></div>
  <div class="kpi" style="--kcolor:#6A1B9A"><div class="k-label">On Leave</div>
    <div class="k-value">{L}</div></div>
</div>
<div class="card"><div class="card-title">📅 Leave Balance — {yr}</div>
  <div class="kpi-grid">{bal_html if bal_html else '<p class="no-data">No leave allocations.</p>'}</div>
</div>"""
    return render_page(content, "emp-dashboard", "My Dashboard")


# ═══════════════════════════════════════════════════════════════════
# EMPLOYEE – ATTENDANCE (Check-In / Check-Out with Camera + GPS)
# ═══════════════════════════════════════════════════════════════════
@app.route("/emp/attendance", methods=["GET","POST"])
@login_required
def emp_attendance():
    if session["user"]["role"] == "admin":
        return redirect("/attendance")
    eid  = session["user"]["employee_id"]
    emp  = db.get_employee(eid)
    msg  = ""
    msg_type = "success"

    if request.method == "POST":
        action   = request.form.get("action")
        photo_b64= request.form.get("photo_data","") or None
        lat      = request.form.get("lat","")
        lng      = request.form.get("lng","")
        location = f"{lat},{lng}" if lat and lng else None

        if action == "checkin":
            ok, text, late = db.mark_checkin(eid, photo_b64, location)
            msg = text; msg_type = "warning" if late else "success"
        elif action == "checkout":
            ok, text = db.mark_checkout(eid, photo_b64, location)
            msg = text; msg_type = "success" if ok else "danger"

    rec     = db.get_today_attendance(eid)
    ci      = rec.get("check_in")  if rec else None
    co      = rec.get("check_out") if rec else None
    year    = int(request.args.get("year",  date.today().year))
    month   = int(request.args.get("month", date.today().month))
    hist    = db.get_monthly_attendance(eid, year, month)
    months_sel = "".join(
        f'<option value="{i}" {"selected" if i==month else ""}>{calendar.month_name[i]}</option>'
        for i in range(1,13))
    years_sel = "".join(
        f'<option {"selected" if y==year else ""}>{y}</option>'
        for y in range(2023, date.today().year+2))

    duty_info = f"Duty: {emp.get('duty_start','09:00')} – {emp.get('duty_end','17:00')}" if emp else ""

    hist_rows = ""
    for r in hist:
        d = datetime.strptime(r["att_date"],"%Y-%m-%d")
        row_cls = {"present":"row-present","late":"row-late","absent":"row-absent","leave":"row-leave"}.get(r.get("status",""),"")
        hist_rows += f"""<tr class="{row_cls}">
          <td>{r['att_date']}</td>
          <td>{d.strftime('%A')}</td>
          <td>{r.get('check_in','—')}</td>
          <td>{r.get('check_out','—')}</td>
          <td><span class="badge b-{r.get('status','absent')}">{r.get('status','—').upper()}</span></td>
          <td>{r.get('late_minutes',0)} min</td>
        </tr>"""

    content = f"""
<div class="page-header"><h1>📋 My Attendance</h1></div>
{'<div class="alert alert-'+msg_type+'">'+msg+'</div>' if msg else ''}
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px;margin-bottom:18px;">
  <div class="card">
    <div class="ci-panel">
      <div class="ci-clock" id="live-clock">--:--:--</div>
      <div class="ci-date">📅 {date.today().strftime('%A, %d %B %Y')}</div>
      <div class="ci-duty">{duty_info}</div>
      {('<div class="alert alert-info" style="margin-bottom:12px;">Today: In='+ci+' | Out='+(co or '—')+'</div>') if rec else ''}
      <div class="cam-box" id="cam-box" style="display:none;">
        <video id="cam-video" autoplay playsinline muted></video>
        <canvas id="cam-canvas" style="display:none;"></canvas>
        <div class="cam-overlay" id="cam-label">Camera active</div>
      </div>
      <div id="location-status" style="font-size:11px;color:var(--muted);margin-bottom:10px;"></div>
      <form method="POST" id="att-form">
        <input type="hidden" name="photo_data" id="photo_data">
        <input type="hidden" name="lat" id="lat_val">
        <input type="hidden" name="lng" id="lng_val">
        <div class="ci-btns">
          <button name="action" value="checkin" type="submit" id="btn-ci"
            class="btn btn-success ci-btn" {'disabled style="opacity:.4;cursor:not-allowed"' if ci else ''}>
            ✅ CHECK IN
          </button>
          <button name="action" value="checkout" type="submit" id="btn-co"
            class="btn btn-danger ci-btn" {'disabled style="opacity:.4;cursor:not-allowed"' if not ci or co else ''}>
            🚪 CHECK OUT
          </button>
        </div>
      </form>
    </div>
  </div>
</div>
<div class="card">
  <div class="card-title">📆 My Attendance History</div>
  <div class="toolbar">
    <form method="GET" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
      <select name="year">{years_sel}</select>
      <select name="month">{months_sel}</select>
      <button class="btn btn-primary btn-sm" type="submit">📋 Load</button>
    </form>
  </div>
  <div class="tbl-wrap"><table>
    <thead><tr><th>Date</th><th>Day</th><th>Check-In</th><th>Check-Out</th><th>Status</th><th>Late</th></tr></thead>
    <tbody>{hist_rows if hist_rows else '<tr><td colspan="6" class="no-data">No records for this month.</td></tr>'}</tbody>
  </table></div>
</div>
<script>
// Camera
var stream = null;
function startCamera(){{
  if(!navigator.mediaDevices)return;
  navigator.mediaDevices.getUserMedia({{video:{{facingMode:'user'}},audio:false}})
  .then(function(s){{
    stream=s;
    var v=document.getElementById('cam-video');
    v.srcObject=s; v.play();
    document.getElementById('cam-box').style.display='block';
  }}).catch(function(){{ document.getElementById('cam-label').textContent='Camera unavailable'; }});
}}
function capturePhoto(){{
  var v=document.getElementById('cam-video');
  var c=document.getElementById('cam-canvas');
  if(!stream||!v.videoWidth)return;
  c.width=v.videoWidth; c.height=v.videoHeight;
  c.getContext('2d').drawImage(v,0,0);
  document.getElementById('photo_data').value=c.toDataURL('image/jpeg',0.6).split(',')[1];
}}
// GPS
function getLocation(){{
  if(!navigator.geolocation)return;
  navigator.geolocation.getCurrentPosition(function(pos){{
    document.getElementById('lat_val').value=pos.coords.latitude;
    document.getElementById('lng_val').value=pos.coords.longitude;
    document.getElementById('location-status').textContent='📍 Location: '+pos.coords.latitude.toFixed(4)+', '+pos.coords.longitude.toFixed(4);
  }},function(){{
    document.getElementById('location-status').textContent='📍 Location not available';
  }});
}}
startCamera(); getLocation();
document.getElementById('att-form').addEventListener('submit',function(){{
  capturePhoto();
}});
</script>"""
    return render_page(content, "emp-att", "My Attendance")


# ═══════════════════════════════════════════════════════════════════
# EMPLOYEE – APPLY LEAVE
# ═══════════════════════════════════════════════════════════════════
@app.route("/emp/leave", methods=["GET","POST"])
@login_required
def emp_leave():
    if session["user"]["role"] == "admin":
        return redirect("/leaves")
    eid  = session["user"]["employee_id"]
    lts  = db.get_leave_types()
    bal  = db.get_leave_balance(eid)
    reqs = db.get_leave_requests(employee_id=eid)

    if request.method == "POST":
        from_d = request.form["from_date"]
        to_d   = request.form["to_date"]
        try:
            d1 = datetime.strptime(from_d, "%Y-%m-%d").date()
            d2 = datetime.strptime(to_d,   "%Y-%m-%d").date()
            days = max(1, (d2-d1).days+1)
        except Exception:
            days = 1
        db.apply_leave(eid, request.form["leave_type"], from_d, to_d, days,
                       request.form.get("reason",""))
        flash("Leave application submitted. Awaiting admin approval.", "success")
        return redirect("/emp/leave")

    lt_opts = "".join(f"<option>{t}</option>" for t in lts)
    bal_html = "".join(
        f'<div class="kpi" style="--kcolor:#6A1B9A"><div class="k-label">{b["leave_type"]}</div>'
        f'<div class="k-value" style="font-size:20px;">{b["total_days"]-b["used_days"]}</div>'
        f'<div class="k-sub">Remaining / {b["total_days"]} total</div></div>'
        for b in bal)

    req_rows = ""
    for r in reqs:
        req_rows += f"""<tr>
          <td>{r['leave_type']}</td>
          <td>{r['from_date']}</td><td>{r['to_date']}</td>
          <td class="text-center">{r['days']}</td>
          <td>{r.get('reason','—')}</td>
          <td><span class="badge b-{r['status']}">{r['status'].title()}</span></td>
          <td>{r.get('admin_note','—')}</td>
        </tr>"""

    content = f"""
<div class="page-header"><h1>📅 Leave Management</h1></div>
<div class="card"><div class="card-title">📊 My Leave Balance — {date.today().year}</div>
  <div class="kpi-grid">{bal_html if bal_html else '<p class="no-data">No leave balance allocated.</p>'}</div>
</div>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px;">
  <div class="card">
    <div class="card-title">📝 Apply for Leave</div>
    <form method="POST">
      <div class="form-group" style="margin-bottom:10px;">
        <label>Leave Type</label>
        <select name="leave_type" required><option value="">-- Select --</option>{lt_opts}</select>
      </div>
      <div class="form-group" style="margin-bottom:10px;">
        <label>From Date</label>
        <input name="from_date" type="date" required value="{date.today().isoformat()}">
      </div>
      <div class="form-group" style="margin-bottom:10px;">
        <label>To Date</label>
        <input name="to_date" type="date" required value="{date.today().isoformat()}">
      </div>
      <div class="form-group" style="margin-bottom:14px;">
        <label>Reason</label>
        <input name="reason" placeholder="Brief reason for leave">
      </div>
      <button class="btn btn-success" type="submit">📤 Submit Application</button>
    </form>
  </div>
</div>
<div class="card" style="margin-top:18px;">
  <div class="card-title">📋 My Leave History</div>
  <div class="tbl-wrap"><table>
    <thead><tr><th>Type</th><th>From</th><th>To</th><th>Days</th>
      <th>Reason</th><th>Status</th><th>Admin Note</th></tr></thead>
    <tbody>{req_rows if req_rows else '<tr><td colspan="7" class="no-data">No leave requests yet.</td></tr>'}</tbody>
  </table></div>
</div>"""
    return render_page(content, "emp-leave", "My Leave")


# ═══════════════════════════════════════════════════════════════════
# EMPLOYEE – PAYSLIP
# ═══════════════════════════════════════════════════════════════════
@app.route("/emp/payslip")
@login_required
def emp_payslip():
    if session["user"]["role"] == "admin":
        return redirect("/payroll")
    eid   = session["user"]["employee_id"]
    year  = int(request.args.get("year",  date.today().year))
    month = int(request.args.get("month", date.today().month))
    pr    = db.get_payroll(eid, year, month)
    months_sel = "".join(
        f'<option value="{i}" {"selected" if i==month else ""}>{calendar.month_name[i]}</option>'
        for i in range(1,13))
    years_sel = "".join(
        f'<option {"selected" if y==year else ""}>{y}</option>'
        for y in range(2023, date.today().year+2))

    if pr:
        slip_html = f"""
<div class="payslip">
  <div class="payslip-head"><h2>SALARY PAYSLIP</h2>
    <div class="sub">{calendar.month_name[pr['month']]} {pr['year']} | Cortex Flow HR</div>
  </div>
  <div class="payslip-meta">
    <div class="m-item"><b>Employee ID</b>{pr['employee_id']}</div>
    <div class="m-item"><b>Name</b>{pr.get('employee_name','—')}</div>
    <div class="m-item"><b>Designation</b>{pr.get('designation','—')}</div>
    <div class="m-item"><b>Department</b>{pr.get('department','—')}</div>
  </div>
  <table class="ps-table">
    <tr><td>Working Days</td><td style="text-align:right">{pr['working_days']}</td></tr>
    <tr><td>Present Days</td><td style="text-align:right;color:#2E7D32;font-weight:700">{pr['present_days']}</td></tr>
    <tr><td>Absent Days</td><td style="text-align:right;color:#C62828">{pr['absent_days']}</td></tr>
    <tr><td>Leave Days</td><td style="text-align:right">{pr['leave_days']}</td></tr>
    <tr><td>Late Arrivals</td><td style="text-align:right">{pr['late_count']} times ({pr['late_minutes']} min)</td></tr>
    <tr class="ps-gross"><td>Gross Salary</td><td style="text-align:right">PKR {pr['gross_salary']:,.2f}</td></tr>
    <tr class="ps-deduct"><td>Absent Deduction</td><td style="text-align:right">– PKR {pr['absent_deduct']:,.2f}</td></tr>
    <tr class="ps-deduct"><td>Late Penalty</td><td style="text-align:right">– PKR {pr['late_deduct']:,.2f}</td></tr>
    <tr><td>Bonus</td><td style="text-align:right;color:#2E7D32">+ PKR {pr.get('bonus',0):,.2f}</td></tr>
    <tr class="ps-total" style="background:#FFF5F5;color:#C62828;font-weight:800"><td>Total Deductions</td><td style="text-align:right">– PKR {pr['total_deduct']:,.2f}</td></tr>
    <tr style="background:#0F2A4A;color:#fff;font-size:17px;font-weight:900;"><td>NET SALARY</td><td style="text-align:right">PKR {pr['net_salary']:,.2f}</td></tr>
  </table>
</div>
<div style="text-align:center;margin-top:14px;">
  <a href="/payroll/slip/{eid}/{year}/{month}" target="_blank" class="btn btn-primary">🖨️ Print Payslip</a>
</div>"""
    else:
        slip_html = '<div class="alert alert-warning">⚠️ No payroll found for this period. Please ask admin to generate payroll.</div>'

    content = f"""
<div class="page-header"><h1>💰 My Payslip</h1></div>
<div class="card" style="max-width:700px;">
  <div class="toolbar">
    <form method="GET" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
      <select name="year">{years_sel}</select>
      <select name="month">{months_sel}</select>
      <button class="btn btn-primary btn-sm" type="submit">💰 View</button>
    </form>
  </div>
  {slip_html}
</div>"""
    return render_page(content, "emp-pay", "My Payslip")


# ═══════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "localhost"

    print("=" * 60)
    print("  🚀  CORTEX FLOW — HR Management System")
    print("=" * 60)
    print(f"  💻  Windows:  http://localhost:5000")
    print(f"  📱  Mobile:   http://{ip}:5000")
    print(f"       (PC & phone must be on same WiFi)")
    print("=" * 60)
    print("  👑  Admin Login:  ADMIN001 / admin123")
    print("=" * 60)
    print("  ⛔  To stop:  Ctrl + C")
    print("=" * 60)

    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    app.run(host=host, port=port, debug=False)