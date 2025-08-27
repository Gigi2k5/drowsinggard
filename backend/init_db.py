#!/usr/bin/env python3
"""Script d'initialisation forcée de la base de données"""

import sqlite3
import hashlib
import os

def init_database():
    """Initialiser la base de données"""
    db_path = 'sessions.db'
    
    # Supprimer la base existante si elle existe
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️ Base de données {db_path} supprimée")
    
    print(f"🔧 Création de la nouvelle base de données {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table des utilisateurs
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    print("✅ Table 'users' créée")
    
    # Table des sessions
    cursor.execute('''
        CREATE TABLE sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            start_time TEXT,
            end_time TEXT,
            duration INTEGER,
            awake_count INTEGER,
            drowsy_count INTEGER,
            alert_count INTEGER,
            avg_confidence REAL,
            client_session_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Table 'sessions' créée")
    
    # Table des frames
    cursor.execute('''
        CREATE TABLE session_frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            user_id INTEGER DEFAULT 1,
            client_session_id INTEGER,
            frame_data TEXT,
            timestamp REAL,
            prediction TEXT,
            confidence REAL,
            frame_number INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        )
    ''')
    print("✅ Table 'session_frames' créée")
    
    # Créer l'utilisateur admin
    admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, role) 
        VALUES (?, ?, ?, ?)
    ''', ('admin', 'admin@drowsingguard.com', admin_password, 'admin'))
    print("👑 Utilisateur admin créé: admin / admin123")
    
    # Créer un utilisateur de test
    user_password = hashlib.sha256('user123'.encode()).hexdigest()
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, role) 
        VALUES (?, ?, ?, ?)
    ''', ('user', 'user@drowsingguard.com', user_password, 'user'))
    print("👤 Utilisateur créé: user / user123")
    
    conn.commit()
    conn.close()
    
    print("🎉 Base de données initialisée avec succès!")
    return True

if __name__ == "__main__":
    init_database()
