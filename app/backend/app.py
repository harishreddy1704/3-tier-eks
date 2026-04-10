import os
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db():
    return psycopg2.connect(
        host     = os.environ.get("DB_HOST", "localhost"),
        port     = os.environ.get("DB_PORT", 5432),
        dbname   = os.environ.get("DB_NAME", "appdb"),
        user     = os.environ.get("DB_USER", "dbadmin"),
        password = os.environ.get("DB_PASSWORD", ""),
    )

def init_db():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id         SERIAL PRIMARY KEY,
            name       VARCHAR(100) NOT NULL,
            department VARCHAR(100) NOT NULL,
            role       VARCHAR(100) NOT NULL,
            email      VARCHAR(150) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route("/health")
def health():
    try:
        conn = get_db()
        conn.close()
        return jsonify({"status": "ok", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "error", "database": str(e)}), 500

@app.route("/api/employees", methods=["GET"])
def get_employees():
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM employees ORDER BY created_at DESC")
    employees = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(list(employees)), 200

@app.route("/api/employees", methods=["POST"])
def add_employee():
    data = request.get_json()
    name       = data.get("name", "").strip()
    department = data.get("department", "").strip()
    role       = data.get("role", "").strip()
    email      = data.get("email", "").strip()

    if not all([name, department, role, email]):
        return jsonify({"error": "All fields are required"}), 400

    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """INSERT INTO employees (name, department, role, email)
               VALUES (%s, %s, %s, %s) RETURNING *""",
            (name, department, role, email)
        )
        new_employee = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(dict(new_employee)), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({"error": "Email already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/employees/<int:emp_id>", methods=["DELETE"])
def delete_employee(emp_id):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("DELETE FROM employees WHERE id = %s RETURNING id", (emp_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if deleted:
        return jsonify({"message": f"Employee {emp_id} deleted"}), 200
    return jsonify({"error": "Employee not found"}), 404

@app.route("/api/departments", methods=["GET"])
def get_departments():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT department FROM employees ORDER BY department")
    departments = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(departments), 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)