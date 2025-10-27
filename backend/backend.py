# Import all the libraries we need for our web application
from flask import (
    Flask,              # Main web framework - creates our web app
    render_template,    # Shows HTML pages to users
    request,           # Gets data from forms and URLs
    jsonify,           # Sends JSON responses (data format)
    send_from_directory, # Serves files like images
    redirect,          # Sends users to different pages
    flash,             # Shows temporary messages to users
    session,           # Remembers user login information
    url_for,           # Creates URLs for our pages
)
from flask_cors import CORS        # Allows frontend and backend to communicate
import mysql.connector             # Connects to MySQL database
from werkzeug.security import generate_password_hash, check_password_hash  # Password security
from dotenv import load_dotenv      # Loads secret settings from .env file
import os                          # Works with files and folders
from functools import wraps        # Helps create decorators (special functions)
from werkzeug.utils import secure_filename  # Makes uploaded filenames safe


# Load secret database settings from .env file (keeps passwords safe)
load_dotenv()

# Get database connection details from .env file
# If not found, use default values
DB_HOST = os.getenv("DB_HOST", "localhost")  # Database server location
DB_USER = os.getenv("DB_USER", "root")       # Database username
DB_PASS = os.getenv("DB_PASS", "root")       # Database password
DB_NAME = os.getenv("DB_NAME", "petcare")    # Database name

# app = Flask(_name_, template_folder=template_dir)
# CORS(app)

# Find where this Python file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Set up paths to our HTML templates and CSS/JS files
# Go one level up from backend folder, then into frontend folder
template_dir = os.path.join(BASE_DIR, "..", "frontend")  # Where HTML files are
static_dir = os.path.join(BASE_DIR, "..", "frontend", "assets")  # Where CSS/JS files are

# Fix the paths so they work on Windows and other systems
template_dir = os.path.normpath(template_dir)
static_dir = os.path.normpath(static_dir)

print("Looking for templates in:", template_dir)  # Show where we're looking for HTML files

# Create our Flask web application
app = Flask(
    __name__,                          # Name of our app
    template_folder=template_dir,      # Where to find HTML files
    static_folder=static_dir,          # Where to find CSS/JS files
    static_url_path="/assets",         # URL path for CSS/JS files
)

# Secret key needed for security (sessions and flash messages)
app.secret_key = "super_secret_key"


# Set up file upload settings
UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'static', 'uploads')  # Where to save uploaded files
UPLOAD_FOLDER = os.path.normpath(UPLOAD_FOLDER)  # Fix path for different operating systems
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}  # Only allow these image types

# Configure Flask app for file uploads
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER  # Tell Flask where to save files
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # Maximum file size: 5 MB

# Create the upload folder if it doesn't exist yet
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)  # Create the folder

# Function to serve uploaded files (like pet images) to users
@app.route('/static/<path:filename>')
def serve_static(filename):
    """This function sends uploaded files to users when they request them"""
    static_root = os.path.join(BASE_DIR, '..', 'static')  # Find static files folder
    static_root = os.path.normpath(static_root)  # Fix path
    return send_from_directory(static_root, filename)  # Send the requested file

def get_conn():
    """Create a connection to our MySQL database"""
    return mysql.connector.connect(
        host=DB_HOST,      # Database server location
        user=DB_USER,      # Username
        password=DB_PASS,  # Password
        database=DB_NAME   # Database name
    )

def allowed_file(filename):
    """Check if uploaded file has an allowed extension (png, jpg, etc.)"""
    # Check if filename has a dot AND the extension is in our allowed list
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Page to show when users try to access something they're not allowed to
@app.route("/404", methods=["GET"])
def logaccessdenied():
    """Show access denied page when user doesn't have permission"""
    return render_template("dashboard/accessdenied.html")

# Security decorator - checks if user has the right role to access a page
def role_required(*roles):
    """This is a decorator that protects pages - only certain user roles can access them"""
    def wrapper(fn):  # Wrapper function
        @wraps(fn)    # Preserves original function info
        def decorated(*args, **kwargs):  # The actual protection logic
            # Check if user is logged in
            if "user_id" not in session:
                return redirect(url_for("login"))  # Send to login page if not logged in
            
            # Check if user has the right role (Admin, Vet, or Pet Owner)
            if session.get("role") not in roles:
                return redirect(url_for("logaccessdenied"))  # Show access denied if wrong role
            
            # If user is logged in and has right role, let them access the page
            return fn(*args, **kwargs)
        return decorated
    return wrapper


# USER REGISTRATION - Let new users create accounts
@app.route("/register", methods=["GET", "POST"])
def register():
    """Handle user registration - both showing the form and processing it"""
    
    # If user just wants to see the registration form
    if request.method == "GET":
        return render_template("petcareFrontend/register.html")
    
    # If user submitted the registration form, process it
    data = request.form or {}  # Get form data, use empty dict if none
    
    # Extract all the information from the form
    full_name = data.get("full_name")           # User's full name
    email = data.get("email")                   # User's email address
    password = data.get("password")             # User's chosen password
    phone = data.get("phone") or ""             # Phone number (optional)
    specialization = data.get("specialization") or ""  # For vets only
    address = data.get("address") or ""         # Address (optional)
    confirm_password = data.get("confirm_password")  # Password confirmation
    role = data.get("role")                     # Admin, Vet, or Pet Owner
    
    # Check if required fields are filled
    if not (full_name and email and password):
        flash("Please fill in all required fields.", "danger")  # Show error message
        return render_template("petcareFrontend/register.html")
    
    # Check if passwords match
    if confirm_password != password:
        flash("Passwords don't match.", "danger")  # Show error message
        return render_template("petcareFrontend/register.html")

    # Connect to database
    conn = get_conn()
    cur = conn.cursor()

    # Check if email already exists in database
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user1 = cur.fetchone()  # Get first matching user

    # If email already exists, show error
    if user1:
        flash("This email is already registered. Please use a different email.", "danger")
        cur.close()    # Close database cursor
        conn.close()   # Close database connection
        return render_template("petcareFrontend/register.html")
    
    # Hash (encrypt) the password for security - never store plain passwords!
    hashed = generate_password_hash(password)
    try:
        # Insert new user into users table
        cur.execute(
            "INSERT INTO users (full_name, password, email, role) VALUES (%s, %s, %s, %s)",
            (full_name, hashed, email, role),  # Use hashed password, not plain text
        )
        
        # Get the ID of the user we just created
        user_id = cur.lastrowid
        
        # Depending on user role, add extra information to role-specific tables
        roleQuery = ""  # Start with empty query
        
        if role == "Veterinarian":
            # If user is a vet, add their info to veterinarians table
            roleQuery = "INSERT INTO veterinarians (user_id, specialization, phone, clinic_address) VALUES (%s, %s, %s, %s)"
            values = (user_id, specialization, phone, address)
        elif role == "Pet Owner":
            # If user is a pet owner, add their info to owners table
            roleQuery = "INSERT INTO owners (user_id, phone, address) VALUES (%s, %s, %s)"
            values = (user_id, phone, address)
        
        # Execute the role-specific query if we have one
        if roleQuery:
            cur.execute(roleQuery, values)
        
        # Save all changes to database
        conn.commit()
    except mysql.connector.Error as e:
        # If something goes wrong with database, undo all changes
        conn.rollback()  # Undo any changes
        cur.close()      # Close cursor
        conn.close()     # Close connection
        print(str(e))    # Print error for debugging
        flash("Something went wrong during registration. Please try again.", "danger")
        return render_template("petcareFrontend/register.html")

    # Close database connections
    cur.close()
    conn.close()
    
    # Show success message and redirect to login page
    flash("Registration successful! Please login with your new account.", "success")
    return redirect(url_for("login"))  # Send user to login page


# USER LOGIN - Let existing users sign into their accounts
@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login - both showing login form and checking credentials"""
    
    # If user just wants to see the login form
    if request.method == "GET":
        return render_template("petcareFrontend/index.html")
    
    # If user submitted login form, check their credentials
    data = request.form or {}  # Get form data
    email = data.get("email")        # User's email
    password = data.get("password")  # User's password
    
    # Make sure both email and password were provided
    if not (email and password):
        flash("Please enter both email and password.", "danger")
        return render_template("petcareFrontend/index.html")

    # Connect to database and look for user
    conn = get_conn()
    cur = conn.cursor(dictionary=True)  # dictionary=True means results come as dictionaries
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()  # Get the user with this email
    cur.close()
    conn.close()

    # If no user found with this email
    if not user:
        flash("Invalid email or password.", "danger")
        return render_template("petcareFrontend/index.html")

    # Check if the password is correct
    if check_password_hash(user["password"], password):
        # Password is correct! Log the user in by storing their info in session
        session["user_id"] = user["user_id"]      # Remember user's ID
        session["full_name"] = user["full_name"]  # Remember user's name
        session["role"] = user["role"]            # Remember user's role (Admin/Vet/Owner)
        
        # Send user to their dashboard
        return redirect(url_for("homePage"))
    else:
        # Password is wrong
        flash("Invalid email or password.", "danger")
        return render_template("petcareFrontend/index.html")


# FORGOT PASSWORD - Currently just shows the form (password reset not implemented yet)
@app.route("/forgot-password", methods=["GET", "POST"])
def forgotPassword():
    """Handle forgot password - currently just shows form, reset functionality not implemented"""
    if request.method == "GET":
        return render_template("petcareFrontend/forgot-password.html")
    
    # This is placeholder code - actual password reset would need email functionality
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")
    if not (email and password):
        return jsonify({"msg": "email and password required"}), 400
    return jsonify({"msg": "Invalid credentials"}), 401

# USER LOGOUT - Clear user's session and send them back to login
@app.route("/logout", methods=["GET"])
def logout():
    """Log user out by clearing their session data"""
    session.clear()  # Remove all session data (user_id, name, role, etc.)
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("login"))  # Send back to login page


# MAIN DASHBOARD - Shows different content based on user role
@app.route("/", methods=["GET"])
@role_required("Admin", "Pet Owner", "Veterinarian")  # Only logged-in users can access
def homePage():
    """Main dashboard - shows different content for Admin, Vet, and Pet Owner"""
    
    # Double-check user is logged in (role_required should handle this, but just in case)
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Get user's role and ID from their session
    role = session.get("role")      # Admin, Veterinarian, or Pet Owner
    user_id = session.get("user_id") # User's unique ID number
    
    # Connect to database to get dashboard data
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # ADMIN DASHBOARD - Show system statistics and recent activities
        if role == "Admin":
            # Count total active users (not deleted)
            cursor.execute("SELECT COUNT(*) as total_users FROM users WHERE vchr_status = 'A'")
            total_users = cursor.fetchone()["total_users"]
            
            # Count total pets in system
            cursor.execute("SELECT COUNT(*) as total_pets FROM pets")
            total_pets = cursor.fetchone()["total_pets"]
            
            # Count upcoming appointments (today and future)
            cursor.execute("SELECT COUNT(*) as total_appointments FROM appointments WHERE DATE(appointment_date) >= CURDATE()")
            total_appointments = cursor.fetchone()["total_appointments"]
            
            # Count total medical records (vaccinations + medications)
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
        # VETERINARIAN DASHBOARD - Show today's appointments and recent activities
        elif role == "Veterinarian":
            # First, get this vet's ID from the veterinarians table
            cursor.execute("SELECT vet_id FROM veterinarians WHERE user_id = %s", (user_id,))
            vet_data = cursor.fetchone()
            
            today_appointments = []  # Start with empty list
            
            if vet_data:  # If we found the vet's data
                # Get all of today's appointments for this vet
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
        # This code is now moved below in the PET OWNER DASHBOARD section
        
        # PET OWNER DASHBOARD - Show their pets and upcoming reminders
        # If we get here, user must be a Pet Owner (the only remaining role)
        
        # Get all pets owned by this user
        cursor.execute(
            """
                SELECT pt.*
                FROM pets pt
                LEFT JOIN owners owr ON pt.owner_id = owr.owner_id
                WHERE owr.user_id = %s
            """, (user_id,)
        )
        pets = cursor.fetchall()
        
        # Get upcoming reminders for medications and vaccinations
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
        
        # Show pet owner dashboard with their pets and reminders
        return render_template("dashboard/owner.html", 
                             pets=pets, 
                             upcoming_reminders=upcoming_reminders)
    finally:
        # Always close database connections, even if something goes wrong
        cursor.close()  # Close the cursor
        conn.close()    # Close the connection

# USER MANAGEMENT (ADMIN ONLY) - View all users in the system
@app.route("/manageusers", methods=["GET", "POST"])
@role_required("Admin")  # Only admins can manage users
def manage_users():
    """Show list of all users - only admins can access this"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    users = []  # Start with empty list
    
    try:
        # Get all active users with their role-specific information
        # This complex query joins users with owners and veterinarians tables
        cursor.execute(
            """
            SELECT 
            usr.user_id AS user_id,
            usr.full_name AS full_name,
            COALESCE(owr.owner_id, vet.vet_id) AS related_id,  -- Get either owner_id or vet_id
            usr.email AS email,
            usr.role AS role,
            usr.status AS status,
            vet.specialization AS specialization,  -- Only for vets
            CASE 
                WHEN usr.role = 'Pet Owner' THEN owr.phone
                WHEN usr.role = 'Veterinarian' THEN vet.phone
                ELSE NULL
            END AS phone,  -- Get phone from appropriate table based on role
            CASE 
                WHEN usr.role = 'Pet Owner' THEN owr.address
                WHEN usr.role = 'Veterinarian' THEN vet.clinic_address
                ELSE NULL
            END AS address  -- Get address from appropriate table based on role
            FROM users AS usr
            LEFT JOIN owners AS owr ON usr.user_id = owr.user_id
            LEFT JOIN veterinarians AS vet ON usr.user_id = vet.user_id
            WHERE usr.vchr_status = 'A'  -- Only get active users (not deleted)
            """
        )
        users = cursor.fetchall()  # Get all matching users

    except mysql.connector.Error as e:
        # If database error occurs, handle it gracefully
        conn.rollback()  # Undo any changes
        print(str(e))    # Print error for debugging

    finally:
        # Always close database connections
        cursor.close()
        conn.close()
    
    # Show the user management page with list of all users
    return render_template("dashboard/admin_dashboard/manageusers.html", users=users)


# ADD NEW USER (ADMIN ONLY) - Admin can create new user accounts
@app.route("/manage_add_user", methods=["POST"])
@role_required("Admin")  # Only admins can add users
def manage_add_users():
    """Admin function to add new users to the system"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all the form data from admin's input
        full_name = request.form["full_name"]        # New user's name
        email = request.form["email"]                # New user's email
        role = request.form["role"]                  # Admin, Vet, or Pet Owner
        status = request.form["status"]              # Active or Inactive
        phone = request.form["phone"]                # Phone number
        specialization = request.form["specialization"]  # For vets only
        address = request.form["address"]            # Address
        password = request.form["password"]          # Temporary password
        
        # Hash the password for security
        password = generate_password_hash(password)
        
        # Insert new user into main users table
        query = "INSERT INTO users (full_name, email, role, status, password) VALUES (%s, %s, %s, %s, %s)"
        values = (full_name, email, role, status, password)
        cursor.execute(query, values)
        
        # Get the ID of the user we just created
        user_id = cursor.lastrowid
        
        # Add role-specific information to appropriate table
        roleQuery = ""  # Start with empty query
        
        if role == "Veterinarian":
            # Add vet-specific info to veterinarians table
            roleQuery = "INSERT INTO veterinarians (user_id, specialization, phone, clinic_address) VALUES (%s, %s, %s, %s)"
            values = (user_id, specialization, phone, address)
        elif role == "Pet Owner":
            # Add owner-specific info to owners table
            roleQuery = "INSERT INTO owners (user_id, phone, address) VALUES (%s, %s, %s)"
            values = (user_id, phone, address)
        
        # Execute the role-specific query if we have one
        if roleQuery:
            cursor.execute(roleQuery, values)
        
        # Show success message
        flash(f"New {role} has been added successfully", "success")
        conn.commit()  # Save all changes to database
        
    except mysql.connector.Error as e:
        # If something goes wrong, undo all changes
        conn.rollback()
        flash("Something went wrong while adding user", "danger")
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()
    
    # Go back to user management page
    return redirect(url_for("manage_users"))


# EDIT EXISTING USER (ADMIN ONLY) - Admin can modify user accounts
@app.route("/manage_edit_user", methods=["POST"])
@role_required("Admin")  # Only admins can edit users
def manage_edit_users():
    """Admin function to edit existing user information"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all form data for the user being edited
        user_id = request.form["user_id"]            # Which user to edit
        full_name = request.form["full_name"]        # Updated name
        role = request.form["role"]                  # Updated role
        status = request.form["status"]              # Updated status
        phone = request.form.get("phone")            # Updated phone (optional)
        specialization = request.form.get("specialization")  # For vets (optional)
        address = request.form.get("address")        # Updated address (optional)
        password = request.form.get("password")      # New password (optional)

        # --- Update the main users table ---
        query = "UPDATE users SET full_name = %s, role = %s, status = %s"
        values = [full_name, role, status]

        # If admin provided a new password, include it in update
        if password:  # Only update password if one was provided
            query += ", password = %s"
            values.append(generate_password_hash(password))  # Hash the new password

        # Complete the query with WHERE clause
        query += " WHERE user_id = %s"
        values.append(user_id)

        # Execute the main users table update
        cursor.execute(query, tuple(values))

        # --- Update role-specific table (veterinarians or owners) ---
        if role == "Veterinarian":
            # Check if this user already has vet info in veterinarians table
            cursor.execute("SELECT * FROM veterinarians WHERE user_id = %s", (user_id,))
            vet = cursor.fetchone()
            
            if vet:
                # User already has vet record, so update it
                cursor.execute(
                    "UPDATE veterinarians SET specialization = %s, phone = %s, clinic_address = %s WHERE user_id = %s",
                    (specialization, phone, address, user_id)
                )
            else:
                # User doesn't have vet record yet, so create one
                cursor.execute(
                    "INSERT INTO veterinarians (user_id, specialization, phone, clinic_address) VALUES (%s, %s, %s, %s)",
                    (user_id, specialization, phone, address)
                )
                
        elif role == "Pet Owner":
            # Check if this user already has owner info in owners table
            cursor.execute("SELECT * FROM owners WHERE user_id = %s", (user_id,))
            owner = cursor.fetchone()
            
            if owner:
                # User already has owner record, so update it
                cursor.execute(
                    "UPDATE owners SET phone = %s, address = %s WHERE user_id = %s",
                    (phone, address, user_id)
                )
            else:
                # User doesn't have owner record yet, so create one
                cursor.execute(
                    "INSERT INTO owners (user_id, phone, address) VALUES (%s, %s, %s)",
                    (user_id, phone, address)
                )

        # Save all changes to database at once
        conn.commit()
        flash("User updated successfully", "success")

    except mysql.connector.Error as e:
        # If anything goes wrong, undo all changes
        conn.rollback()
        print("MySQL Error:", e)  # Print error for debugging
        flash("Something went wrong while updating user", "danger")

    finally:
        # Always close database connections
        cursor.close()
        conn.close()

    # Go back to user management page
    return redirect(url_for("manage_users"))

# DELETE USER (ADMIN ONLY) - Soft delete user (mark as deleted, don't actually remove)
@app.route("/manage_delete_user", methods=["DELETE"])
@role_required("Admin")  # Only admins can delete users
def manage_delete_users():
    """Admin function to soft-delete users (mark as deleted, don't actually remove from database)"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get user ID from JSON request (sent by JavaScript)
        data = request.get_json()
        user_id = data.get("user_id")
        
        # We don't actually DELETE the user from database (that would break relationships)
        # Instead, we mark them as deleted with 'D' status (soft delete)
        # cursor.execute("DELETE FROM users WHERE user_id =%s", (user_id,))  # Don't do this!
        
        # Soft delete: just change status to 'D' (deleted)
        cursor.execute(
            "UPDATE users SET vchr_status = 'D' WHERE user_id = %s", (user_id,)
        )
        
        conn.commit()  # Save the change
        
        # Send success response back to JavaScript
        return jsonify({"success": True, "message": "User deleted successfully"})
        
    except mysql.connector.Error as e:
        # If something goes wrong, undo changes
        conn.rollback()
        # Send error response back to JavaScript
        return jsonify({"success": False, "message": "Something went wrong"}), 500
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()


# ----- List all pets -----

# PET MANAGEMENT - View and manage pets (Admin sees all, Pet Owners see only their pets)
@app.route("/managepets", defaults={"pet_id": None})  # Default route without pet_id
@app.route("/managepets/<int:pet_id>")                # Route with specific pet_id
@role_required("Admin", "Pet Owner")  # Only admins and pet owners can manage pets
def manage_pets(pet_id):
    """Show list of pets - Admins see all pets, Pet Owners see only their own pets"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        user_id = session["user_id"]  # Get current user's ID
        
        # Base query to get pets with owner information
        query = """
            SELECT pt.*, usr.full_name AS owner_name
            FROM pets pt
            LEFT JOIN owners owr ON pt.owner_id = owr.owner_id
            LEFT JOIN users usr ON usr.user_id = owr.user_id
        """
        params = []  # Parameters for the query
        
        # If user is a Pet Owner, only show their pets
        if session["role"] == "Pet Owner":
            query += " WHERE owr.user_id = %s"  # Filter by owner
            params.append(user_id)

            # If looking for a specific pet, add that filter too
            if pet_id is not None:
                query += " AND pt.pet_id = %s"
                params.append(pet_id)
                
        # If user is Admin and looking for specific pet
        elif pet_id is not None:
            query += " WHERE pt.pet_id = %s"
            params.append(pet_id)
            
        # Execute the query with appropriate filters
        cursor.execute(query, tuple(params))
        pets = cursor.fetchall()  # Get all matching pets
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()
    
    # Show the pet management page with the list of pets
    return render_template("dashboard/admin_dashboard/managepets.html", pets=pets)



# ADD NEW PET - Create a new pet record with optional photo upload
@app.route("/manage_add_pet", methods=["POST"])
@role_required("Admin", "Pet Owner")  # Admins and pet owners can add pets
def manage_add_pet():
    """Add a new pet to the system with optional photo upload"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Determine who owns this pet
        if session["role"] == "Pet Owner":
            # Pet owners can only add pets for themselves
            # Get their owner_id from the owners table
            cursor.execute("SELECT owner_id FROM owners WHERE user_id = %s", (session["user_id"],))
            owner_data = cursor.fetchone()
            owner_id = owner_data["owner_id"] if owner_data else None
        else:
            # Admins can add pets for any owner (owner_id comes from form)
            owner_id = request.form["owner_id"]
        
        # Get pet information from the form
        name = request.form["name"]                      # Pet's name
        breed = request.form["breed"]                    # Pet's breed
        age = request.form["age"]                        # Pet's age
        gender = request.form["gender"]                  # Male or Female
        medical_history = request.form.get("medical_history")  # Optional medical history
        
        # Handle pet photo upload
        file = request.files.get("image")  # Get uploaded file
        image_path = ""  # Default to no image
        
        if file and file.filename and allowed_file(file.filename):
            # Check file size (must be under 5MB)
            file.seek(0, 2)  # Move to end of file
            file_size = file.tell()  # Get file size
            file.seek(0)  # Move back to beginning
            
            if file_size > 5 * 1024 * 1024:  # 5MB in bytes
                flash("File size must not exceed 5MB", "danger")
                return redirect(url_for("manage_pets"))
            
            # Make filename safe and unique
            filename = secure_filename(file.filename)  # Remove dangerous characters
            
            # Add timestamp to avoid filename conflicts
            import time
            filename = f"{int(time.time())}_{filename}"
            
            # Create pets folder if it doesn't exist
            pets_folder = os.path.join(UPLOAD_FOLDER, 'pets')
            os.makedirs(pets_folder, exist_ok=True)
            
            # Save the file
            file.save(os.path.join(pets_folder, filename))
            
            # Store relative path in database (not full system path)
            image_path = f"uploads/pets/{filename}"

        # Insert new pet into database
        query = """
            INSERT INTO pets (owner_id, name, breed, age, gender, medical_history, image)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (owner_id, name, breed, age, gender, medical_history, image_path)
        cursor.execute(query, values)
        
        conn.commit()  # Save changes
        flash("Pet added successfully", "success")
        
    except mysql.connector.Error as e:
        # If database error, undo changes
        conn.rollback()
        print("MySQL Error:", e)  # Print for debugging
        flash("Something went wrong while adding pet", "danger")
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()

    # Go back to pet management page
    return redirect(url_for("manage_pets"))



# EDIT EXISTING PET - Update pet information with optional new photo
@app.route("/manage_edit_pet", methods=["POST"])
@role_required("Admin", "Pet Owner")  # Admins and pet owners can edit pets
def manage_edit_pet():
    """Edit existing pet information with optional photo update"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        pet_id = request.form["pet_id"]  # Which pet to edit
        
        # Determine ownership (Pet owners can only edit their own pets)
        if session["role"] == "Pet Owner":
            # Get owner_id for pet owners
            cursor.execute("SELECT owner_id FROM owners WHERE user_id = %s", (session["user_id"],))
            owner_data = cursor.fetchone()
            owner_id = owner_data["owner_id"] if owner_data else None
        else:
            # Admins can edit pets for any owner
            owner_id = request.form["owner_id"]
        
        # Get updated pet information from form
        name = request.form["name"]                      # Updated name
        breed = request.form["breed"]                    # Updated breed
        age = request.form["age"]                        # Updated age
        gender = request.form["gender"]                  # Updated gender
        medical_history = request.form.get("medical_history")  # Updated medical history

        # Handle optional new photo upload
        file = request.files.get("image")  # Get uploaded file (if any)
        image_path = None  # Default to no new image
        
        if file and file.filename and allowed_file(file.filename):
            # Check file size (must be under 5MB)
            file.seek(0, 2)  # Move to end of file
            file_size = file.tell()  # Get file size
            file.seek(0)  # Move back to beginning
            
            if file_size > 5 * 1024 * 1024:  # 5MB in bytes
                flash("File size must not exceed 5MB", "danger")
                return redirect(url_for("manage_pets"))
            
            # Make filename safe and unique
            filename = secure_filename(file.filename)
            
            # Add timestamp to avoid filename conflicts
            import time
            filename = f"{int(time.time())}_{filename}"
            
            # Create pets folder if it doesn't exist
            pets_folder = os.path.join(UPLOAD_FOLDER, 'pets')
            os.makedirs(pets_folder, exist_ok=True)
            
            # Save the new file
            file.save(os.path.join(pets_folder, filename))
            image_path = f"uploads/pets/{filename}"

        # Build update query for pet information
        query = """
            UPDATE pets
            SET owner_id = %s, name = %s, breed = %s, age = %s, gender = %s,
                medical_history = %s
        """
        values = [owner_id, name, breed, age, gender, medical_history]

        # If new image was uploaded, include it in update
        if image_path:
            query += ", image = %s"
            values.append(image_path)

        # Complete the query with WHERE clause
        query += " WHERE pet_id = %s"
        values.append(pet_id)

        # Execute the update
        cursor.execute(query, tuple(values))
        conn.commit()  # Save changes
        flash("Pet updated successfully", "success")
        
    except mysql.connector.Error as e:
        # If database error, undo changes
        conn.rollback()
        print("MySQL Error:", e)  # Print for debugging
        flash("Something went wrong while updating pet", "danger")
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()

    # Go back to pet management page
    return redirect(url_for("manage_pets"))


# DELETE PET (ADMIN ONLY) - Permanently remove pet record from system
@app.route("/manage_delete_pet", methods=["DELETE"])
@role_required("Admin")  # Only admins can delete pets
def manage_delete_pet():
    """Admin function to permanently delete a pet record from the system"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get pet ID from JSON request (sent by JavaScript)
        data = request.get_json()
        pet_id = data.get("pet_id")
        
        # Permanently delete the pet record from database
        # Note: This is a hard delete, unlike users which are soft-deleted
        cursor.execute(
            "DELETE FROM pets WHERE pet_id = %s", (pet_id,)
        )
        
        conn.commit()  # Save the deletion
        
        # Send success response back to JavaScript
        return jsonify({"success": True, "message": "Pet deleted successfully"})
        
    except mysql.connector.Error as e:
        # If something goes wrong, undo changes
        conn.rollback()
        # Send error response back to JavaScript
        return jsonify({"success": False, "message": "Something went wrong"}), 500
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()


# USER PROFILE - Show user's profile information
@app.route("/profile", methods=["GET"])
@role_required("Admin", "Pet Owner", "Veterinarian")  # All logged-in users can view their profile
def profile():
    """Show user's profile page with their personal information"""
    
    # Double-check user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        user_id = session["user_id"]  # Get current user's ID
        role = session["role"]        # Get current user's role
        
        # Get basic user information from users table
        cursor.execute("SELECT user_id AS user_id, full_name AS full_name, email AS email, role AS role, status AS status, DATE_FORMAT(created_at, '%d %M %Y') AS created_at FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        # Get role-specific additional information
        if role == "Pet Owner":
            # Get pet owner's phone and address
            cursor.execute("SELECT phone, address FROM owners WHERE user_id = %s", (user_id,))
            role_data = cursor.fetchone()
        elif role == "Veterinarian":
            # Get vet's phone, clinic address, and specialization
            cursor.execute("SELECT phone, clinic_address as address, specialization FROM veterinarians WHERE user_id = %s", (user_id,))
            role_data = cursor.fetchone()
        else:
            # Admin users don't have additional role-specific data
            role_data = {}
        
        # Combine basic user info with role-specific info
        profile = {**user, **(role_data or {})}
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()
    
    # Show profile page with user's information
    return render_template("dashboard/profile.html", objProfile=profile)

# UPDATE PROFILE - Allow users to update their profile information
@app.route("/update_profile", methods=["POST"])
@role_required("Admin", "Pet Owner", "Veterinarian")  # All logged-in users can update their profile
def update_profile():
    """Process profile update form - update user's personal information"""
    
    # Double-check user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        user_id = session["user_id"]  # Get current user's ID
        role = session["role"]        # Get current user's role
        
        # Get updated information from form
        full_name = request.form["full_name"]           # Updated name
        phone = request.form.get("phone")               # Updated phone (optional)
        address = request.form.get("address")           # Updated address (optional)
        specialization = request.form.get("specialization")  # For vets only (optional)
        password = request.form.get("password")         # New password (optional)
        
        # Update basic user information in users table
        query = "UPDATE users SET full_name = %s"
        values = [full_name]
        
        # If user provided a new password, include it in update
        if password:
            query += ", password = %s"
            values.append(generate_password_hash(password))  # Hash the new password
        
        # Complete the query and execute
        query += " WHERE user_id = %s"
        values.append(user_id)
        cursor.execute(query, values)
        
        # Update role-specific information
        if role == "Pet Owner":
            # Check if owner record exists
            cursor.execute("SELECT * FROM owners WHERE user_id = %s", (user_id,))
            if cursor.fetchone():
                # Update existing owner record
                cursor.execute("UPDATE owners SET phone = %s, address = %s WHERE user_id = %s", (phone, address, user_id))
            else:
                # Create new owner record if it doesn't exist
                cursor.execute("INSERT INTO owners (user_id, phone, address) VALUES (%s, %s, %s)", (user_id, phone, address))
                
        elif role == "Veterinarian":
            # Check if veterinarian record exists
            cursor.execute("SELECT * FROM veterinarians WHERE user_id = %s", (user_id,))
            if cursor.fetchone():
                # Update existing vet record
                cursor.execute("UPDATE veterinarians SET phone = %s, clinic_address = %s, specialization = %s WHERE user_id = %s", (phone, address, specialization, user_id))
            else:
                # Create new vet record if it doesn't exist
                cursor.execute("INSERT INTO veterinarians (user_id, phone, clinic_address, specialization) VALUES (%s, %s, %s, %s)", (user_id, phone, address, specialization))
        
        # Save all changes to database
        conn.commit()
        flash("Profile updated successfully", "success")
        
    except mysql.connector.Error as e:
        # If something goes wrong, undo changes
        conn.rollback()
        flash("Something went wrong while updating profile", "danger")
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()
    
    # Go back to profile page
    return redirect(url_for("profile"))

# DELETE ACCOUNT - Allow users to delete their own account
@app.route("/delete_account", methods=["DELETE"])
@role_required("Admin", "Pet Owner", "Veterinarian")  # All logged-in users can delete their account
def delete_account():
    """Allow users to soft-delete their own account (mark as deleted, don't remove from database)"""
    
    # Check if user is logged in
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        user_id = session["user_id"]  # Get current user's ID
        
        # Soft delete: mark user as deleted instead of removing from database
        # This preserves data integrity (appointments, medical records, etc.)
        cursor.execute("UPDATE users SET vchr_status = 'D' WHERE user_id = %s", (user_id,))
        
        conn.commit()  # Save the change
        session.clear()  # Log user out immediately
        
        # Send success response back to JavaScript
        return jsonify({"success": True, "message": "Account deleted successfully"})
        
    except mysql.connector.Error as e:
        # If something goes wrong, undo changes
        conn.rollback()
        # Send error response back to JavaScript
        return jsonify({"success": False, "message": "Something went wrong"}), 500
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()

# BOOK APPOINTMENT - Pet owners can schedule appointments with veterinarians
@app.route("/book_appointment", methods=["GET", "POST"])
@role_required("Pet Owner")  # Only pet owners can book appointments
def book_appointment():
    """Handle appointment booking - show form and process booking requests"""
    
    # First, get the owner's pets for the booking form
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    pets = []  # Start with empty list
    
    try:
        # Get owner's ID from owners table
        cursor.execute("SELECT owner_id FROM owners WHERE user_id = %s", (session["user_id"],))
        owner_data = cursor.fetchone()
        
        if owner_data:
            # Get all pets owned by this user
            cursor.execute("SELECT * FROM pets WHERE owner_id = %s", (owner_data["owner_id"],))
            pets = cursor.fetchall()
            
    finally:
        cursor.close()
        conn.close()
    
    # If user just wants to see the booking form
    if request.method == "GET":
        return render_template("appointments/book.html", pets=pets)
    
    # If user submitted the booking form, process the appointment
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get appointment details from form
        pet_id = request.form["pet_id"]              # Which pet
        vet_id = request.form["vet_id"]              # Which veterinarian
        appointment_date = request.form["appointment_date"]  # Date
        appointment_time = request.form["appointment_time"]  # Time
        
        # Get owner_id again for database insert
        cursor.execute("SELECT owner_id FROM owners WHERE user_id = %s", (session["user_id"],))
        owner_data = cursor.fetchone()
        
        # Combine date and time into single datetime
        appointment_datetime = f"{appointment_date} {appointment_time}"
        
        # Check for scheduling conflicts (appointments are 30-minute slots)
        cursor.execute("""
            SELECT * FROM appointments 
            WHERE vet_id = %s AND appointment_date BETWEEN 
            DATE_SUB(%s, INTERVAL 30 MINUTE) AND DATE_ADD(%s, INTERVAL 30 MINUTE)
            AND status != 'Cancelled'
        """, (vet_id, appointment_datetime, appointment_datetime))
        
        # If there's a conflict, show error and return to form
        if cursor.fetchone():
            flash("Time slot not available. Please choose another time.", "danger")
            
            # Get vet name to show in error message
            cursor.execute("SELECT u.full_name FROM users u JOIN veterinarians v ON u.user_id = v.user_id WHERE v.vet_id = %s", (vet_id,))
            vet_data = cursor.fetchone()
            vet_name = vet_data["full_name"] if vet_data else ""
            
            # Return to form with previous values filled in
            return render_template("appointments/book.html", 
                                 pets=pets, 
                                 pet_id=pet_id, 
                                 vet_id=vet_id, 
                                 vet_name=vet_name, 
                                 appointment_date=appointment_date, 
                                 appointment_time=appointment_time)
        
        # No conflict, so book the appointment
        cursor.execute("""
            INSERT INTO appointments (pet_id, owner_id, vet_id, appointment_date)
            VALUES (%s, %s, %s, %s)
        """, (pet_id, owner_data["owner_id"], vet_id, appointment_datetime))
        
        conn.commit()  # Save the appointment
        flash("Appointment booked successfully!", "success")
        
    except mysql.connector.Error as e:
        print(e)  # Print error for debugging
        conn.rollback()  # Undo changes
        flash("Something went wrong while booking appointment", "danger")
        
    finally:
        cursor.close()
        conn.close()
    
    # After successful booking, go to appointments list
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

# ADD VACCINATION RECORD - Veterinarians can record vaccinations given to pets
@app.route("/add_vaccination", methods=["POST"])
@role_required("Veterinarian")  # Only vets can add vaccination records
def add_vaccination():
    """Veterinarian function to record a vaccination given to a pet"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get this vet's ID from veterinarians table
        cursor.execute("SELECT vet_id FROM veterinarians WHERE user_id = %s", (session["user_id"],))
        vet_data = cursor.fetchone()
        
        # Get vaccination details from form
        pet_id = request.form["pet_id"]              # Which pet was vaccinated
        vaccine_name = request.form["vaccine_name"]  # Name of vaccine (e.g., "Rabies")
        date_given = request.form["date_given"]      # When vaccine was given
        next_due_date = request.form.get("next_due_date") or None  # When next dose is due (optional)
        notes = request.form.get("notes")            # Any additional notes (optional)
        
        # Insert vaccination record into database
        cursor.execute("""
            INSERT INTO vaccinations (pet_id, vet_id, vaccine_name, date_given, next_due_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (pet_id, vet_data["vet_id"], vaccine_name, date_given, next_due_date, notes))
        
        # Automatically mark today's appointments as completed
        # (If vet is adding medical records, the appointment is probably done)
        cursor.execute("""
            UPDATE appointments SET status = 'Completed' 
            WHERE pet_id = %s AND vet_id = %s AND DATE(appointment_date) = CURDATE() 
            AND status != 'Cancelled'
        """, (pet_id, vet_data["vet_id"]))
        
        conn.commit()  # Save all changes
        flash("Vaccination record added successfully!", "success")
        
    except mysql.connector.Error as e:
        # If something goes wrong, undo changes
        conn.rollback()
        flash("Something went wrong while adding vaccination record", "danger")
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()
    
    # Go back to pet's medical records page
    return redirect(url_for("pet_medical", pet_id=pet_id))

# ADD MEDICATION RECORD - Veterinarians can prescribe medications for pets
@app.route("/add_medication", methods=["POST"])
@role_required("Veterinarian")  # Only vets can add medication records
def add_medication():
    """Veterinarian function to record a medication prescribed to a pet"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get this vet's ID from veterinarians table
        cursor.execute("SELECT vet_id FROM veterinarians WHERE user_id = %s", (session["user_id"],))
        vet_data = cursor.fetchone()
        
        # Get medication details from form
        pet_id = request.form["pet_id"]              # Which pet gets the medication
        medicine_name = request.form["medicine_name"]  # Name of medicine
        dosage = request.form["dosage"]              # How much to give (e.g., "2 tablets daily")
        start_date = request.form["start_date"]      # When to start medication
        end_date = request.form.get("end_date") or None  # When to stop (optional)
        notes = request.form.get("notes")            # Additional instructions (optional)
        
        # Insert medication record into database
        cursor.execute("""
            INSERT INTO medications (pet_id, vet_id, medicine_name, dosage, start_date, end_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (pet_id, vet_data["vet_id"], medicine_name, dosage, start_date, end_date, notes))
        
        # Automatically mark today's appointments as completed
        # (If vet is prescribing medication, the appointment is probably done)
        cursor.execute("""
            UPDATE appointments SET status = 'Completed' 
            WHERE pet_id = %s AND vet_id = %s AND DATE(appointment_date) = CURDATE() 
            AND status != 'Cancelled'
        """, (pet_id, vet_data["vet_id"]))
        
        conn.commit()  # Save all changes
        flash("Medication record added successfully!", "success")
        
    except mysql.connector.Error as e:
        # If something goes wrong, undo changes
        conn.rollback()
        flash("Something went wrong while adding medication record", "danger")
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()
    
    # Go back to pet's medical records page
    return redirect(url_for("pet_medical", pet_id=pet_id))

# ADMIN MEDICAL OVERVIEW - Admin can see all medical records in the system
@app.route("/admin_medical")
@role_required("Admin")  # Only admins can see all medical records
def admin_medical():
    """Admin function to view all vaccination and medication records system-wide"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all vaccinations with pet, vet, and owner information
        # This complex query joins multiple tables to show complete information
        cursor.execute("""
            SELECT v.*, p.name as pet_name, u.full_name as vet_name, o.full_name as owner_name
            FROM vaccinations v
            JOIN pets p ON v.pet_id = p.pet_id                    -- Get pet info
            JOIN veterinarians vet ON v.vet_id = vet.vet_id       -- Get vet info
            JOIN users u ON vet.user_id = u.user_id               -- Get vet's name
            JOIN owners o_tbl ON p.owner_id = o_tbl.owner_id      -- Get owner info
            JOIN users o ON o_tbl.user_id = o.user_id             -- Get owner's name
            ORDER BY v.date_given DESC                            -- Show newest first
        """)
        vaccinations = cursor.fetchall()
        
        # Get all medications with pet, vet, and owner information
        # Similar complex query for medications
        cursor.execute("""
            SELECT m.*, p.name as pet_name, u.full_name as vet_name, o.full_name as owner_name
            FROM medications m
            JOIN pets p ON m.pet_id = p.pet_id                    -- Get pet info
            JOIN veterinarians vet ON m.vet_id = vet.vet_id       -- Get vet info
            JOIN users u ON vet.user_id = u.user_id               -- Get vet's name
            JOIN owners o_tbl ON p.owner_id = o_tbl.owner_id      -- Get owner info
            JOIN users o ON o_tbl.user_id = o.user_id             -- Get owner's name
            ORDER BY m.start_date DESC                            -- Show newest first
        """)
        medications = cursor.fetchall()
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()
    
    # Show admin medical overview page with all records
    return render_template("medical/admin_medical.html", 
                         vaccinations=vaccinations, 
                         medications=medications)

# VIEW VACCINATIONS - Show vaccination records (role-based filtering)
@app.route("/vaccinations")
@role_required("Admin", "Veterinarian")  # Only admins and vets can view vaccination records
def view_vaccinations():
    """Show vaccination records - Admins see all, Vets see only their own records"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if session["role"] == "Admin":
            # Admin sees all vaccinations in the system
            cursor.execute("""
                SELECT v.*, p.name as pet_name, u.full_name as vet_name, o.full_name as owner_name
                FROM vaccinations v
                JOIN pets p ON v.pet_id = p.pet_id                    -- Get pet info
                JOIN veterinarians vet ON v.vet_id = vet.vet_id       -- Get vet info
                JOIN users u ON vet.user_id = u.user_id               -- Get vet's name
                JOIN owners o_tbl ON p.owner_id = o_tbl.owner_id      -- Get owner info
                JOIN users o ON o_tbl.user_id = o.user_id             -- Get owner's name
                ORDER BY v.date_given DESC                            -- Show newest first
            """)
            
        else:  # Veterinarian role
            # Vet sees only vaccinations they administered
            cursor.execute("SELECT vet_id FROM veterinarians WHERE user_id = %s", (session["user_id"],))
            vet_data = cursor.fetchone()
            
            if vet_data:
                # Get only this vet's vaccination records
                cursor.execute("""
                    SELECT v.*, p.name as pet_name, o.full_name as owner_name
                    FROM vaccinations v
                    JOIN pets p ON v.pet_id = p.pet_id                -- Get pet info
                    JOIN owners o_tbl ON p.owner_id = o_tbl.owner_id  -- Get owner info
                    JOIN users o ON o_tbl.user_id = o.user_id         -- Get owner's name
                    WHERE v.vet_id = %s                               -- Filter by this vet
                    ORDER BY v.date_given DESC                        -- Show newest first
                """, (vet_data["vet_id"],))
            else:
                # If vet data not found, return empty result
                cursor.execute("SELECT * FROM vaccinations WHERE 1=0")  # Query that returns no rows
        
        vaccinations = cursor.fetchall()  # Get all matching vaccination records
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()
    
    # Show vaccinations page with filtered results
    return render_template("medical/vaccinations.html", vaccinations=vaccinations)

# VIEW MEDICATIONS - Show medication records (role-based filtering)
@app.route("/medications")
@role_required("Admin", "Veterinarian")  # Only admins and vets can view medication records
def view_medications():
    """Show medication records - Admins see all, Vets see only their own prescriptions"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if session["role"] == "Admin":
            # Admin sees all medications in the system
            cursor.execute("""
                SELECT m.*, p.name as pet_name, u.full_name as vet_name, o.full_name as owner_name
                FROM medications m
                JOIN pets p ON m.pet_id = p.pet_id                    -- Get pet info
                JOIN veterinarians vet ON m.vet_id = vet.vet_id       -- Get vet info
                JOIN users u ON vet.user_id = u.user_id               -- Get vet's name
                JOIN owners o_tbl ON p.owner_id = o_tbl.owner_id      -- Get owner info
                JOIN users o ON o_tbl.user_id = o.user_id             -- Get owner's name
                ORDER BY m.start_date DESC                            -- Show newest first
            """)
            
        else:  # Veterinarian role
            # Vet sees only medications they prescribed
            cursor.execute("SELECT vet_id FROM veterinarians WHERE user_id = %s", (session["user_id"],))
            vet_data = cursor.fetchone()
            
            if vet_data:
                # Get only this vet's medication records
                cursor.execute("""
                    SELECT m.*, p.name as pet_name, o.full_name as owner_name
                    FROM medications m
                    JOIN pets p ON m.pet_id = p.pet_id                -- Get pet info
                    JOIN owners o_tbl ON p.owner_id = o_tbl.owner_id  -- Get owner info
                    JOIN users o ON o_tbl.user_id = o.user_id         -- Get owner's name
                    WHERE m.vet_id = %s                               -- Filter by this vet
                    ORDER BY m.start_date DESC                        -- Show newest first
                """, (vet_data["vet_id"],))
            else:
                # If vet data not found, return empty result
                cursor.execute("SELECT * FROM medications WHERE 1=0")  # Query that returns no rows
        
        medications = cursor.fetchall()  # Get all matching medication records
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()
    
    # Show medications page with filtered results
    return render_template("medical/medications.html", medications=medications)

# UPDATE APPOINTMENT STATUS - Veterinarians can change appointment status
@app.route("/update_appointment_status", methods=["POST"])
@role_required("Veterinarian")  # Only vets can update appointment status
def update_appointment_status():
    """Veterinarian function to update appointment status (Pending -> Confirmed -> Completed)"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get data sent from JavaScript (AJAX request)
        data = request.get_json()
        appointment_id = data.get("appointment_id")  # Which appointment to update
        status = data.get("status")                  # New status (Confirmed, Completed, etc.)
        
        # Security check: Make sure this appointment belongs to the current vet
        cursor.execute("SELECT vet_id FROM veterinarians WHERE user_id = %s", (session["user_id"],))
        vet_data = cursor.fetchone()
        
        # Check if appointment exists and belongs to this vet
        cursor.execute("SELECT * FROM appointments WHERE appointment_id = %s AND vet_id = %s", 
                      (appointment_id, vet_data["vet_id"]))
        appointment = cursor.fetchone()
        
        # If appointment not found or doesn't belong to this vet
        if not appointment:
            return jsonify({"success": False, "message": "Appointment not found"}), 404
        
        # Update the appointment status
        cursor.execute("UPDATE appointments SET status = %s WHERE appointment_id = %s", 
                      (status, appointment_id))
        conn.commit()  # Save the change
        
        # Send success response back to JavaScript
        return jsonify({"success": True, "message": f"Appointment marked as {status}"})
        
    except mysql.connector.Error as e:
        # If database error, undo changes
        conn.rollback()
        # Send error response back to JavaScript
        return jsonify({"success": False, "message": "Something went wrong"}), 500
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()

# CANCEL APPOINTMENT - Pet owners can cancel their pending appointments
@app.route("/cancel_appointment", methods=["POST"])
@role_required("Pet Owner")  # Only pet owners can cancel appointments
def cancel_appointment():
    """Pet owner function to cancel their own pending appointments"""
    
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get data sent from JavaScript (AJAX request)
        data = request.get_json()
        appointment_id = data.get("appointment_id")  # Which appointment to cancel
        
        # Security check: Make sure this appointment belongs to the current pet owner
        cursor.execute("SELECT owner_id FROM owners WHERE user_id = %s", (session["user_id"],))
        owner_data = cursor.fetchone()
        
        # Check if appointment exists and belongs to this owner
        cursor.execute("SELECT * FROM appointments WHERE appointment_id = %s AND owner_id = %s", 
                      (appointment_id, owner_data["owner_id"]))
        appointment = cursor.fetchone()
        
        # If appointment not found or doesn't belong to this owner
        if not appointment:
            return jsonify({"success": False, "message": "Appointment not found"}), 404
        
        # Can only cancel appointments that are still pending
        if appointment["status"] != "Pending":
            return jsonify({"success": False, "message": "Can only cancel pending appointments"}), 400
        
        # Update appointment status to cancelled
        cursor.execute("UPDATE appointments SET status = 'Cancelled' WHERE appointment_id = %s", 
                      (appointment_id,))
        conn.commit()  # Save the change
        
        # Send success response back to JavaScript
        return jsonify({"success": True, "message": "Appointment cancelled successfully"})
        
    except mysql.connector.Error as e:
        # If database error, undo changes
        conn.rollback()
        # Send error response back to JavaScript
        return jsonify({"success": False, "message": "Something went wrong"}), 500
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()

# AUTOCOMPLETE USERS - Help forms find users as you type (for dropdowns and search)
@app.route("/autocomplete_users", methods=["GET"])
def autocomplete_users():
    """Provide user suggestions for forms - searches users as you type"""
    
    # Get search parameters from URL
    role = request.args.get("role", "")    # What type of user to search for
    query = request.args.get("q", "")      # What the user typed

    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Different queries based on what type of user we're searching for
        
        if role == "Pet Owner":
            # For pet owners, we need owner_id (not user_id) for pet relationships
            sql = """
                SELECT u.user_id, u.full_name, u.email, o.owner_id
                FROM users u
                JOIN owners o ON u.user_id = o.user_id
                WHERE u.role = "Pet Owner" AND u.full_name LIKE %s AND u.vchr_status = 'A'
                LIMIT 10
            """
            cursor.execute(sql, (f"%{query}%",))  # Search for names containing the query
            results = cursor.fetchall()
            
            # Replace user_id with owner_id for pet ownership relationships
            for result in results:
                result['user_id'] = result['owner_id']
                
        elif role == "Veterinarian":
            # For veterinarians, include their specialization in results
            sql = """
                SELECT u.user_id, u.full_name, u.email, v.specialization, v.vet_id
                FROM users u
                JOIN veterinarians v ON u.user_id = v.user_id
                WHERE u.role = "Veterinarian" AND u.full_name LIKE %s AND u.vchr_status = 'A'
                LIMIT 10
            """
            cursor.execute(sql, (f"%{query}%",))
            results = cursor.fetchall()
            
        else:
            # For other roles or general search
            sql = """
                SELECT user_id, full_name, email 
                FROM users 
                WHERE role = %s AND full_name LIKE %s AND vchr_status = 'A'
                LIMIT 10
            """
            cursor.execute(sql, (role, f"%{query}%"))
            results = cursor.fetchall()
            
        # Return results as JSON for JavaScript to use
        return jsonify(results)
        
    except Exception as e:
        # If something goes wrong, return empty list
        return jsonify([])
        
    finally:
        # Always close database connections
        cursor.close()
        conn.close()

# ---------- MAIN PROGRAM START ----------
if __name__ == "__main__":
    """This code runs when the program starts"""
    
    # Create default admin user if it doesn't exist
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    
    # Default admin account details
    objAdmin = {
        "full_name": "admin",
        "password": "test123",           # Default password (should be changed!)
        "email": "admin@petcare.in",
        "role": "Admin",
        "status": "Active",
    }
    
    # Check if admin user already exists
    cur.execute("SELECT * FROM users WHERE full_name = %s", (objAdmin["full_name"],))
    user = cur.fetchone()
    
    if not user:  # If no admin user exists, create one
        try:
            print("Creating default admin user...")
            # Hash the password for security
            hashedPassword = generate_password_hash(objAdmin["password"])
            
            # Insert admin user into database
            cur.execute(
                "INSERT INTO users (full_name, password, email, role) VALUES (%s, %s, %s, %s)",
                (
                    objAdmin["full_name"],
                    hashedPassword,      # Use hashed password, not plain text
                    objAdmin["email"],
                    objAdmin["role"],
                ),
            )
            conn.commit()  # Save changes to database
            print("Default admin user created successfully!")
            
        except mysql.connector.Error as e:
            # If something goes wrong, undo changes
            conn.rollback()
            print(f"Error creating admin user: {e}")
            
    else:
        print("Default admin user already exists")
    
    # Close database connections
    cur.close()
    conn.close()
    
    # Start the Flask web server
    print("Starting Pet Care Management System...")
    print("Access the application at: http://localhost:5000")
    print("Default admin login: admin@petcare.in / test123")
    app.run(debug=True)  # debug=True shows detailed error messages
