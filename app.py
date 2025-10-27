from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail, Message
import mysql.connector
import schedule
import time
import threading
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

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

# ------------------- 1. User Registration (Supports 'Sign In' Page) -------------------
@app.route('/register', methods=['POST'])
def register():
    """Handles new user sign-ups (Full Name, Email, Password)."""
    try:
        data = request.get_json()
        # Assuming the 'Username' field in the UI maps to 'email' for login verification.
        name = data.get('full_name') 
        email = data.get('email')
        password = data.get('password')
        # Age and Username fields from the UI are ignored here for simplicity 
        # but could be added to the users table.

        if not all([name, email, password]):
            return jsonify({'message': 'Missing required registration fields.'}), 400

        password_hash = generate_password_hash(password)

        db = get_db_connection()
        cursor = db.cursor()
        # NOTE: Using 'email' as the username/identifier as it's unique
        cursor.execute(
            'INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)',
            (name, email, password_hash)
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'User registered successfully!'}), 201
    except mysql.connector.Error as err:
        print(f"Database error on registration: {err}")
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
    """Adds a new medicine with specific scheduling details from the UI."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        medicine_name = data.get('medicine_name')
        dosage = data.get('dose')
        
        # Specific fields from the 'New Medicine' UI
        food_time = data.get('food_time') # 'Before' or 'After'
        morning = data.get('morning', False)
        noon = data.get('noon', False)
        night = data.get('night', False)

        if not all([user_id, medicine_name, dosage, food_time]):
            return jsonify({'message': 'Missing essential medicine details.'}), 400

        db = get_db_connection()
        cursor = db.cursor()
        
        # Insert into medicines table. Assumes the table has columns for all fields below.
        cursor.execute(
            'INSERT INTO medicines (user_id, medicine_name, dosage, food_time, schedule_morning, schedule_noon, schedule_night) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (user_id, medicine_name, dosage, food_time, morning, noon, night)
        )
        db.commit()
        
        # In a complete app, you would now generate entries in the `reminders` table 
        # based on the (morning, noon, night) flags, but that complex logic is omitted here 
        # to focus on the core endpoints.

        cursor.close()
        db.close()
        return jsonify({'message': 'Medicine added successfully!'}), 201
    except mysql.connector.Error as err:
        print(f"Database error on add_medicine: {err}")
        return jsonify({'message': f'Database error: {err.msg}'}), 500
    except Exception as e:
        print(f"Error adding medicine: {e}")
        return jsonify({'message': f'An unexpected error occurred: {e}'}), 500

# ------------------- 4. Get User's Medicines (Supports Dashboard Table) -------------------
@app.route('/my_medicines/<int:user_id>', methods=['GET'])
def get_user_medicines(user_id):
    """Fetches all medicines for the Dashboard table view."""
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Fetching all relevant fields needed to populate the table in the UI
        cursor.execute(
            'SELECT '
            'medicine_id, medicine_name, dosage, food_time, schedule_morning, schedule_noon, schedule_night '
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

def check_reminders():
    """Background task to query the database and send pending reminders."""
    db = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # This query assumes a separate 'reminders' table is pre-populated with specific times.
        cursor.execute(
            "SELECT r.reminder_id, r.reminder_datetime, u.email, m.medicine_name, m.dosage "
            "FROM reminders r "
            "JOIN medicines m ON r.medicine_id=m.medicine_id "
            "JOIN users u ON m.user_id=u.user_id "
            "WHERE r.status='Pending'"
        )
        reminders = cursor.fetchall()
        now = datetime.now()
        
        for r in reminders:
            reminder_time = r['reminder_datetime']
            
            # Check if the current time is past the reminder time (with a small buffer)
            if now >= reminder_time and (now - reminder_time).total_seconds() < 120: 
                subject = f"Time for your medicine: {r['medicine_name']}"
                message = f"Please take your medicine {r['medicine_name']} ({r['dosage']}) now. Scheduled for {reminder_time.strftime('%Y-%m-%d %H:%M')}"
                
                send_email_reminder(r['email'], subject, message)
                
                # Update status
                cursor.execute("UPDATE reminders SET status='Sent', sent_at=%s WHERE reminder_id=%s", (now, r['reminder_id'],))
                db.commit()
                
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
    app.run(debug=True, host='0.0.0.0')