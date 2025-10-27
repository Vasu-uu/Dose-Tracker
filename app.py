from flask import Flask, request, jsonify, send_from_directory # <-- send_from_directory ADDED
from flask_cors import CORS
from flask_mail import Mail, Message
import mysql.connector
import schedule
import time
import threading
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os # <-- os ADDED

# --- App Initialization ---
app = Flask(__name__)
# Enable CORS for frontend access
CORS(app)

# --- Database Configuration ---
# NOTE: Replace these with your actual database credentials
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "medicine_reminder"
}

def get_db_connection():
    """Establishes a new database connection."""
    return mysql.connector.connect(**db_config)

# --- Mail Configuration (Essential for Reminders) ---
# NOTE: If using Gmail, you must generate an App Password for security.
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'dosetracker0@gmail.com'
app.config['MAIL_PASSWORD'] = 'dosetracker2025' 
mail = Mail(app)


# ---------------------------------------------------------------------
# --- NEW SECTION: Serve Frontend Website Files ---
# ---------------------------------------------------------------------

# This tells Flask where your HTML, CSS, JS, and image files are.
# We use os.path.dirname to get the directory where app.py is.
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def get_index():
    """Serves the main index.html file."""
    # 'filename' is relative to the APP_ROOT
    return send_from_directory(APP_ROOT, 'index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    """Serves all other files (login.html, style.css, images, etc.)."""
    return send_from_directory(APP_ROOT, filename)

# ---------------------------------------------------------------------
# --- Your API Code (All Fixes Included) ---
# ---------------------------------------------------------------------


# ------------------- 1. User Registration (Supports 'Sign In' Page) -------------------
@app.route('/register', methods=['POST'])
def register():
    """Handles new user sign-ups (Full Name, Email, Password, Username, Age)."""
    try:
        data = request.get_json()
        name = data.get('full_name') 
        email = data.get('email')
        password = data.get('password')
        username = data.get('username') # New field
        age = data.get('age')           # New field

        if not all([name, email, password, username, age]):
            return jsonify({'message': 'Missing required registration fields.'}), 400

        password_hash = generate_password_hash(password)

        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute(
            'INSERT INTO users (name, email, password_hash, username, age) VALUES (%s, %s, %s, %s, %s)',
            (name, email, password_hash, username, age)
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'User registered successfully!'}), 201
    except mysql.connector.Error as err:
        print(f"Database error on registration: {err}")
        # Check for duplicate email/username if you add UNIQUE constraints
        if err.errno == 1062:
             return jsonify({'message': 'Email or Username already exists.'}), 409
        return jsonify({'message': f'Database error: {err.msg}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {e}'}), 500

# ------------------- 2. User Login (Supports 'Log In' Page) -------------------
@app.route('/login', methods=['POST'])
def login():
    """Authenticates user based on Email (Username) and Password."""
    try:
        data = request.get_json()
        # Assuming 'Enter Username' field maps to 'email'
        email = data.get('email')
        password = data.get('password')

        if not all([email, password]):
            return jsonify({'message': 'Missing login credentials'}), 400

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        # Login remains based on email
        cursor.execute('SELECT user_id, name, password_hash FROM users WHERE email=%s', (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user['password_hash'], password):
            # Return user_id to the frontend so it can fetch the user's medicines
            return jsonify({'message': 'Login successful!', 'user_id': user['user_id'], 'name': user['name']})
        else:
            return jsonify({'message': 'Invalid email or password'}), 401
    except Exception as e:
        print(f"Error during login: {e}")
        return jsonify({'message': f'An error occurred: {e}'}), 500

# ------------------- 3. Add Medicine (Supports 'New Medicine' Page) -------------------
@app.route('/add_medicine', methods=['POST'])
def add_medicine():
    """Adds a new medicine AND generates all associated reminders."""
    db = None
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        medicine_name = data.get('medicine_name')
        dosage = data.get('dose')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        times_per_day = data.get('times_per_day')
        morning = data.get('morning', False)
        noon = data.get('noon', False)
        night = data.get('night', False)

        if not all([user_id, medicine_name, dosage, start_date_str, end_date_str, times_per_day]):
            return jsonify({'message': 'Missing essential medicine details.'}), 400

        db = get_db_connection()
        cursor = db.cursor()
        
        # Insert into medicines table
        cursor.execute(
            'INSERT INTO medicines (user_id, medicine_name, dosage, start_date, end_date, times_per_day, schedule_morning, schedule_noon, schedule_night) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (user_id, medicine_name, dosage, start_date_str, end_date_str, times_per_day, morning, noon, night)
        )
        
        # Get the ID of the medicine we just inserted
        medicine_id = cursor.lastrowid

        # --- NEW: Reminder Generation Logic ---
        REMINDER_TIMES = {
            "morning": "08:00:00", # 8:00 AM
            "noon": "13:00:00",    # 1:00 PM
            "night": "20:00:00"    # 8:00 PM
        }
        
        start_dt = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        current_date = start_dt
        reminders_to_insert = []
        
        # Loop from start date to end date
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            
            if morning:
                reminders_to_insert.append((medicine_id, f"{date_str} {REMINDER_TIMES['morning']}"))
            if noon:
                reminders_to_insert.append((medicine_id, f"{date_str} {REMINDER_TIMES['noon']}"))
            if night:
                reminders_to_insert.append((medicine_id, f"{date_str} {REMINDER_TIMES['night']}"))
            
            current_date += timedelta(days=1)

        # Insert all reminders into the reminders table
        if reminders_to_insert:
            # Note the table name is "reminders"
            reminder_query = "INSERT INTO reminders (medicine_id, reminder_datetime) VALUES (%s, %s)"
            cursor.executemany(reminder_query, reminders_to_insert)
        # --- End of New Logic ---

        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Medicine added successfully!'}), 201

    except mysql.connector.Error as err:
        print(f"Database error on add_medicine: {err}")
        if db: db.rollback()
        return jsonify({'message': f'Database error: {err.msg}'}), 500
    except Exception as e:
        print(f"Error adding medicine: {e}")
        if db: db.rollback()
        return jsonify({'message': f'An unexpected error occurred: {e}'}), 500
    finally:
        if db and db.is_connected():
            cursor.close()
            db.close()

# ------------------- 4. Get User's Medicines (Supports Dashboard Table) -------------------
# --- THIS FUNCTION IS UPDATED (DATE FIX) ---
@app.route('/my_medicines/<int:user_id>', methods=['GET'])
def get_user_medicines(user_id):
    """Fetches all medicines for the Dashboard table view."""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Use DATE_FORMAT to force MySQL to return the date as a 'YYYY-MM-DD' string
        cursor.execute(
            'SELECT '
            'medicine_id, medicine_name, dosage, '
            'DATE_FORMAT(start_date, "%Y-%m-%d") as start_date, '    # <-- THIS IS FIXED
            'DATE_FORMAT(end_date, "%Y-%m-%d") as end_date, '      # <-- THIS IS FIXED
            'times_per_day, schedule_morning, schedule_noon, schedule_night '
            'FROM medicines WHERE user_id = %s',
            (user_id,)
        )
        medicines = cursor.fetchall()
        cursor.close()
        db.close()
        
        return jsonify(medicines)
        
    except mysql.connector.Error as err:
        print(f"Database error on get_user_medicines: {err}")
        return jsonify({'message': f'Database error: {err.msg}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {e}'}), 500

# ------------------- Email Reminder & Scheduler Logic (Core Function) -------------------

def send_email_reminder(to_email, subject, message):
    """Utility function to send an email using Flask-Mail."""
    with app.app_context():
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[to_email])
        msg.body = message
        try:
            mail.send(msg)
            print(f"Reminder sent successfully to {to_email}")
        except Exception as e:
            print(f"ERROR sending email to {to_email}: {e}")

# --- THIS FUNCTION IS UPDATED (REMINDER LOGIC FIX) ---
def check_reminders():
    """Background task to query the database and send pending reminders."""
    db = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # New, more robust query:
        # Get all reminders that are 'Pending' AND scheduled for any time in the past
        # Note the table name is "reminders"
        query = (
            "SELECT r.reminder_id, r.reminder_datetime, u.email, m.medicine_name, m.dosage "
            "FROM reminders r "
            "JOIN medicines m ON r.medicine_id=m.medicine_id "
            "JOIN users u ON m.user_id=u.user_id "
            "WHERE r.status='Pending' AND r.reminder_datetime <= %s"
        )
        
        cursor.execute(query, (datetime.now(),))
        reminders = cursor.fetchall()
        
        if not reminders:
            # print("No pending reminders.") # Uncomment for debugging
            cursor.close()
            return

        print(f"Found {len(reminders)} pending reminders to send...")

        for r in reminders:
            try:
                subject = f"Time for your medicine: {r['medicine_name']}"
                message = f"This is a reminder to please take your medicine: \n\n" \
                          f"Medicine: {r['medicine_name']}\n" \
                          f"Dose: {r['dosage']}\n" \
                          f"Scheduled for: {r['reminder_datetime'].strftime('%Y-%m-%d %I:%M %p')}\n\n" \
                          f"From your Dose Tracker app."
                
                send_email_reminder(r['email'], subject, message)
                
                # Update status to 'Sent'
                # Note the table name is "reminders"
                cursor.execute("UPDATE reminders SET status='Sent' WHERE reminder_id=%s", (r['reminder_id'],))
                db.commit()
                
            except Exception as e:
                print(f"Failed to send or update reminder {r['reminder_id']}: {e}")
                db.rollback() # Rollback this one transaction
                
        cursor.close()
        
    except Exception as e:
        print(f"ERROR in check_reminders background task: {e}")
    finally:
        if db and db.is_connected():
            db.close()

def run_scheduler():
    """Runs the schedule loop in a background thread."""
    schedule.every(1).minutes.do(check_reminders)
    while True:
        schedule.run_pending()
        time.sleep(1) 

# Start the reminder checking thread when the server starts
threading.Thread(target=run_scheduler, daemon=True).start()

# ------------------- Run App -------------------
if __name__ == '__main__':
    # Use host='0.0.0.0' for external network access (e.g., frontend running on a different port)
    # The default port is 5000
    app.run(debug=True, host='0.0.0.0')