import os
import sqlite3

from flask import Flask, g, jsonify, redirect, render_template, request, url_for

from app import db
from app.balances import compute_balances, settle


def parse_amount(text):
    """'12.5' or '12,50' (euros) -> 1250 (cents). Returns None if it's not a valid amount."""
    euros, _, cents = text.strip().replace(",", ".").partition(".")
    if not (euros + cents).isdigit() or len(cents) > 2:
        return None
    value = int(euros or 0) * 100 + int(cents.ljust(2, "0"))
    return value if value > 0 else None


def summary(conn):
    people = db.list_people(conn)
    expenses = db.list_expenses(conn)
    balances = compute_balances(people, expenses)
    return {
        "people": people,
        "expenses": expenses,
        "balances": balances,
        "payments": [{"from": a, "to": b, "amount": c} for a, b, c in settle(balances)],
    }


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or os.environ.get("DB_PATH", "data/house.db")

    def get_db():
        if "conn" not in g:
            g.conn = db.connect(app.config["DB_PATH"])
        return g.conn

    @app.teardown_appcontext
    def close_db(_error):
        conn = g.pop("conn", None)
        if conn is not None:
            conn.close()

    @app.template_filter("euros")
    def euros(cents):
        return f"{cents / 100:.2f} €"

    @app.get("/")
    def index():
        return render_template("index.html", error=request.args.get("error"), **summary(get_db()))

    @app.post("/people")
    def new_person():
        name = request.form.get("name", "").strip().lower()
        if not name:
            return redirect(url_for("index", error="The name can't be empty"))
        try:
            db.add_person(get_db(), name)
        except sqlite3.IntegrityError:
            return redirect(url_for("index", error=f"{name} is already in the house"))
        return redirect(url_for("index"))

    @app.post("/expenses")
    def new_expense():
        conn = get_db()
        people = db.list_people(conn)
        description = request.form.get("description", "").strip()
        amount = parse_amount(request.form.get("amount", ""))
        paid_by = request.form.get("paid_by")
        # if nobody is ticked, the expense is shared by the whole house
        shared_by = [p for p in request.form.getlist("shared_by") if p in people] or people

        if not description or amount is None or paid_by not in people:
            return redirect(url_for("index", error="Fill in a description, a valid amount and who paid"))
        db.add_expense(conn, description, amount, paid_by, shared_by)
        return redirect(url_for("index"))

    @app.post("/expenses/<int:expense_id>/delete")
    def remove_expense(expense_id):
        db.delete_expense(get_db(), expense_id)
        return redirect(url_for("index"))

    @app.get("/api/summary")
    def api_summary():
        return jsonify(summary(get_db()))

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
