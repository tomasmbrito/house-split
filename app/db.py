import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    amount INTEGER NOT NULL,  -- cents
    paid_by INTEGER NOT NULL REFERENCES people(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS shares (
    expense_id INTEGER NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    person_id INTEGER NOT NULL REFERENCES people(id),
    PRIMARY KEY (expense_id, person_id)
);
"""


def connect(path):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def list_people(conn):
    return [row["name"] for row in conn.execute("SELECT name FROM people ORDER BY id")]


def add_person(conn, name):
    conn.execute("INSERT INTO people (name) VALUES (?)", (name,))
    conn.commit()


def list_expenses(conn):
    rows = conn.execute(
        """SELECT e.id, e.description, e.amount, p.name AS paid_by
           FROM expenses e JOIN people p ON p.id = e.paid_by
           ORDER BY e.id DESC"""
    ).fetchall()
    expenses = []
    for row in rows:
        shared_by = [
            r["name"]
            for r in conn.execute(
                """SELECT p.name FROM shares s JOIN people p ON p.id = s.person_id
                   WHERE s.expense_id = ? ORDER BY p.id""",
                (row["id"],),
            )
        ]
        expenses.append({**dict(row), "shared_by": shared_by})
    return expenses


def add_expense(conn, description, amount, paid_by, shared_by):
    ids = {row["name"]: row["id"] for row in conn.execute("SELECT id, name FROM people")}
    cur = conn.execute(
        "INSERT INTO expenses (description, amount, paid_by) VALUES (?, ?, ?)",
        (description, amount, ids[paid_by]),
    )
    for name in shared_by:
        conn.execute("INSERT INTO shares (expense_id, person_id) VALUES (?, ?)", (cur.lastrowid, ids[name]))
    conn.commit()
    return cur.lastrowid


def delete_expense(conn, expense_id):
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
