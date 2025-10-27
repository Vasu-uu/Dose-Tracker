CREATE DATABASE IF NOT EXISTS medicine_reminder;

USE medicine_reminder;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE medicines (
    medicine_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    medicine_name VARCHAR(100) NOT NULL,
    dosage VARCHAR(50),
    food_time ENUM('Before', 'After'),
    schedule_morning BOOLEAN DEFAULT 0,
    schedule_noon BOOLEAN DEFAULT 0,
    schedule_night BOOLEAN DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE reminders (
    reminder_id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    reminder_datetime DATETIME NOT NULL,
    status ENUM('Pending', 'Sent') DEFAULT 'Pending',
    sent_at DATETIME NULL,
    FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id) ON DELETE CASCADE
);