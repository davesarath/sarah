from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_from_directory,
    redirect,
    flash,
    session,
    url_for,
)
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from functools import wraps
from werkzeug.utils import secure_filename


# Load environment variables from your custom file
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "root")
DB_NAME = os.getenv("DB_NAME", "petcare")

# app = Flask(_name_, template_folder=template_dir)
# CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Go one level up, then into frontend/dashboard/admin dashboard
template_dir = os.path.join(BASE_DIR, "..", "frontend")
static_dir = os.path.join(BASE_DIR, "..", "frontend", "assets")

# Normalize the path (important for Windows)
template_dir = os.path.normpath(template_dir)
static_dir = os.path.normpath(static_dir)

print("Looking for templates in:", template_dir)
app = Flask(
    __name__,
    template_folder=template_dir,
    static_folder=static_dir,
    static_url_path="/assets",
)

app.secret_key = "super_secret_key"  # Required for flash and session


UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'static', 'uploads')
UPLOAD_FOLDER = os.path.normpath(UPLOAD_FOLDER)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Serve static files from the static directory
@app.route('/static/<path:filename>')
def serve_static(filename):
    static_root = os.path.join(BASE_DIR, '..', 'static')
    static_root = os.path.normpath(static_root)
    return send_from_directory(static_root, filename)

def get_conn():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
    )

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/404", methods=["GET"])
def logaccessdenied():
    return render_template("dashboard/accessdenied.html")


def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                return redirect(url_for("logaccessdenied"))
            return fn(*args, **kwargs)

        return decorated

    return wrapper


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("petcareFrontend/register.html")
    data = request.form or {}
    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")
    phone = data.get("phone") or ""
    specialization =  data.get("specialization") or ""
    address =  data.get("address") or ""
    confirm_password = data.get("confirm_password")
    role = data.get("role")
    if not (full_name and email and password):
        flash("Please log in first.", "danger")
        return render_template("petcareFrontend/register.html")
    if confirm_password != password:
        flash("Password mismatch.", "danger")
        return render_template("petcareFrontend/register.html")

    conn = get_conn()
    cur = conn.cursor()

    # cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user1 = cur.fetchone()

    if user1:
        flash("email duplicate.", "danger")
        cur.close()
        conn.close()
        return render_template("petcareFrontend/register.html")
    hashed = generate_password_hash(password)
    try:
        cur.execute(
            "INSERT INTO users (full_name, password, email, role) VALUES (%s, %s, %s, %s)",
            (full_name, hashed, email, role),
        )
        
        # Get the newly inserted user_id
        user_id = cur.lastrowid
        roleQuery=""
        if(role == "Veterinarian"):
            roleQuery = "INSERT INTO veterinarians (user_id, specialization, phone, clinic_address) VALUES (%s, %s, %s, %s)"
            values = (user_id, specialization, phone, address)
        elif(role == "Pet Owner"):
            roleQuery = "INSERT INTO owners (user_id, phone, address) VALUES (%s, %s, %s)"
            values = (user_id, phone, address)
        if(roleQuery):
            cur.execute(roleQuery, values)
        conn.commit()
    except mysql.connector.Error as e:
        conn.rollback()
        cur.close()
        conn.close()
        print(str(e))
        flash("Something went wrong.", "danger")
        return render_template("petcareFrontend/register.html")

    cur.close()
    conn.close()
    flash("Registration successful! Please login.", "success")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("petcareFrontend/index.html")
    data = request.form or {}
    email = data.get("email")
    password = data.get("password")
    if not (email and password):
        flash("email and password required.", "danger")
        return render_template("petcareFrontend/index.html")

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        flash("Invalid credentials.", "danger")
        return render_template("petcareFrontend/index.html")

    if check_password_hash(user["password"], password):
        session["user_id"] = user["user_id"]
        session["full_name"] = user["full_name"]
        session["role"] = user["role"]
        # NOTE: we return user_id and role for simple session handling on frontend (no JWT here yet)
        return redirect(url_for("homePage"))
    else:
        flash("Invalid credentials.", "danger")
        return render_template("petcareFrontend/index.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgotPassword():
    if request.method == "GET":
        return render_template("petcareFrontend/forgot-password.html")
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")
    if not (email and password):
        return jsonify({"msg": "email and password required"}), 400
    return jsonify({"msg": "Invalid credentials"}), 401


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


@app.route("/", methods=["GET"])
@role_required("Admin","Pet Owner","Veterinarian")
def homePage():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Role-based dashboard rendering
    role = session.get("role")
    user_id = session.get("user_id")
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        if role == "Admin":
            # Get dashboard statistics
            cursor.execute("SELECT COUNT(*) as total_users FROM users WHERE vchr_status = 'A'")
            total_users = cursor.fetchone()["total_users"]
            
            cursor.execute("SELECT COUNT(*) as total_pets FROM pets")
            total_pets = cursor.fetchone()["total_pets"]
            
            cursor.execute("SELECT COUNT(*) as total_appointments FROM appointments WHERE DATE(appointment_date) >= CURDATE()")
            total_appointments = cursor.fetchone()["total_appointments"]
            
            cursor.execute("SELECT COUNT(*) as total_records FROM (SELECT vaccination_id FROM vaccinations UNION ALL SELECT medication_id FROM medications) as records")
            total_records = cursor.fetchone()["total_records"]
            
            # Get recent activities
            cursor.execute("""
                (SELECT 'User Registration' as activity_type, CONCAT('New user: ', u.full_name) as details, u.created_at as activity_date
                 FROM users u WHERE u.vchr_status = 'A' ORDER BY u.created_at DESC LIMIT 3)
                UNION ALL
                (SELECT 'Pet Added' as activity_type, CONCAT('New pet: ', p.name, ' (', p.breed, ')') as details, p.created_at as activity_date
                 FROM pets p ORDER BY p.created_at DESC LIMIT 3)
                UNION ALL
                (SELECT 'Appointment' as activity_type, CONCAT('Appointment booked for ', p.name) as details, a.created_at as activity_date
                 FROM appointments a JOIN pets p ON a.pet_id = p.pet_id ORDER BY a.created_at DESC LIMIT 3)
                ORDER BY activity_date DESC LIMIT 10
            """)
            recent_activities = cursor.fetchall()
            
            return render_template("dashboard/admin.html", 
                                 total_users=total_users, 
                                 total_pets=total_pets, 
                                 total_appointments=total_appointments, 
                                 total_records=total_records,
                                 recent_activities=recent_activities)
        elif role == "Veterinarian":
            # Get vet_id and today's appointments
            cursor.execute("SELECT vet_id FROM veterinarians WHERE user_id = %s", (user_id,))
            vet_data = cursor.fetchone()
            
            today_appointments = []
            if vet_data:
                cursor.execute("""
                    SELECT a.*, p.name as pet_name, u.full_name as owner_name,
                           TIME_FORMAT(a.appointment_date, '%h:%i %p') as appointment_time
                    FROM appointments a
                    JOIN pets p ON a.pet_id = p.pet_id
                    JOIN owners o ON a.owner_id = o.owner_id
                    JOIN users u ON o.user_id = u.user_id
                    WHERE a.vet_id = %s AND DATE(a.appointment_date) = CURDATE()
                    AND a.status != 'Cancelled'
                    ORDER BY a.appointment_date ASC
                """, (vet_data["vet_id"],))
                today_appointments = cursor.fetchall()
            
            # Get recent activities (last 10)
            recent_activities = []
            if vet_data:
                cursor.execute("""
                    (SELECT 'Vaccination' as activity_type, v.vaccine_name as details, 
                     p.name as pet_name, v.date_given as activity_date
                     FROM vaccinations v
                     JOIN pets p ON v.pet_id = p.pet_id
                     WHERE v.vet_id = %s)
                    UNION ALL
                    (SELECT 'Medication' as activity_type, m.medicine_name as details,
                     p.name as pet_name, m.start_date as activity_date
                     FROM medications m
                     JOIN pets p ON m.pet_id = p.pet_id
                     WHERE m.vet_id = %s)
                    ORDER BY activity_date DESC
                    LIMIT 10
                """, (vet_data["vet_id"], vet_data["vet_id"]))
                recent_activities = cursor.fetchall()
            
            return render_template("dashboard/vet.html", today_appointments=today_appointments, recent_activities=recent_activities)
        cursor.execute(
            """
                SELECT pt.*
                FROM pets pt
                LEFT JOIN owners owr ON pt.owner_id = owr.owner_id
                WHERE owr.user_id = %s
            """,(user_id,)
        )
        pets = cursor.fetchall()
        
        # Get upcoming reminders (medications and vaccinations)
        cursor.execute(
            """
            (SELECT 'Medication' as reminder_type, m.medicine_name as details,
             p.name as pet_name, m.end_date as reminder_date
             FROM medications m
             JOIN pets p ON m.pet_id = p.pet_id
             JOIN owners o ON p.owner_id = o.owner_id
             WHERE o.user_id = %s AND m.end_date >= CURDATE())
            UNION ALL
            (SELECT 'Vaccination' as reminder_type, v.vaccine_name as details,
             p.name as pet_name, DATE_ADD(v.date_given, INTERVAL 365 DAY) as reminder_date
             FROM vaccinations v
             JOIN pets p ON v.pet_id = p.pet_id
             JOIN owners o ON p.owner_id = o.owner_id
             WHERE o.user_id = %s AND DATE_ADD(v.date_given, INTERVAL 365 DAY) >= CURDATE())
            ORDER BY reminder_date ASC
            LIMIT 5
            """, (user_id, user_id)
        )
        upcoming_reminders = cursor.fetchall()
        
        return render_template("dashboard/owner.html", pets=pets, upcoming_reminders=upcoming_reminders)
    finally:
        cursor.close()
        conn.close()

@app.route("/manageusers", methods=["GET", "POST"])
@role_required("Admin")
def manage_users():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    users = []
    try:
        # Fetch all users (whether GET or POST)
        cursor.execute(
            """
            SELECT 
            usr.user_id AS user_id,
            usr.full_name AS full_name,
            COALESCE(owr.owner_id, vet.vet_id) AS related_id,
            usr.email AS email,
            usr.role AS role,
            usr.status AS status,
            vet.specialization AS specialization,
            CASE 
                WHEN usr.role = 'Pet Owner' THEN owr.phone
                WHEN usr.role = 'Veterinarian' THEN vet.phone
                ELSE NULL
            END AS phone,
            CASE 
                WHEN usr.role = 'Pet Owner' THEN owr.address
                WHEN usr.role = 'Veterinarian' THEN vet.clinic_address
                ELSE NULL
            END AS address
            FROM users AS usr
            LEFT JOIN owners AS owr ON usr.user_id = owr.user_id
            LEFT JOIN veterinarians AS vet ON usr.user_id = vet.user_id
            WHERE usr.vchr_status = 'A'
            """
        )
        users = cursor.fetchall()

    except mysql.connector.Error as e:
        conn.rollback()
        cur.close()
        conn.close()
        print(str(e))

    finally:
        cursor.close()
        conn.close()
    return render_template("dashboard/admin_dashboard/manageusers.html", users=users)


@app.route("/manage_add_user", methods=["POST"])
@role_required("Admin")
def manage_add_users():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        # Handle form submission (Add new user)
        full_name = request.form["full_name"]
        email = request.form["email"]
        role = request.form["role"]
        status = request.form["status"]
        phone = request.form["phone"]
        specialization = request.form["specialization"]
        address = request.form["address"]
        password = request.form["password"]
        password = generate_password_hash(password)
        query = "INSERT INTO users (full_name, email, role, status,password) VALUES (%s, %s, %s, %s, %s)"
        values = (full_name, email, role, status, password)
        cursor.execute(query, values)
        
        # Get the newly inserted user_id
        user_id = cursor.lastrowid
        roleQuery=""
        if(role == "Veterinarian"):
            roleQuery = "INSERT INTO veterinarians (user_id, specialization, phone, clinic_address) VALUES (%s, %s, %s, %s)"
            values = (user_id, specialization, phone, address)
        elif(role == "Pet Owner"):
            roleQuery = "INSERT INTO owners (user_id, phone, address) VALUES (%s, %s, %s)"
            values = (user_id, phone, address)
        if(roleQuery):
            cursor.execute(roleQuery, values)
        flash("New " + role + " has been added", "success")
        conn.commit()
    except mysql.connector.Error as e:
        conn.rollback()
        flash("Something went wrong", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for("manage_users"))


@app.route("/manage_edit_user", methods=["POST"])
@role_required("Admin")
def manage_edit_users():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get form data
        user_id = request.form["user_id"]
        full_name = request.form["full_name"]
        role = request.form["role"]
        status = request.form["status"]
        phone = request.form.get("phone")
        specialization = request.form.get("specialization")
        address = request.form.get("address")
        password = request.form.get("password")

        # --- Update users table ---
        query = "UPDATE users SET full_name = %s, role = %s, status = %s"
        values = [full_name, role, status]

        if password:  # optional password update
            query += ", password = %s"
            values.append(generate_password_hash(password))

        query += " WHERE user_id = %s"
        values.append(user_id)

        cursor.execute(query, tuple(values))

        # --- Update role-specific table ---
        if role == "Veterinarian":
            # Check if entry exists
            cursor.execute("SELECT * FROM veterinarians WHERE user_id = %s", (user_id,))
            vet = cursor.fetchone()
            if vet:
                # Update existing
                cursor.execute(
                    "UPDATE veterinarians SET specialization = %s, phone = %s, clinic_address = %s WHERE user_id = %s",
                    (specialization, phone, address, user_id)
                )
            else:
                # Insert new
                cursor.execute(
                    "INSERT INTO veterinarians (user_id, specialization, phone, clinic_address) VALUES (%s, %s, %s, %s)",
                    (user_id, specialization, phone, address)
                )
        elif role == "Pet Owner":
            # Check if entry exists
            cursor.execute("SELECT * FROM owners WHERE user_id = %s", (user_id,))
            owner = cursor.fetchone()
            if owner:
                # Update existing
                cursor.execute(
                    "UPDATE owners SET phone = %s, address = %s WHERE user_id = %s",
                    (phone, address, user_id)
                )
            else:
                # Insert new
                cursor.execute(
                    "INSERT INTO owners (user_id, phone, address) VALUES (%s, %s, %s)",
                    (user_id, phone, address)
                )

        # Commit everything at once
        conn.commit()
        flash("User updated successfully", "success")

    except mysql.connector.Error as e:
        conn.rollback()
        print("MySQL Error:", e)
        flash("Something went wrong", "danger")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("manage_users"))

@app.route("/manage_delete_user", methods=["DELETE"])
@role_required("Admin")
def manage_delete_users():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        # cursor.execute("DELETE FROM users WHERE user_id =%s", (user_id,))
        cursor.execute(
            "UPDATE users SET vchr_status ='D' WHERE user_id =%s", (user_id,)
        )
        conn.commit()
        return jsonify({"success": True, "message": "User deleted successfully"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"success": False, "message": "Something went wrong"}), 500
    finally:
        cursor.close()
        conn.close()


# ----- List all pets -----

@app.route("/managepets", defaults={"pet_id": None})
@app.route("/managepets/<int:pet_id>")
# @app.route("/managepets")
@role_required("Admin","Pet Owner")
def manage_pets(pet_id):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        user_id = session["user_id"]
        query = """
            SELECT pt.*, usr.full_name AS owner_name
            FROM pets pt
            LEFT JOIN owners owr ON pt.owner_id = owr.owner_id
            LEFT JOIN users usr ON usr.user_id = owr.user_id
        """
        params = []
        if session["role"] == "Pet Owner":
            query += " WHERE owr.user_id = %s"
            params.append(user_id)

            if pet_id is not None:
                query += " AND pt.pet_id = %s"
                params.append(pet_id)
                
        elif pet_id is not None:
            query += " WHERE pt.pet_id = %s"
            params.append(pet_id)
            
        cursor.execute(query, tuple(params))
        pets = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return render_template("dashboard/admin_dashboard/managepets.html", pets=pets)



@app.route("/manage_add_pet", methods=["POST"])
@role_required("Admin", "Pet Owner")
def manage_add_pet():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        # For Pet Owner role, get owner_id from session
        if session["role"] == "Pet Owner":
            owner_id = session["user_id"]
            cursor.execute("SELECT owner_id FROM owners WHERE user_id = %s", (session["user_id"],))
            owner_data = cursor.fetchone()
            owner_id = owner_data["owner_id"] if owner_data else None
        else:
            owner_id = request.form["owner_id"]
        name = request.form["name"]
        breed = request.form["breed"]
        age = request.form["age"]
        gender = request.form["gender"]
        medical_history = request.form.get("medical_history")
        
        # Handle file upload
        file = request.files.get("image")
        image_path = ""
        if file and file.filename and allowed_file(file.filename):
            # Check file size (5MB limit)
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            if file_size > 5 * 1024 * 1024:
                flash("File size must not exceed 5MB", "danger")
                return redirect(url_for("manage_pets"))
            
            filename = secure_filename(file.filename)
            # Create unique filename to avoid conflicts
            import time
            filename = f"{int(time.time())}_{filename}"
            pets_folder = os.path.join(UPLOAD_FOLDER, 'pets')
            os.makedirs(pets_folder, exist_ok=True)
            file.save(os.path.join(pets_folder, filename))
            # Store relative path for database
            image_path = f"uploads/pets/{filename}"

        query = """
            INSERT INTO pets (owner_id, name, breed, age, gender, medical_history, image)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (owner_id, name, breed, age, gender, medical_history, image_path)
        cursor.execute(query, values)
        conn.commit()
        flash("Pet added successfully", "success")
    except mysql.connector.Error as e:
        conn.rollback()
        print("MySQL Error:", e)
        flash("Something went wrong", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("manage_pets"))



@app.route("/manage_edit_pet", methods=["POST"])
@role_required("Admin", "Pet Owner")
def manage_edit_pet():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        pet_id = request.form["pet_id"]
        # For Pet Owner role, get owner_id from session
        if session["role"] == "Pet Owner":
            cursor.execute("SELECT owner_id FROM owners WHERE user_id = %s", (session["user_id"],))
            owner_data = cursor.fetchone()
            owner_id = owner_data["owner_id"] if owner_data else None
        else:
            owner_id = request.form["owner_id"]
        name = request.form["name"]
        breed = request.form["breed"]
        age = request.form["age"]
        gender = request.form["gender"]
        medical_history = request.form.get("medical_history")

        # Handle file upload
        file = request.files.get("image")
        image_path = None
        if file and file.filename and allowed_file(file.filename):
            # Check file size (5MB limit)
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            if file_size > 5 * 1024 * 1024:
                flash("File size must not exceed 5MB", "danger")
                return redirect(url_for("manage_pets"))
            
            filename = secure_filename(file.filename)
            # Create unique filename to avoid conflicts
            import time
            filename = f"{int(time.time())}_{filename}"
            pets_folder = os.path.join(UPLOAD_FOLDER, 'pets')
            os.makedirs(pets_folder, exist_ok=True)
            file.save(os.path.join(pets_folder, filename))
            image_path = f"uploads/pets/{filename}"

        query = """
            UPDATE pets
            SET owner_id = %s, name = %s, breed = %s, age = %s, gender = %s,
                medical_history = %s
        """
        values = [owner_id, name, breed, age, gender, medical_history]

        if image_path:
            query += ", image = %s"
            values.append(image_path)

        query += " WHERE pet_id = %s"
        values.append(pet_id)

        cursor.execute(query, tuple(values))
        conn.commit()
        flash("Pet updated successfully", "success")
    except mysql.connector.Error as e:
        conn.rollback()
        print("MySQL Error:", e)
        flash("Something went wrong", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("manage_pets"))


@app.route("/manage_delete_pet", methods=["DELETE"])
@role_required("Admin")
def manage_delete_pet():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        data = request.get_json()
        pet_id = data.get("pet_id")
        
        # Delete the pet record
        cursor.execute(
            "DELETE FROM pets WHERE pet_id = %s", (pet_id,)
        )
        conn.commit()
        return jsonify({"success": True, "message": "Pet deleted successfully"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"success": False, "message": "Something went wrong"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/profile", methods=["GET"])
@role_required("Admin","Pet Owner","Veterinarian")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        user_id = session["user_id"]
        role = session["role"]
        
        # Get user basic info
        cursor.execute("SELECT user_id AS user_id, full_name AS full_name, email AS email, role AS role, status AS status, DATE_FORMAT(created_at, '%d %M %Y') AS created_at FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        # Get role-specific info
        if role == "Pet Owner":
            cursor.execute("SELECT phone, address FROM owners WHERE user_id = %s", (user_id,))
            role_data = cursor.fetchone()
        elif role == "Veterinarian":
            cursor.execute("SELECT phone, clinic_address as address, specialization FROM veterinarians WHERE user_id = %s", (user_id,))
            role_data = cursor.fetchone()
        else:
            role_data = {}
        
        # Merge data
        profile = {**user, **(role_data or {})}
        
    finally:
        cursor.close()
        conn.close()
    
    return render_template("dashboard/profile.html", objProfile=profile)

@app.route("/update_profile", methods=["POST"])
@role_required("Admin","Pet Owner","Veterinarian")
def update_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        user_id = session["user_id"]
        role = session["role"]
        
        full_name = request.form["full_name"]
        phone = request.form.get("phone")
        address = request.form.get("address")
        specialization = request.form.get("specialization")
        password = request.form.get("password")
        
        # Update users table
        query = "UPDATE users SET full_name = %s"
        values = [full_name]
        
        if password:
            query += ", password = %s"
            values.append(generate_password_hash(password))
        
        query += " WHERE user_id = %s"
        values.append(user_id)
        cursor.execute(query, values)
        
        # Update role-specific table
        if role == "Pet Owner":
            cursor.execute("SELECT * FROM owners WHERE user_id = %s", (user_id,))
            if cursor.fetchone():
                cursor.execute("UPDATE owners SET phone = %s, address = %s WHERE user_id = %s", (phone, address, user_id))
            else:
                cursor.execute("INSERT INTO owners (user_id, phone, address) VALUES (%s, %s, %s)", (user_id, phone, address))
        elif role == "Veterinarian":
            cursor.execute("SELECT * FROM veterinarians WHERE user_id = %s", (user_id,))
            if cursor.fetchone():
                cursor.execute("UPDATE veterinarians SET phone = %s, clinic_address = %s, specialization = %s WHERE user_id = %s", (phone, address, specialization, user_id))
            else:
                cursor.execute("INSERT INTO veterinarians (user_id, phone, clinic_address, specialization) VALUES (%s, %s, %s, %s)", (user_id, phone, address, specialization))
        
        conn.commit()
        flash("Profile updated successfully", "success")
        
    except mysql.connector.Error as e:
        conn.rollback()
        flash("Something went wrong", "danger")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for("profile"))

@app.route("/delete_account", methods=["DELETE"])
@role_required("Admin","Pet Owner","Veterinarian")
def delete_account():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        user_id = session["user_id"]
        cursor.execute("UPDATE users SET vchr_status = 'D' WHERE user_id = %s", (user_id,))
        conn.commit()
        session.clear()
        return jsonify({"success": True, "message": "Account deleted successfully"})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"success": False, "message": "Something went wrong"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/book_appointment", methods=["GET", "POST"])
@role_required("Pet Owner")
def book_appointment():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    pets = []
    try:
        # Get owner's pets
        cursor.execute("SELECT owner_id FROM owners WHERE user_id = %s", (session["user_id"],))
        owner_data = cursor.fetchone()
        if owner_data:
            cursor.execute("SELECT * FROM pets WHERE owner_id = %s", (owner_data["owner_id"],))
            pets = cursor.fetchall()
            
    finally:
        cursor.close()
        conn.close()
    if request.method == "GET":
        return render_template("appointments/book.html", pets=pets)
    
    # POST - Book appointment
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        pet_id = request.form["pet_id"]
        vet_id = request.form["vet_id"]
        appointment_date = request.form["appointment_date"]
        appointment_time = request.form["appointment_time"]
        
        # Get owner_id
        cursor.execute("SELECT owner_id FROM owners WHERE user_id = %s", (session["user_id"],))
        owner_data = cursor.fetchone()
        
        # Combine date and time
        appointment_datetime = f"{appointment_date} {appointment_time}"
        
        # Check for conflicts (30-minute slots)
        cursor.execute("""
            SELECT * FROM appointments 
            WHERE vet_id = %s AND appointment_date BETWEEN 
            DATE_SUB(%s, INTERVAL 30 MINUTE) AND DATE_ADD(%s, INTERVAL 30 MINUTE)
            AND status != 'Cancelled'
        """, (vet_id, appointment_datetime, appointment_datetime))
        
        if cursor.fetchone():
            flash("Time slot not available. Please choose another time.", "danger")
            # Get vet name for display
            cursor.execute("SELECT u.full_name FROM users u JOIN veterinarians v ON u.user_id = v.user_id WHERE v.vet_id = %s", (vet_id,))
            vet_data = cursor.fetchone()
            vet_name = vet_data["full_name"] if vet_data else ""
            return render_template("appointments/book.html", pets=pets, pet_id=pet_id, vet_id=vet_id, vet_name=vet_name, appointment_date=appointment_date, appointment_time=appointment_time)
        
        # Book appointment
        cursor.execute("""
            INSERT INTO appointments (pet_id, owner_id, vet_id, appointment_date)
            VALUES (%s, %s, %s, %s)
        """, (pet_id, owner_data["owner_id"], vet_id, appointment_datetime))
        
        conn.commit()
        flash("Appointment booked successfully!", "success")
        
    except mysql.connector.Error as e:
        print(e)
        conn.rollback()
        flash("Something went wrong", "danger")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for("view_appointments"))

@app.route("/appointments")
@role_required("Admin", "Veterinarian", "Pet Owner")
def view_appointments():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        if session["role"] == "Admin":
            # Admin sees all appointments
            cursor.execute("""
                SELECT a.*, p.name as pet_name, u.full_name as owner_name, v_user.full_name as vet_name
                FROM appointments a
                JOIN pets p ON a.pet_id = p.pet_id
                JOIN owners o ON a.owner_id = o.owner_id
                JOIN users u ON o.user_id = u.user_id
                JOIN veterinarians v ON a.vet_id = v.vet_id
                JOIN users v_user ON v.user_id = v_user.user_id
                ORDER BY a.appointment_date DESC
            """)
            appointments = cursor.fetchall()
        elif session["role"] == "Veterinarian":
            # Get vet_id
            cursor.execute("SELECT vet_id FROM veterinarians WHERE user_id = %s", (session["user_id"],))
            vet_data = cursor.fetchone()
            
            if vet_data:
                cursor.execute("""
                    SELECT a.*, p.name as pet_name, u.full_name as owner_name
                    FROM appointments a
                    JOIN pets p ON a.pet_id = p.pet_id
                    JOIN owners o ON a.owner_id = o.owner_id
                    JOIN users u ON o.user_id = u.user_id
                    WHERE a.vet_id = %s
                    ORDER BY a.appointment_date DESC
                """, (vet_data["vet_id"],))
                appointments = cursor.fetchall()
            else:
                appointments = []
        else:  # Pet Owner
            # Get owner_id
            cursor.execute("SELECT owner_id FROM owners WHERE user_id = %s", (session["user_id"],))
            owner_data = cursor.fetchone()
            
            if owner_data:
                cursor.execute("""
                    SELECT a.*, p.name as pet_name, u.full_name as vet_name, v.specialization
                    FROM appointments a
                    JOIN pets p ON a.pet_id = p.pet_id
                    JOIN veterinarians v ON a.vet_id = v.vet_id
                    JOIN users u ON v.user_id = u.user_id
                    WHERE a.owner_id = %s
                    ORDER BY a.appointment_date DESC
                """, (owner_data["owner_id"],))
                appointments = cursor.fetchall()
            else:
                appointments = []
            
    finally:
        cursor.close()
        conn.close()
    
    if session["role"] == "Admin":
        template = "appointments/admin_list.html"
    elif session["role"] == "Veterinarian":
        template = "appointments/calender.html"
    else:
        template = "appointments/list.html"
    return render_template(template, appointments=appointments)

@app.route("/pet_medical/<int:pet_id>")
@role_required("Veterinarian")
def pet_medical(pet_id):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get pet info
        cursor.execute("SELECT * FROM pets WHERE pet_id = %s", (pet_id,))
        pet = cursor.fetchone()
        
        # Get vaccinations
        cursor.execute("SELECT * FROM vaccinations WHERE pet_id = %s ORDER BY date_given DESC", (pet_id,))
        vaccinations = cursor.fetchall()
        
        # Get medications
        cursor.execute("SELECT * FROM medications WHERE pet_id = %s ORDER BY start_date DESC", (pet_id,))
        medications = cursor.fetchall()
        
    finally:
        cursor.close()
        conn.close()
    
    return render_template("medical/pet_medical.html", pet=pet, vaccinations=vaccinations, medications=medications)

@app.route("/add_vaccination", methods=["POST"])
@role_required("Veterinarian")
def add_vaccination():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get vet_id
        cursor.execute("SELECT vet_id FROM veterinarians WHERE user_id = %s", (session["user_id"],))
        vet_data = cursor.fetchone()
        
        pet_id = request.form["pet_id"]
        vaccine_name = request.form["vaccine_name"]
        date_given = request.form["date_given"]
        next_due_date = request.form.get("next_due_date") or None
        notes = request.form.get("notes")
        
        cursor.execute("""
            INSERT INTO vaccinations (pet_id, vet_id, vaccine_name, date_given, next_due_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (pet_id, vet_data["vet_id"], vaccine_name, date_given, next_due_date, notes))
        
        # Auto-complete today's appointments for this pet and vet
        cursor.execute("""
            UPDATE appointments SET status = 'Completed' 
            WHERE pet_id = %s AND vet_id = %s AND DATE(appointment_date) = CURDATE() 
            AND status != 'Cancelled'
        """, (pet_id, vet_data["vet_id"]))
        
        conn.commit()
        flash("Vaccination record added successfully!", "success")
        
    except mysql.connector.Error as e:
        conn.rollback()
        flash("Something went wrong", "danger")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for("pet_medical", pet_id=pet_id))

@app.route("/add_medication", methods=["POST"])
@role_required("Veterinarian")
def add_medication():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get vet_id
        cursor.execute("SELECT vet_id FROM veterinarians WHERE user_id = %s", (session["user_id"],))
        vet_data = cursor.fetchone()
        
        pet_id = request.form["pet_id"]
        medicine_name = request.form["medicine_name"]
        dosage = request.form["dosage"]
        start_date = request.form["start_date"]
        end_date = request.form.get("end_date") or None
        notes = request.form.get("notes")
        
        cursor.execute("""
            INSERT INTO medications (pet_id, vet_id, medicine_name, dosage, start_date, end_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (pet_id, vet_data["vet_id"], medicine_name, dosage, start_date, end_date, notes))
        
        # Auto-complete today's appointments for this pet and vet
        cursor.execute("""
            UPDATE appointments SET status = 'Completed' 
            WHERE pet_id = %s AND vet_id = %s AND DATE(appointment_date) = CURDATE() 
            AND status != 'Cancelled'
        """, (pet_id, vet_data["vet_id"]))
        
        conn.commit()
        flash("Medication record added successfully!", "success")
        
    except mysql.connector.Error as e:
        conn.rollback()
        flash("Something went wrong", "danger")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for("pet_medical", pet_id=pet_id))

@app.route("/admin_medical")
@role_required("Admin")
def admin_medical():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get all vaccinations
        cursor.execute("""
            SELECT v.*, p.name as pet_name, u.full_name as vet_name, o.full_name as owner_name
            FROM vaccinations v
            JOIN pets p ON v.pet_id = p.pet_id
            JOIN veterinarians vet ON v.vet_id = vet.vet_id
            JOIN users u ON vet.user_id = u.user_id
            JOIN owners o_tbl ON p.owner_id = o_tbl.owner_id
            JOIN users o ON o_tbl.user_id = o.user_id
            ORDER BY v.date_given DESC
        """)
        vaccinations = cursor.fetchall()
        
        # Get all medications
        cursor.execute("""
            SELECT m.*, p.name as pet_name, u.full_name as vet_name, o.full_name as owner_name
            FROM medications m
            JOIN pets p ON m.pet_id = p.pet_id
            JOIN veterinarians vet ON m.vet_id = vet.vet_id
            JOIN users u ON vet.user_id = u.user_id
            JOIN owners o_tbl ON p.owner_id = o_tbl.owner_id
            JOIN users o ON o_tbl.user_id = o.user_id
            ORDER BY m.start_date DESC
        """)
        medications = cursor.fetchall()
        
    finally:
        cursor.close()
        conn.close()
    
    return render_template("medical/admin_medical.html", vaccinations=vaccinations, medications=medications)

@app.route("/vaccinations")
@role_required("Admin", "Veterinarian")
def view_vaccinations():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        if session["role"] == "Admin":
            # Admin sees all vaccinations
            cursor.execute("""
                SELECT v.*, p.name as pet_name, u.full_name as vet_name, o.full_name as owner_name
                FROM vaccinations v
                JOIN pets p ON v.pet_id = p.pet_id
                JOIN veterinarians vet ON v.vet_id = vet.vet_id
                JOIN users u ON vet.user_id = u.user_id
                JOIN owners o_tbl ON p.owner_id = o_tbl.owner_id
                JOIN users o ON o_tbl.user_id = o.user_id
                ORDER BY v.date_given DESC
            """)
        else:  # Veterinarian
            # Vet sees only their vaccinations
            cursor.execute("SELECT vet_id FROM veterinarians WHERE user_id = %s", (session["user_id"],))
            vet_data = cursor.fetchone()
            
            if vet_data:
                cursor.execute("""
                    SELECT v.*, p.name as pet_name, o.full_name as owner_name
                    FROM vaccinations v
                    JOIN pets p ON v.pet_id = p.pet_id
                    JOIN owners o_tbl ON p.owner_id = o_tbl.owner_id
                    JOIN users o ON o_tbl.user_id = o.user_id
                    WHERE v.vet_id = %s
                    ORDER BY v.date_given DESC
                """, (vet_data["vet_id"],))
            else:
                cursor.execute("SELECT * FROM vaccinations WHERE 1=0")  # Empty result
        
        vaccinations = cursor.fetchall()
        
    finally:
        cursor.close()
        conn.close()
    
    return render_template("medical/vaccinations.html", vaccinations=vaccinations)

@app.route("/medications")
@role_required("Admin", "Veterinarian")
def view_medications():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        if session["role"] == "Admin":
            # Admin sees all medications
            cursor.execute("""
                SELECT m.*, p.name as pet_name, u.full_name as vet_name, o.full_name as owner_name
                FROM medications m
                JOIN pets p ON m.pet_id = p.pet_id
                JOIN veterinarians vet ON m.vet_id = vet.vet_id
                JOIN users u ON vet.user_id = u.user_id
                JOIN owners o_tbl ON p.owner_id = o_tbl.owner_id
                JOIN users o ON o_tbl.user_id = o.user_id
                ORDER BY m.start_date DESC
            """)
        else:  # Veterinarian
            # Vet sees only their medications
            cursor.execute("SELECT vet_id FROM veterinarians WHERE user_id = %s", (session["user_id"],))
            vet_data = cursor.fetchone()
            
            if vet_data:
                cursor.execute("""
                    SELECT m.*, p.name as pet_name, o.full_name as owner_name
                    FROM medications m
                    JOIN pets p ON m.pet_id = p.pet_id
                    JOIN owners o_tbl ON p.owner_id = o_tbl.owner_id
                    JOIN users o ON o_tbl.user_id = o.user_id
                    WHERE m.vet_id = %s
                    ORDER BY m.start_date DESC
                """, (vet_data["vet_id"],))
            else:
                cursor.execute("SELECT * FROM medications WHERE 1=0")  # Empty result
        
        medications = cursor.fetchall()
        
    finally:
        cursor.close()
        conn.close()
    
    return render_template("medical/medications.html", medications=medications)

@app.route("/update_appointment_status", methods=["POST"])
@role_required("Veterinarian")
def update_appointment_status():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        data = request.get_json()
        appointment_id = data.get("appointment_id")
        status = data.get("status")
        
        # Verify appointment belongs to this vet
        cursor.execute("SELECT vet_id FROM veterinarians WHERE user_id = %s", (session["user_id"],))
        vet_data = cursor.fetchone()
        
        cursor.execute("SELECT * FROM appointments WHERE appointment_id = %s AND vet_id = %s", 
                      (appointment_id, vet_data["vet_id"]))
        appointment = cursor.fetchone()
        
        if not appointment:
            return jsonify({"success": False, "message": "Appointment not found"}), 404
        
        cursor.execute("UPDATE appointments SET status = %s WHERE appointment_id = %s", 
                      (status, appointment_id))
        conn.commit()
        
        return jsonify({"success": True, "message": f"Appointment marked as {status}"})
        
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"success": False, "message": "Something went wrong"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/cancel_appointment", methods=["POST"])
@role_required("Pet Owner")
def cancel_appointment():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        data = request.get_json()
        appointment_id = data.get("appointment_id")
        
        # Verify appointment belongs to this owner
        cursor.execute("SELECT owner_id FROM owners WHERE user_id = %s", (session["user_id"],))
        owner_data = cursor.fetchone()
        
        cursor.execute("SELECT * FROM appointments WHERE appointment_id = %s AND owner_id = %s", 
                      (appointment_id, owner_data["owner_id"]))
        appointment = cursor.fetchone()
        
        if not appointment:
            return jsonify({"success": False, "message": "Appointment not found"}), 404
        
        if appointment["status"] != "Pending":
            return jsonify({"success": False, "message": "Can only cancel pending appointments"}), 400
        
        cursor.execute("UPDATE appointments SET status = 'Cancelled' WHERE appointment_id = %s", 
                      (appointment_id,))
        conn.commit()
        
        return jsonify({"success": True, "message": "Appointment cancelled successfully"})
        
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"success": False, "message": "Something went wrong"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/autocomplete_users", methods=["GET"])
def autocomplete_users():
    role = request.args.get("role", "")
    query = request.args.get("q", "")

    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        # For Pet Owner role, we need to get owner_id from owners table
        if role == "Pet Owner":
            sql = """
                SELECT u.user_id, u.full_name, u.email, o.owner_id
                FROM users u
                JOIN owners o ON u.user_id = o.user_id
                WHERE u.role = "Pet Owner" AND u.full_name LIKE %s AND u.vchr_status = 'A'
                LIMIT 10
            """
            cursor.execute(sql, (f"%{query}%",))
            results = cursor.fetchall()
            # Replace user_id with owner_id for pet ownership
            for result in results:
                result['user_id'] = result['owner_id']
        elif role == "Veterinarian":
            sql = """
                SELECT u.user_id, u.full_name, u.email, v.specialization,v.vet_id
                FROM users u
                JOIN veterinarians v ON u.user_id = v.user_id
                WHERE u.role = "Veterinarian" AND u.full_name LIKE %s AND u.vchr_status = 'A'
                LIMIT 10
            """
            cursor.execute(sql, (f"%{query}%",))
            results = cursor.fetchall()
        else:
            sql = """
                SELECT user_id, full_name, email 
                FROM users 
                WHERE role = %s AND full_name LIKE %s AND vchr_status = 'A'
                LIMIT 10
            """
            cursor.execute(sql, (role, f"%{query}%"))
            results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

# ---------- MAIN ----------
if __name__ == "__main__":
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    objAdmin = {
        "full_name": "admin",
        "password": "test123",
        "email": "admin@petcare.in",
        "role": "Admin",
        "status": "Active",
    }
    cur.execute("SELECT * FROM users WHERE full_name = %s", (objAdmin["full_name"],))
    user = cur.fetchone()
    if not user:
        try:
            print("inserting default admin")
            hashedPassword = generate_password_hash(objAdmin["password"])
            cur.execute(
                "INSERT INTO users (full_name, password, email, role) VALUES (%s, %s, %s, %s)",
                (
                    objAdmin["full_name"],
                    hashedPassword,
                    objAdmin["email"],
                    objAdmin["role"],
                ),
            )
            conn.commit()
        except mysql.connector.Error as e:
            conn.rollback()
            cur.close()
            conn.close()
    else:
        print("default admin already added")
    cur.close()
    conn.close()
    app.run(debug=True)
