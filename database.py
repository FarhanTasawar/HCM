"""
database.py — Cortex Flow HR Management System
SQLite local storage | Future MongoDB migration ready
"""

import sqlite3
import hashlib
import calendar
import os
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path("cortexflow.db")

# ═══════════════════════════════════════════════════════════════════
# CONNECTION & INIT
# ═══════════════════════════════════════════════════════════════════

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def hash_pwd(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    return date.today().isoformat()


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # ── Organizations ──────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS organizations (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL UNIQUE,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Departments ────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS departments (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        name    TEXT NOT NULL,
        org_id  INTEGER REFERENCES organizations(id)
    )""")

    # ── Designations ───────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS designations (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        title   TEXT NOT NULL,
        dept_id INTEGER REFERENCES departments(id)
    )""")

    # ── Users (login) ──────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL UNIQUE,
        password    TEXT NOT NULL,
        role        TEXT NOT NULL DEFAULT 'employee',
        active      INTEGER DEFAULT 1,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Employees ──────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS employees (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id     TEXT NOT NULL UNIQUE,
        name            TEXT NOT NULL,
        designation     TEXT DEFAULT '',
        department      TEXT DEFAULT '',
        organization    TEXT DEFAULT '',
        salary          REAL DEFAULT 0,
        joining_date    TEXT DEFAULT '',
        phone           TEXT DEFAULT '',
        email           TEXT DEFAULT '',
        address         TEXT DEFAULT '',
        duty_start      TEXT DEFAULT '09:00',
        duty_end        TEXT DEFAULT '17:00',
        active          INTEGER DEFAULT 1,
        resigned_at     TEXT DEFAULT NULL,
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Attendance ─────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id     TEXT NOT NULL,
        att_date        TEXT NOT NULL,
        check_in        TEXT DEFAULT NULL,
        check_out       TEXT DEFAULT NULL,
        status          TEXT DEFAULT 'absent',
        late_minutes    INTEGER DEFAULT 0,
        photo_in        TEXT DEFAULT NULL,
        photo_out       TEXT DEFAULT NULL,
        location_in     TEXT DEFAULT NULL,
        location_out    TEXT DEFAULT NULL,
        manual          INTEGER DEFAULT 0,
        note            TEXT DEFAULT '',
        created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(employee_id, att_date)
    )""")

    # ── Leave Types ────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS leave_types (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL UNIQUE,
        description TEXT DEFAULT ''
    )""")

    # ── Leave Allocations (per employee per year) ──────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS leave_allocations (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL,
        leave_type  TEXT NOT NULL,
        year        INTEGER NOT NULL,
        total_days  INTEGER DEFAULT 0,
        used_days   INTEGER DEFAULT 0,
        UNIQUE(employee_id, leave_type, year)
    )""")

    # ── Leave Requests ─────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS leave_requests (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL,
        leave_type  TEXT NOT NULL,
        from_date   TEXT NOT NULL,
        to_date     TEXT NOT NULL,
        days        INTEGER DEFAULT 1,
        reason      TEXT DEFAULT '',
        status      TEXT DEFAULT 'pending',
        admin_note  TEXT DEFAULT '',
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # ── Payroll ────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS payroll (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id     TEXT NOT NULL,
        year            INTEGER NOT NULL,
        month           INTEGER NOT NULL,
        working_days    INTEGER DEFAULT 0,
        present_days    REAL DEFAULT 0,
        absent_days     REAL DEFAULT 0,
        leave_days      REAL DEFAULT 0,
        half_days       REAL DEFAULT 0,
        late_count      INTEGER DEFAULT 0,
        late_minutes    INTEGER DEFAULT 0,
        gross_salary    REAL DEFAULT 0,
        absent_deduct   REAL DEFAULT 0,
        late_deduct     REAL DEFAULT 0,
        bonus           REAL DEFAULT 0,
        total_deduct    REAL DEFAULT 0,
        net_salary      REAL DEFAULT 0,
        generated_at    TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(employee_id, year, month)
    )""")

    conn.commit()

    # ── Seed admin ─────────────────────────────────────────────────
    if not c.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
        c.execute("INSERT INTO users (employee_id,password,role) VALUES (?,?,?)",
                  ("ADMIN001", hash_pwd("admin123"), "admin"))
        conn.commit()

    # ── Seed default leave types ───────────────────────────────────
    for lt in [("Sick Leave","Medical/health leave"),
               ("Casual Leave","Personal/casual leave"),
               ("Annual Leave","Yearly earned leave")]:
        c.execute("INSERT OR IGNORE INTO leave_types (name,description) VALUES (?,?)", lt)
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════

def authenticate(employee_id: str, password: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE employee_id=? AND active=1", (employee_id,)
    ).fetchone()
    conn.close()
    if row and row["password"] == hash_pwd(password):
        return dict(row)
    return None


def change_admin_password(old_pwd: str, new_pwd: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE role='admin' AND active=1"
    ).fetchone()
    if not row or row["password"] != hash_pwd(old_pwd):
        conn.close()
        return False
    conn.execute("UPDATE users SET password=? WHERE role='admin'", (hash_pwd(new_pwd),))
    conn.commit()
    conn.close()
    return True


def update_user_password(employee_id: str, new_pwd: str):
    conn = get_conn()
    conn.execute("UPDATE users SET password=? WHERE employee_id=?",
                 (hash_pwd(new_pwd), employee_id))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════
# ORGANIZATIONS / DEPARTMENTS / DESIGNATIONS
# ═══════════════════════════════════════════════════════════════════

def get_organizations():
    conn = get_conn()
    rows = conn.execute("SELECT name FROM organizations ORDER BY name").fetchall()
    conn.close()
    return [r["name"] for r in rows]


def add_organization(name: str):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO organizations (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def get_departments():
    conn = get_conn()
    rows = conn.execute("SELECT name FROM departments ORDER BY name").fetchall()
    conn.close()
    return [r["name"] for r in rows]


def add_department(name: str):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def get_designations():
    conn = get_conn()
    rows = conn.execute("SELECT title FROM designations ORDER BY title").fetchall()
    conn.close()
    return [r["title"] for r in rows]


def add_designation(title: str):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO designations (title) VALUES (?)", (title,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════
# EMPLOYEES
# ═══════════════════════════════════════════════════════════════════

def add_employee(data: dict):
    conn = get_conn()
    # Check duplicate
    if conn.execute("SELECT 1 FROM employees WHERE employee_id=?",
                    (data["employee_id"],)).fetchone():
        conn.close()
        raise ValueError(f"Employee ID '{data['employee_id']}' already exists.")
    conn.execute("""INSERT INTO employees
        (employee_id,name,designation,department,organization,salary,
         joining_date,phone,email,address,duty_start,duty_end)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
        data["employee_id"], data["name"],
        data.get("designation",""), data.get("department",""),
        data.get("organization",""), float(data.get("salary",0)),
        data.get("joining_date", today_str()),
        data.get("phone",""), data.get("email",""), data.get("address",""),
        data.get("duty_start","09:00"), data.get("duty_end","17:00")
    ))
    conn.execute("INSERT INTO users (employee_id,password,role) VALUES (?,?,?)",
                 (data["employee_id"], hash_pwd(data.get("password","pass1234")), "employee"))
    conn.commit()
    # Add default leave allocations
    yr = date.today().year
    for lt in get_leave_types():
        conn.execute("""INSERT OR IGNORE INTO leave_allocations
            (employee_id,leave_type,year,total_days,used_days) VALUES (?,?,?,?,?)""",
            (data["employee_id"], lt, yr, 10, 0))
    conn.commit()
    conn.close()
    # Auto-add org/dept/desig
    if data.get("organization"): add_organization(data["organization"])
    if data.get("department"):   add_department(data["department"])
    if data.get("designation"):  add_designation(data["designation"])


def get_employee(employee_id: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM employees WHERE employee_id=? AND active=1", (employee_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_employees():
    conn = get_conn()
    rows = conn.execute("""SELECT * FROM employees WHERE active=1
                           ORDER BY organization, department, designation, name""").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_employee(employee_id: str, data: dict):
    conn = get_conn()
    fields = ["name","designation","department","organization","salary",
              "joining_date","phone","email","address","duty_start","duty_end"]
    sets   = ", ".join(f"{f}=?" for f in fields if f in data)
    vals   = [data[f] for f in fields if f in data]
    if sets:
        conn.execute(f"UPDATE employees SET {sets} WHERE employee_id=?",
                     vals + [employee_id])
    if "password" in data:
        conn.execute("UPDATE users SET password=? WHERE employee_id=?",
                     (hash_pwd(data["password"]), employee_id))
    conn.commit()
    conn.close()
    if data.get("organization"): add_organization(data["organization"])
    if data.get("department"):   add_department(data["department"])
    if data.get("designation"):  add_designation(data["designation"])


def resign_employee(employee_id: str):
    conn = get_conn()
    conn.execute("UPDATE employees SET active=0, resigned_at=? WHERE employee_id=?",
                 (now_str(), employee_id))
    conn.execute("UPDATE users SET active=0 WHERE employee_id=?", (employee_id,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════
# ATTENDANCE
# ═══════════════════════════════════════════════════════════════════

def mark_checkin(employee_id: str, photo_b64: str = None, location: str = None):
    emp = get_employee(employee_id)
    if not emp:
        return False, "Employee not found.", False

    today = today_str()
    conn  = get_conn()
    existing = conn.execute(
        "SELECT * FROM attendance WHERE employee_id=? AND att_date=?",
        (employee_id, today)
    ).fetchone()

    if existing and existing["check_in"]:
        conn.close()
        return False, "Already checked in today.", False

    now       = datetime.now()
    duty_str  = emp.get("duty_start","09:00")
    duty_time = datetime.strptime(f"{today} {duty_str}", "%Y-%m-%d %H:%M")
    is_late   = now > duty_time
    late_mins = int((now - duty_time).total_seconds() / 60) if is_late else 0
    status    = "late" if is_late else "present"
    ci_str    = now.strftime("%H:%M:%S")

    if existing:
        conn.execute("""UPDATE attendance SET check_in=?,status=?,late_minutes=?,
                        photo_in=?,location_in=? WHERE employee_id=? AND att_date=?""",
                     (ci_str, status, late_mins, photo_b64, location, employee_id, today))
    else:
        conn.execute("""INSERT INTO attendance
            (employee_id,att_date,check_in,status,late_minutes,photo_in,location_in)
            VALUES (?,?,?,?,?,?,?)""",
            (employee_id, today, ci_str, status, late_mins, photo_b64, location))
    conn.commit()
    conn.close()

    msg = f"Checked in at {ci_str[:5]}."
    if is_late:
        msg += f" ⚠️ You are {late_mins} minute(s) late!"
    return True, msg, is_late


def mark_checkout(employee_id: str, photo_b64: str = None, location: str = None):
    today = today_str()
    conn  = get_conn()
    rec   = conn.execute(
        "SELECT * FROM attendance WHERE employee_id=? AND att_date=?",
        (employee_id, today)
    ).fetchone()

    if not rec or not rec["check_in"]:
        conn.close()
        return False, "No check-in found for today."
    if rec["check_out"]:
        conn.close()
        return False, "Already checked out today."

    now = datetime.now()
    conn.execute("""UPDATE attendance SET check_out=?,photo_out=?,location_out=?
                    WHERE employee_id=? AND att_date=?""",
                 (now.strftime("%H:%M:%S"), photo_b64, location, employee_id, today))
    conn.commit()
    conn.close()
    return True, f"Checked out at {now.strftime('%H:%M')}."


def get_today_attendance(employee_id: str):
    conn = get_conn()
    row  = conn.execute(
        "SELECT * FROM attendance WHERE employee_id=? AND att_date=?",
        (employee_id, today_str())
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_today_all_attendance():
    conn = get_conn()
    rows = conn.execute("""
        SELECT a.*, e.name as emp_name, e.designation, e.department
        FROM attendance a
        JOIN employees e ON a.employee_id = e.employee_id
        WHERE a.att_date=?
        ORDER BY a.check_in ASC NULLS LAST
    """, (today_str(),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_monthly_attendance(employee_id: str, year: int, month: int):
    start = f"{year}-{month:02d}-01"
    end   = f"{year}-{month:02d}-{calendar.monthrange(year,month)[1]:02d}"
    conn  = get_conn()
    rows  = conn.execute("""SELECT * FROM attendance
                            WHERE employee_id=? AND att_date>=? AND att_date<=?
                            ORDER BY att_date""",
                         (employee_id, start, end)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_attendance_month(year: int, month: int):
    start = f"{year}-{month:02d}-01"
    end   = f"{year}-{month:02d}-{calendar.monthrange(year,month)[1]:02d}"
    conn  = get_conn()
    rows  = conn.execute("""SELECT a.*, e.name as emp_name, e.designation, e.department
                            FROM attendance a
                            JOIN employees e ON a.employee_id=e.employee_id
                            WHERE a.att_date>=? AND a.att_date<=?
                            ORDER BY a.att_date, e.name""",
                         (start, end)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_manual_attendance(employee_id: str, att_date: str, status: str,
                            check_in: str = "", check_out: str = "", note: str = ""):
    emp  = get_employee(employee_id)
    conn = get_conn()
    conn.execute("""INSERT INTO attendance
        (employee_id,att_date,check_in,check_out,status,late_minutes,manual,note)
        VALUES (?,?,?,?,?,?,1,?)
        ON CONFLICT(employee_id,att_date) DO UPDATE SET
        check_in=excluded.check_in, check_out=excluded.check_out,
        status=excluded.status, manual=1, note=excluded.note""",
        (employee_id, att_date, check_in or None, check_out or None, status, 0, note))
    conn.commit()
    conn.close()


def get_attendance_photo(employee_id: str, att_date: str, which: str = "in"):
    conn = get_conn()
    col  = "photo_in" if which == "in" else "photo_out"
    row  = conn.execute(f"SELECT {col} FROM attendance WHERE employee_id=? AND att_date=?",
                        (employee_id, att_date)).fetchone()
    conn.close()
    return row[col] if row else None


# ═══════════════════════════════════════════════════════════════════
# LEAVE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

def get_leave_types():
    conn  = get_conn()
    rows  = conn.execute("SELECT name FROM leave_types ORDER BY name").fetchall()
    conn.close()
    return [r["name"] for r in rows]


def add_leave_type(name: str, description: str = ""):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO leave_types (name,description) VALUES (?,?)",
                 (name, description))
    conn.commit()
    conn.close()


def delete_leave_type(name: str):
    conn = get_conn()
    conn.execute("DELETE FROM leave_types WHERE name=?", (name,))
    conn.commit()
    conn.close()


def get_leave_balance(employee_id: str, year: int = None):
    if not year: year = date.today().year
    conn = get_conn()
    rows = conn.execute("""SELECT * FROM leave_allocations
                           WHERE employee_id=? AND year=?""",
                        (employee_id, year)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_leave_allocation(employee_id: str, leave_type: str, year: int, total_days: int):
    conn = get_conn()
    conn.execute("""INSERT INTO leave_allocations (employee_id,leave_type,year,total_days,used_days)
                    VALUES (?,?,?,?,0)
                    ON CONFLICT(employee_id,leave_type,year)
                    DO UPDATE SET total_days=excluded.total_days""",
                 (employee_id, leave_type, year, total_days))
    conn.commit()
    conn.close()


def apply_leave(employee_id: str, leave_type: str,
                from_date: str, to_date: str, days: int, reason: str):
    conn = get_conn()
    conn.execute("""INSERT INTO leave_requests
        (employee_id,leave_type,from_date,to_date,days,reason,status)
        VALUES (?,?,?,?,?,?,'pending')""",
        (employee_id, leave_type, from_date, to_date, days, reason))
    conn.commit()
    conn.close()


def get_leave_requests(employee_id: str = None, status: str = None):
    conn  = get_conn()
    query = """SELECT lr.*, e.name as emp_name FROM leave_requests lr
               JOIN employees e ON lr.employee_id=e.employee_id WHERE 1=1"""
    params = []
    if employee_id:
        query += " AND lr.employee_id=?"; params.append(employee_id)
    if status:
        query += " AND lr.status=?"; params.append(status)
    query += " ORDER BY lr.created_at DESC"
    rows  = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def approve_leave(request_id: int, admin_note: str = ""):
    conn = get_conn()
    req  = conn.execute("SELECT * FROM leave_requests WHERE id=?", (request_id,)).fetchone()
    if req:
        conn.execute("UPDATE leave_requests SET status='approved',admin_note=? WHERE id=?",
                     (admin_note, request_id))
        conn.execute("""UPDATE leave_allocations SET used_days=used_days+?
                        WHERE employee_id=? AND leave_type=? AND year=?""",
                     (req["days"], req["employee_id"], req["leave_type"],
                      int(req["from_date"][:4])))
        # Mark attendance as leave
        from datetime import timedelta
        s = datetime.strptime(req["from_date"], "%Y-%m-%d").date()
        e = datetime.strptime(req["to_date"],   "%Y-%m-%d").date()
        d = s
        while d <= e:
            conn.execute("""INSERT INTO attendance (employee_id,att_date,status,manual,note)
                            VALUES (?,?,'leave',1,'Approved leave')
                            ON CONFLICT(employee_id,att_date)
                            DO UPDATE SET status='leave',note='Approved leave'""",
                         (req["employee_id"], d.isoformat()))
            d += timedelta(days=1)
        conn.commit()
    conn.close()


def reject_leave(request_id: int, admin_note: str = ""):
    conn = get_conn()
    conn.execute("UPDATE leave_requests SET status='rejected',admin_note=? WHERE id=?",
                 (admin_note, request_id))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════════
# PAYROLL
# ═══════════════════════════════════════════════════════════════════

LATE_PER_MIN        = 10    # PKR per late minute
ABSENT_FACTOR       = 1.5   # multiplier on per-day rate


def generate_payroll(employee_id: str, year: int, month: int, bonus: float = 0) -> dict:
    emp  = get_employee(employee_id)
    if not emp: raise ValueError("Employee not found.")

    recs         = get_monthly_attendance(employee_id, year, month)
    working_days = calendar.monthrange(year, month)[1]

    present = absent = late = leave = half = late_mins_total = 0
    for r in recs:
        s = r.get("status","absent")
        if s == "present":    present += 1
        elif s == "late":     late += 1; present += 1; late_mins_total += r.get("late_minutes",0)
        elif s == "absent":   absent  += 1
        elif s == "leave":    leave   += 1
        elif s == "half-day": half    += 1; present += 0.5

    absent += max(0, working_days - len(recs))
    gross   = emp["salary"]
    per_day = gross / working_days if working_days else 0
    a_ded   = round(absent * per_day * ABSENT_FACTOR, 2)
    l_ded   = round(late_mins_total * LATE_PER_MIN, 2)
    total_d = round(a_ded + l_ded, 2)
    net     = round(max(0, gross - total_d + bonus), 2)

    conn = get_conn()
    conn.execute("""INSERT INTO payroll
        (employee_id,year,month,working_days,present_days,absent_days,leave_days,
         half_days,late_count,late_minutes,gross_salary,absent_deduct,late_deduct,
         bonus,total_deduct,net_salary,generated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(employee_id,year,month) DO UPDATE SET
        working_days=excluded.working_days, present_days=excluded.present_days,
        absent_days=excluded.absent_days, leave_days=excluded.leave_days,
        half_days=excluded.half_days, late_count=excluded.late_count,
        late_minutes=excluded.late_minutes, gross_salary=excluded.gross_salary,
        absent_deduct=excluded.absent_deduct, late_deduct=excluded.late_deduct,
        bonus=excluded.bonus, total_deduct=excluded.total_deduct,
        net_salary=excluded.net_salary, generated_at=excluded.generated_at""",
        (employee_id, year, month, working_days, present, absent, leave,
         half, late, late_mins_total, gross, a_ded, l_ded, bonus, total_d, net, now_str()))
    conn.commit()
    conn.close()

    return {"employee_id": employee_id, "employee_name": emp["name"],
            "designation": emp.get("designation",""), "department": emp.get("department",""),
            "organization": emp.get("organization",""),
            "year": year, "month": month, "working_days": working_days,
            "present_days": present, "absent_days": absent, "leave_days": leave,
            "half_days": half, "late_count": late, "late_minutes": late_mins_total,
            "gross_salary": gross, "absent_deduct": a_ded, "late_deduct": l_ded,
            "bonus": bonus, "total_deduct": total_d, "net_salary": net,
            "generated_at": now_str()}


def get_payroll(employee_id: str, year: int, month: int):
    conn = get_conn()
    row  = conn.execute(
        "SELECT * FROM payroll WHERE employee_id=? AND year=? AND month=?",
        (employee_id, year, month)
    ).fetchone()
    conn.close()
    if not row: return None
    pr   = dict(row)
    emp  = get_employee(employee_id)
    if emp:
        pr["employee_name"] = emp["name"]
        pr["designation"]   = emp.get("designation","")
        pr["department"]    = emp.get("department","")
        pr["organization"]  = emp.get("organization","")
    return pr


def get_all_payroll_month(year: int, month: int):
    conn = get_conn()
    rows = conn.execute("""SELECT p.*, e.name as employee_name, e.designation, e.department
                           FROM payroll p JOIN employees e ON p.employee_id=e.employee_id
                           WHERE p.year=? AND p.month=?
                           ORDER BY e.name""", (year, month)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════

def get_dashboard_stats():
    today = today_str()
    conn  = get_conn()
    total   = conn.execute("SELECT COUNT(*) FROM employees WHERE active=1").fetchone()[0]
    present = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE att_date=? AND status IN ('present','late')",
        (today,)).fetchone()[0]
    absent  = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE att_date=? AND status='absent'",
        (today,)).fetchone()[0]
    late    = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE att_date=? AND status='late'",
        (today,)).fetchone()[0]
    on_leave= conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE att_date=? AND status='leave'",
        (today,)).fetchone()[0]
    pending_leaves = conn.execute(
        "SELECT COUNT(*) FROM leave_requests WHERE status='pending'").fetchone()[0]
    conn.close()
    return {"total": total, "present": present, "absent": absent,
            "late": late, "on_leave": on_leave, "pending_leaves": pending_leaves,
            "date": today}


# ═══════════════════════════════════════════════════════════════════
# INITIALISE
# ═══════════════════════════════════════════════════════════════════
init_db()