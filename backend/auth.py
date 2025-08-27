import hashlib
import secrets
import sqlite3
from datetime import datetime
from functools import wraps
from flask import request, jsonify

# Configuration
DATABASE_PATH = 'drowsingguard.db'
SECRET_KEY = 'your-secret-key-change-in-production'

class AuthDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table des utilisateurs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
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
            
            # Table des sessions avec user_id
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    client_session_id TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration INTEGER,
                    awake_count INTEGER DEFAULT 0,
                    drowsy_count INTEGER DEFAULT 0,
                    alert_count INTEGER DEFAULT 0,
                    avg_confidence REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Table des frames avec user_id
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_frames (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    user_id INTEGER NOT NULL,
                    client_session_id TEXT,
                    frame_data TEXT NOT NULL,
                    prediction TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    frame_number INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Créer l'utilisateur admin par défaut s'il n'existe pas
            cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
            if not cursor.fetchone():
                admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, role) 
                    VALUES (?, ?, ?, ?)
                ''', ('admin', 'admin@drowsingguard.com', admin_password, 'admin'))
                print("👑 Utilisateur admin créé: admin / admin123")
            
            conn.commit()

# Instance de la base de données
auth_db = AuthDatabase(DATABASE_PATH)

# Fonctions d'authentification
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    return hash_password(password) == password_hash

def generate_token(user_id):
    # Token simple pour la démo - en production, utiliser JWT
    return secrets.token_urlsafe(32)

def verify_token(token):
    # En production, vérifier le token dans une table de sessions
    # Pour la démo, on accepte tous les tokens valides
    if len(token) >= 32:
        # Récupérer l'utilisateur depuis la base
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, email, role FROM users WHERE is_active = 1 LIMIT 1')
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'role': user[3]
                }
    return None

# Décorateur pour vérifier l'authentification
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token d\'authentification requis'}), 401
        
        token = auth_header.split(' ')[1]
        user = verify_token(token)
        if not user:
            return jsonify({'error': 'Token invalide ou expiré'}), 401
        
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function

# Décorateur pour vérifier le rôle admin
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user') or request.current_user['role'] != 'admin':
            return jsonify({'error': 'Accès administrateur requis'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Fonctions de base de données
def get_user_sessions(user_id, limit=20):
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, client_session_id, start_time, end_time, duration,
                   awake_count, drowsy_count, alert_count, avg_confidence, created_at
            FROM sessions 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'id': row[0],
                'client_session_id': row[1],
                'start_time': row[2],
                'end_time': row[3],
                'duration': row[4],
                'awake_count': row[5],
                'drowsy_count': row[6],
                'alert_count': row[7],
                'avg_confidence': row[8],
                'created_at': row[9]
            })
        return sessions

def get_all_sessions(limit=20):
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.id, s.client_session_id, s.start_time, s.end_time, s.duration,
                   s.awake_count, s.drowsy_count, s.alert_count, s.avg_confidence, 
                   s.created_at, u.username
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            ORDER BY s.created_at DESC
            LIMIT ?
        ''', (limit,))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'id': row[0],
                'client_session_id': row[1],
                'start_time': row[2],
                'end_time': row[3],
                'duration': row[4],
                'awake_count': row[5],
                'drowsy_count': row[6],
                'alert_count': row[7],
                'avg_confidence': row[8],
                'created_at': row[9],
                'username': row[10]
            })
        return sessions

def can_user_access_session(user_id, session_id):
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM sessions WHERE id = ?', (session_id,))
        result = cursor.fetchone()
        return result and result[0] == user_id

def get_session_id_by_client_id(client_session_id, user_id):
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM sessions WHERE client_session_id = ? AND user_id = ?', 
                      (client_session_id, user_id))
        result = cursor.fetchone()
        return result[0] if result else None
