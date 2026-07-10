import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st
import hashlib
import secrets
import random

DB_PATH = "voyagepro.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_database():
    """Initialise toutes les tables de la base de données"""
    conn = get_connection()
    c = conn.cursor()
    
    # Table des voyages
    c.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_name TEXT NOT NULL,
            destination TEXT NOT NULL,
            departure_date TEXT NOT NULL,
            bus_number TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # Table des utilisateurs (admin + clients)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER,
            role TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            username TEXT UNIQUE,
            password TEXT,
            access_code TEXT UNIQUE,
            seat_number INTEGER,
            seat_row INTEGER,
            seat_col INTEGER,
            seat_label TEXT,
            category TEXT DEFAULT 'standard',
            group_id INTEGER,
            phone TEXT,
            email TEXT,
            points INTEGER DEFAULT 0,
            trips_count INTEGER DEFAULT 0,
            checked_in BOOLEAN DEFAULT 0,
            checked_in_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trip_id) REFERENCES trips(id)
        )
    ''')
    
    # Table des messages (chat)
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER,
            sender_id INTEGER,
            receiver_id INTEGER,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trip_id) REFERENCES trips(id),
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
    ''')
    
    # Table des notifications
    c.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER,
            user_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trip_id) REFERENCES trips(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Table de fidélité historique
    c.execute('''
        CREATE TABLE IF NOT EXISTS loyalty_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            trip_id INTEGER,
            points_earned INTEGER,
            points_used INTEGER,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (trip_id) REFERENCES trips(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_trip(trip_name, destination, departure_date, bus_number):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO trips (trip_name, destination, departure_date, bus_number)
        VALUES (?, ?, ?, ?)
    ''', (trip_name, destination, departure_date, bus_number))
    trip_id = c.lastrowid
    conn.commit()
    conn.close()
    return trip_id

def get_trips():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM trips ORDER BY created_at DESC", conn)
    conn.close()
    return df

def create_admin(trip_id, first_name, last_name, username, password):
    conn = get_connection()
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute('''
            INSERT INTO users (trip_id, role, first_name, last_name, username, password)
            VALUES (?, 'admin', ?, ?, ?, ?)
        ''', (trip_id, first_name, last_name, username, hashed_pw))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def create_client(trip_id, first_name, last_name, category=None, group_id=None, phone=None, email=None):
    conn = get_connection()
    c = conn.cursor()
    
    # Générer credentials automatiques
    username = f"{first_name.lower()}.{last_name.lower()}"
    password = first_name.capitalize()
    access_code = secrets.token_hex(3).upper()
    
    try:
        c.execute('''
            INSERT INTO users (trip_id, role, first_name, last_name, username, password, 
                             access_code, category, group_id, phone, email)
            VALUES (?, 'client', ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (trip_id, first_name, last_name, username, hashlib.sha256(password.encode()).hexdigest(),
              access_code, category, group_id, phone, email))
        user_id = c.lastrowid
        conn.commit()
        return user_id, username, password, access_code
    except sqlite3.IntegrityError:
        # Si username existe, ajouter un nombre
        username = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,999)}"
        c.execute('''
            INSERT INTO users (trip_id, role, first_name, last_name, username, password, 
                             access_code, category, group_id, phone, email)
            VALUES (?, 'client', ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (trip_id, first_name, last_name, username, hashlib.sha256(password.encode()).hexdigest(),
              access_code, category, group_id, phone, email))
        user_id = c.lastrowid
        conn.commit()
        return user_id, username, password, access_code
    finally:
        conn.close()

def get_users_by_trip(trip_id, role=None):
    conn = get_connection()
    query = "SELECT * FROM users WHERE trip_id = ?"
    params = [trip_id]
    if role:
        query += " AND role = ?"
        params.append(role)
    query += " ORDER BY created_at"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def authenticate_user(username, password, trip_id=None):
    conn = get_connection()
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    
    if trip_id:
        c.execute('''
            SELECT * FROM users WHERE username = ? AND password = ? AND trip_id = ?
        ''', (username, hashed_pw, trip_id))
    else:
        c.execute('''
            SELECT * FROM users WHERE username = ? AND password = ?
        ''', (username, hashed_pw))
    
    user = c.fetchone()
    conn.close()
    
    if user:
        columns = [description[0] for description in c.description]
        return dict(zip(columns, user))
    return None

def update_seat(user_id, seat_number, seat_row, seat_col):
    seat_label = f"{seat_row}{chr(64 + seat_col)}"
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE users SET seat_number = ?, seat_row = ?, seat_col = ?, seat_label = ? WHERE id = ?
    ''', (seat_number, seat_row, seat_col, seat_label, user_id))
    conn.commit()
    conn.close()

def check_in_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE users SET checked_in = 1, checked_in_at = ? WHERE id = ?
    ''', (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def admin_check_in_user(user_id):
    """Admin peut check-in n'importe qui"""
    check_in_user(user_id)

def get_messages(trip_id, user_id=None, other_user_id=None):
    conn = get_connection()
    if user_id and other_user_id:
        df = pd.read_sql_query('''
            SELECT m.*, 
                   s.first_name as sender_name, 
                   r.first_name as receiver_name
            FROM messages m
            JOIN users s ON m.sender_id = s.id
            JOIN users r ON m.receiver_id = r.id
            WHERE m.trip_id = ? AND 
                  ((m.sender_id = ? AND m.receiver_id = ?) OR 
                   (m.sender_id = ? AND m.receiver_id = ?))
            ORDER BY m.created_at
        ''', conn, params=(trip_id, user_id, other_user_id, other_user_id, user_id))
    else:
        df = pd.read_sql_query('''
            SELECT m.*, s.first_name as sender_name 
            FROM messages m
            JOIN users s ON m.sender_id = s.id
            WHERE m.trip_id = ?
            ORDER BY m.created_at DESC
        ''', conn, params=(trip_id,))
    conn.close()
    return df

def send_message(trip_id, sender_id, receiver_id, message):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO messages (trip_id, sender_id, receiver_id, message)
        VALUES (?, ?, ?, ?)
    ''', (trip_id, sender_id, receiver_id, message))
    conn.commit()
    conn.close()

def add_points(user_id, points, trip_id=None, description=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET points = points + ?, trips_count = trips_count + 1 WHERE id = ?',
              (points, user_id))
    c.execute('''
        INSERT INTO loyalty_history (user_id, trip_id, points_earned, description)
        VALUES (?, ?, ?, ?)
    ''', (user_id, trip_id, points, description))
    conn.commit()
    conn.close()

def get_client_by_code(access_code):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE access_code = ? AND role = "client"', (access_code,))
    user = c.fetchone()
    conn.close()
    if user:
        columns = [description[0] for description in c.description]
        return dict(zip(columns, user))
    return None

def get_user_by_id(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        columns = [description[0] for description in c.description]
        return dict(zip(columns, user))
    return None

# Initialiser la base de données au démarrage
init_database()
