# auth.py — Role-Based Authentication with SQLite

import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from config import Config


class User(UserMixin):
    def __init__(self, id, username, role, email, assigned_machine=None):
        self.id               = id
        self.username         = username
        self.role             = role
        self.email            = email
        self.assigned_machine = assigned_machine

    def can(self, permission):
        perms = {
            "admin":    ["view_all","manage_users","generate_reports","view_costs","view_failures","update_maintenance","view_assigned"],
            "engineer": ["view_failures","update_maintenance","view_all"],
            "operator": ["view_assigned"],
            "manager":  ["view_all","generate_reports","view_costs"],
        }
        return permission in perms.get(self.role, [])


def get_db():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            username         TEXT UNIQUE NOT NULL,
            password_hash    TEXT NOT NULL,
            role             TEXT NOT NULL,
            email            TEXT,
            assigned_machine TEXT
        )
    """)
    conn.commit()
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        defaults = [
            ("admin",     "Admin@123",     "admin",    "admin@factory.com",   None),
            ("engineer1", "Engineer@123",  "engineer", "eng@factory.com",     None),
            ("operator1", "Operator@123",  "operator", "op@factory.com",      "MCH-101"),
            ("manager1",  "Manager@123",   "manager",  "mgr@factory.com",     None),
        ]
        for u, p, r, e, m in defaults:
            conn.execute(
                "INSERT INTO users (username,password_hash,role,email,assigned_machine) VALUES (?,?,?,?,?)",
                (u, generate_password_hash(p), r, e, m)
            )
        conn.commit()
    conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    row  = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return User(row["id"],row["username"],row["role"],row["email"],row["assigned_machine"]) if row else None


def get_user_by_username(username):
    conn = get_db()
    row  = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return row


def verify_user(username, password):
    row = get_user_by_username(username)
    if row and check_password_hash(row["password_hash"], password):
        return User(row["id"],row["username"],row["role"],row["email"],row["assigned_machine"])
    return None


def get_all_users():
    conn = get_db()
    rows = conn.execute("SELECT id,username,role,email,assigned_machine FROM users").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_user(username, password, role, email, assigned_machine=None):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username,password_hash,role,email,assigned_machine) VALUES (?,?,?,?,?)",
            (username, generate_password_hash(password), role, email, assigned_machine)
        )
        conn.commit()
        return True, "User created successfully"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    finally:
        conn.close()


def delete_user(user_id):
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
