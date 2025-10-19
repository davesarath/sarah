from flask import Flask,render_template, request, jsonify
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv() 

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "root")
DB_NAME = os.getenv("DB_NAME", "petcare")

# app = Flask(_name_, template_folder=template_dir)
# CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Go one level up, then into frontend/dashboard/admin dashboard
template_dir = os.path.join(BASE_DIR, '..', 'frontend', 'dashboard', 'admin_dashboard')

# Normalize the path (important for Windows)
template_dir = os.path.normpath(template_dir)

print("Looking for templates in:", template_dir)

app = Flask(__name__, template_folder=template_dir)

print(DB_HOST)
print(DB_USER)
def get_conn():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    db = get_conn()
    cursor = db.cursor(dictionary=True)
    try:    
        # Handle form submission (Add new user)
        if request.method == 'POST':
            fullname = request.form['fullname']
            email = request.form['email']
            role = request.form['role']
            status = request.form['status']
            password = request.form['password']

            query = "INSERT INTO users (username, email, role, status,password) VALUES (%s, %s, %s, %s, %s)"
            values = (fullname, email, role, status,password )
            print(values)
            print(query)
            cursor.execute(query, values)
            db.commit()

        # Fetch all users (whether GET or POST)
        cursor.execute("SELECT user_id,username,email, role, status FROM users")
        users = cursor.fetchall()

        cursor.close()
    finally:
        db.close()
        print(users)
    return render_template('manageusers.html', users=users)

# @app.route("/api/health", methods=["GET"])
# def health():
#     return jsonify({"status":"ok"}), 200

# @app.route("/api/auth/register", methods=["POST"])
# def register():
#     data = request.json or {}
#     username = data.get("username")
#     email = data.get("email")
#     password = data.get("password")
#     role = data.get("role", "owner")

#     if not (username and email and password):
#         return jsonify({"msg":"username, email and password required"}), 400

#     conn = get_conn()
#     cur = conn.cursor()
#     hashed = generate_password_hash(password)
#     try:
#         cur.execute(
#             "INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)",
#             (username, hashed, email, role)
#         )
#         conn.commit()
#     except mysql.connector.Error as e:
#         conn.rollback()
#         cur.close()
#         conn.close()
#         return jsonify({"msg":"DB error", "error": str(e)}), 400

#     cur.close()
#     conn.close()
#     return jsonify({"msg":"User registered"}), 201

# @app.route("/api/auth/login", methods=["POST"])
# def login():
#     data = request.json or {}
#     username = data.get("username")
#     password = data.get("password")
#     if not (username and password):
#         return jsonify({"msg":"username and password required"}), 400

#     conn = get_conn()
#     cur = conn.cursor(dictionary=True)
#     cur.execute("SELECT * FROM users WHERE username = %s", (username,))
#     user = cur.fetchone()
#     cur.close()
#     conn.close()

#     if not user:
#         return jsonify({"msg":"Invalid credentials"}), 401

#     if check_password_hash(user["password"], password):
#         # NOTE: we return user_id and role for simple session handling on frontend (no JWT here yet)
#         return jsonify({"msg":"Login ok", "user_id": user["user_id"], "role": user["role"]}), 200

#     return jsonify({"msg":"Invalid credentials"}), 401


# @app.route("/api/pets", methods=["GET"])
# def list_pets():
#     conn = get_conn()
#     cur = conn.cursor(dictionary=True)
#     cur.execute("SELECT * FROM pets")
#     rows = cur.fetchall()
#     cur.close()
#     conn.close()
#     return jsonify(rows), 200


# @app.route("/api/pets", methods=["POST"])
# def add_pet():
#     data = request.json or {}
#     required = ("owner_id","name")
#     if not all(k in data for k in required):
#         return jsonify({"msg":"owner_id and name required"}), 400

#     conn = get_conn()
#     cur = conn.cursor()
#     cur.execute("""INSERT INTO pets (owner_id, name, breed, age, gender, medical_history)
#                    VALUES (%s,%s,%s,%s,%s,%s)""",
#                 (data.get("owner_id"), data.get("name"), data.get("breed"),
#                  data.get("age"), data.get("gender"), data.get("medical_history","")))
#     conn.commit()
#     cur.close()
#     conn.close()
#     return jsonify({"msg":"Pet added"}), 201


# ---------- MAIN ----------
if __name__ == '__main__':
    app.run(debug=True)