CREATE DATABASE IF NOT EXISTS medicine_reminder;

USE medicine_reminder;

CREATE TABLE users (
    user_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100),
    username VARCHAR(100),
    age INT,
    email VARCHAR(100),
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE KEY (username),
    UNIQUE KEY (email)
);

CREATE TABLE medicines (
    medicine_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    medicine_name VARCHAR(150) NOT NULL,
    dosage VARCHAR(100),
    start_date DATE,
    end_date DATE,
    times_per_day INT DEFAULT 0,
    schedule_morning BOOLEAN DEFAULT 0,
    schedule_noon BOOLEAN DEFAULT 0,
    schedule_night BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (medicine_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE reminders (
    reminder_id INT NOT NULL AUTO_INCREMENT,
    medicine_id INT NOT NULL,
    reminder_datetime DATETIME NOT NULL,
    status ENUM('Pending', 'Sent', 'Done') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (reminder_id),
    FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id) ON DELETE CASCADE
);
