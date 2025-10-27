````markdown
# Dose Tracker - Medicine Reminder App

This is a web application that helps users track their medicine schedules and sends automatic reminders for each dose.

## Prerequisites
- **Python 3**
- **MySQL server** (like MySQL Community Server, XAMPP, or MAMP)

---

## How to Run

### 1. Set up the Database
1. Make sure your MySQL server is running.
2. Open your MySQL client (like MySQL Workbench, phpMyAdmin, or the command line).
3. Create tables from the queries given in file 'mysql.sql'. This will create the **medicine_reminder** database and all the required tables (`users`, `medicines`, `reminders`).

---

### 2. Set up a Virtual Environment
It’s highly recommended to run this project in a virtual environment.

Open your terminal in the project folder and create an environment:
```bash
python -m venv env
````

Activate the environment:

* On **Windows**:

  ```bash
  .\\env\\Scripts\\activate
  ```
* On **macOS/Linux**:

  ```bash
  source env/bin/activate
  ```

---

### 3. Install Python Libraries

With your virtual environment active, install the required dependencies:

```bash
pip install flask flask_cors flask_mail mysql-connector-python schedule
```

---

### 4. Configure the Application

You must edit the `app.py` file to add your local database password.

#### Database Configuration

Open `app.py` and find the `db_config` section (around line 18):

```python
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Vasu2005",  # <-- Change this to your MySQL password
    "database": "medicine_reminder"
}
```

---

### 5. Run the Server

In your terminal (with the virtual environment still active), start the Flask server:

```bash
python app.py
```

The server will start on [http://127.0.0.1:5000](http://127.0.0.1:5000).

Keep this terminal running.

---

### 6. Use the App! 🚀

1. Open your web browser.
2. Go to [http://127.0.0.1:5000](http://127.0.0.1:5000).
3. The website will load — you can now create an account, log in, and add medicines.

```
```
