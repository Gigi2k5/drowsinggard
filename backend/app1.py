from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
import cv2
import numpy as np
import base64
from facenet_pytorch import MTCNN
import io
import os
import json
from collections import deque
import sqlite3
import sys

# Configuration de l'application Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
CORS(app)  # Permet les requêtes cross-origin

# Cache pour les prédictions (éviter de retraiter la même image)
from functools import lru_cache
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

# Cache des prédictions récentes
prediction_cache = {}
CACHE_SIZE = 100

def get_image_hash(image_data):
    """Générer un hash de l'image pour le cache"""
    if isinstance(image_data, str):
        if 'base64,' in image_data:
            image_data = image_data.split(',')[1]
    return hashlib.md5(image_data.encode()).hexdigest()

# Optionnel: tentative d'import de dlib pour les landmarks
try:
    import dlib
    import face_recognition
    DLIB_AVAILABLE = True
except ImportError:
    DLIB_AVAILABLE = False
    print("Dlib non disponible. Fonctionnalité de landmarks désactivée.")


class SessionDatabase:
    def __init__(self, db_path='sessions.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialiser la base de données avec une nouvelle connexion à chaque fois"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                start_time TEXT,
                end_time TEXT,
                duration INTEGER,
                awake_count INTEGER,
                drowsy_count INTEGER,
                alert_count INTEGER,
                avg_confidence REAL,
                client_session_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Ajout rétroactif des colonnes si absentes
        try:
            cursor.execute('ALTER TABLE sessions ADD COLUMN user_id INTEGER DEFAULT 1')
        except Exception:
            pass
        try:
            cursor.execute('ALTER TABLE sessions ADD COLUMN client_session_id TEXT')
        except Exception:
            pass
        
        # Table des frames vidéo des sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_frames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                user_id INTEGER DEFAULT 1,
                client_session_id TEXT,
                frame_data TEXT,
                timestamp REAL,
                prediction TEXT,
                confidence REAL,
                frame_number INTEGER,
                FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
            )
        ''')
        # Ajout rétroactif des colonnes si absentes
        try:
            cursor.execute('ALTER TABLE session_frames ADD COLUMN user_id INTEGER DEFAULT 1')
        except Exception:
            pass
        try:
            cursor.execute('ALTER TABLE session_frames ADD COLUMN client_session_id TEXT')
        except Exception:
            pass
        
        conn.commit()
        conn.close()
        
        # Initialiser la base de données des utilisateurs
        self.init_users_database()

    def init_users_database(self):
        """Initialiser la base de données des utilisateurs"""
        conn = sqlite3.connect(self.db_path)
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
        
        # Créer l'utilisateur admin par défaut s'il n'existe pas
        cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
        if not cursor.fetchone():
            admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role) 
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin@drowsingguard.com', admin_password, 'admin'))
            print("👑 Utilisateur admin créé: admin / admin123")
        
        # Créer un utilisateur de test s'il n'existe pas
        cursor.execute('SELECT id FROM users WHERE username = ?', ('user',))
        if not cursor.fetchone():
            user_password = hashlib.sha256('user123'.encode()).hexdigest()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role) 
                VALUES (?, ?, ?, ?)
            ''', ('user', 'user@drowsingguard.com', user_password, 'user'))
            print("👤 Utilisateur créé: user / user123")
        
        conn.commit()
        conn.close()

    def insert_session(self, session_data):
        """Insérer une nouvelle session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (user_id, start_time, end_time, duration, awake_count, drowsy_count, alert_count, avg_confidence, client_session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_data.get('user_id', 1), 
            session_data['start_time'], 
            session_data['end_time'], 
            session_data['duration'],
            session_data['awake_count'], 
            session_data['drowsy_count'], 
            session_data['alert_count'], 
            session_data['avg_confidence'],
            session_data.get('client_session_id')
        ))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id

    def get_sessions(self, limit=10):
        """Récupérer les sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?', (limit,))
        sessions = cursor.fetchall()
        conn.close()
        return sessions

    def delete_session(self, session_id):
        """Supprimer une session et ses frames associées"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Supprimer d'abord les frames associées
        cursor.execute('DELETE FROM session_frames WHERE session_id = ?', (session_id,))
        
        # Puis supprimer la session
        cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
        
        conn.commit()
        conn.close()

    def clear_sessions(self):
        """Effacer toutes les sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions')
        conn.commit()
        conn.close()

    def insert_frame(self, session_id, frame_data, timestamp, prediction, confidence, frame_number, client_session_id=None, user_id=None):
        """Insérer une frame vidéo pour une session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO session_frames (session_id, user_id, client_session_id, frame_data, timestamp, prediction, confidence, frame_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id or 1, client_session_id, frame_data, timestamp, prediction, confidence, frame_number))
        conn.commit()
        conn.close()

    def get_session_frames(self, session_id):
        """Récupérer toutes les frames d'une session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT frame_data, timestamp, prediction, confidence, frame_number
            FROM session_frames 
            WHERE session_id = ? 
            ORDER BY frame_number ASC
        ''', (session_id,))
        frames = cursor.fetchall()
        conn.close()
        return frames

    def delete_session_frames(self, session_id):
        """Supprimer toutes les frames d'une session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM session_frames WHERE session_id = ?', (session_id,))
        conn.commit()
        conn.close()


# Fonctions d'authentification
def hash_password(password):
    """Hasher un mot de passe"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Vérifier un mot de passe"""
    return hash_password(password) == password_hash

def generate_token():
    """Générer un token d'authentification"""
    return secrets.token_urlsafe(32)

def verify_token(token):
    """Vérifier un token d'authentification"""
    # Pour simplifier, on stocke les tokens en mémoire
    # En production, utilisez une base de données ou Redis
    return token in active_tokens

# Stockage des tokens actifs (en mémoire - à améliorer en production)
active_tokens = {}
user_tokens = {}

def require_auth(f):
    """Décorateur pour protéger les routes nécessitant une authentification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Token d\'authentification requis'}), 401
        
        token = token.split(' ')[1]
        if not verify_token(token):
            return jsonify({'error': 'Token invalide'}), 401
        
        # Ajouter l'utilisateur à la requête
        request.current_user = user_tokens.get(token)
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Décorateur pour protéger les routes nécessitant des droits admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Token d\'authentification requis'}), 401
        
        token = token.split(' ')[1]
        if not verify_token(token):
            return jsonify({'error': 'Token invalide'}), 401
        
        user = user_tokens.get(token)
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Droits administrateur requis'}), 403
        
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function


class MobileNetDrowsiness(nn.Module):
    def __init__(self):
        super().__init__()
        base_model = models.mobilenet_v2(weights=None)
        base_model.classifier[1] = nn.Sequential(  # CLASSIFIER[1] doit être un Sequential
            nn.Linear(1280, 1),
            nn.Sigmoid()
        )
        self.features = base_model.features
        self.classifier = base_model.classifier  # classifier[1][0].weight sera trouvé

    def forward(self, x):
        x = self.features(x)
        x = nn.functional.adaptive_avg_pool2d(x, (1, 1))
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x



class DrowsinessDetector:
    def __init__(self, model_path='mobilenet_drowsiness.pth'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Utilisation du device: {self.device}")

        self.classes = ['awake', 'drowsy']
        self.prediction_buffer = deque(maxlen=5)
        self.model = MobileNetDrowsiness()

        # Optimisations PyTorch
        if torch.cuda.is_available():
            # Mixed precision pour CUDA
            self.scaler = torch.cuda.amp.GradScaler()
            print("✅ Mixed precision CUDA activé")
        
        # Charger les poids
        if os.path.exists(model_path):
            try:
                checkpoint = torch.load(model_path, map_location=self.device)
                if isinstance(checkpoint, dict) and (
                    'model_state_dict' in checkpoint or 'state_dict' in checkpoint
                ):
                    if 'model_state_dict' in checkpoint:
                        self.model.load_state_dict(checkpoint['model_state_dict'])
                    else:
                        self.model.load_state_dict(checkpoint['state_dict'])
                else:
                    self.model.load_state_dict(checkpoint)

                print(f"✅ Modèle MobileNet chargé depuis {model_path}")
            except Exception as e:
                print(f"❌ Erreur lors du chargement des poids : {str(e)}")
                print("⚠️ Utilisation d'un modèle non entraîné")
        else:
            print(f"📁 Modèle {model_path} non trouvé, utilisation d'un modèle non entraîné")

        self.model.to(self.device)
        self.model.eval()
        
        # Optimisation : JIT compilation si disponible
        try:
            if hasattr(torch, 'jit') and torch.jit.is_available():
                self.model = torch.jit.optimize_for_inference(torch.jit.script(self.model))
                print("✅ Modèle optimisé avec TorchScript")
        except Exception as e:
            print(f"⚠️ TorchScript non disponible: {e}")

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

        # Détection faciale avec fallback
        self.use_face_detection = True
        self.use_opencv_fallback = True  # Activer OpenCV par défaut
        self.use_mtcnn = False  # Désactiver MTCNN par défaut (trop strict)
        
        try:
            if self.use_mtcnn:
                self.detector_face = MTCNN(
                    keep_all=False, 
                    device=self.device,
                    min_face_size=20,  # Visages plus petits
                    thresholds=[0.6, 0.7, 0.7],  # Plus permissif
                    factor=0.8,  # Échelle de pyramide plus fine
                    post_process=False  # Désactiver le post-processing pour la vitesse
                )
                print("✅ MTCNN initialisé avec paramètres optimisés")
            else:
                print("🔄 MTCNN désactivé, utilisation d'OpenCV uniquement")
                self.detector_face = None
        except Exception as e:
            print(f"❌ Erreur MTCNN: {e}")
            print("⚠️ MTCNN désactivé, fallback vers OpenCV")
            self.detector_face = None
            # Ne pas désactiver use_face_detection car OpenCV est disponible en fallback

        # Optionnel : landmarks avec dlib
        self.use_landmarks = False
        if DLIB_AVAILABLE:
            try:
                predictor_path = 'shape_predictor_68_face_landmarks.dat'
                if os.path.exists(predictor_path):
                    self.predictor = dlib.shape_predictor(predictor_path)
                    self.face_detector = dlib.get_frontal_face_detector()
                    self.use_landmarks = True
                    print("Détecteur de landmarks disponible")
                else:
                    print(f"Fichier {predictor_path} non trouvé")
            except Exception as e:
                print(f"Erreur chargement landmarks : {e}")

    def crop_face(self, image_pil):
        """Détecter et recadrer le visage avec OpenCV en priorité, MTCNN en fallback"""
        try:
            print(f"🔍 Tentative détection faciale sur image {image_pil.size}")
            
            # Priorité 1 : OpenCV (plus fiable)
            if self.use_opencv_fallback:
                try:
                    import cv2
                    import numpy as np
                    
                    # Convertir PIL en numpy array
                    img_array = np.array(image_pil)
                    
                    # Détecteur de visages OpenCV (plus permissif)
                    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                    
                    faces = face_cascade.detectMultiScale(
                        gray, 
                        scaleFactor=1.1, 
                        minNeighbors=3, 
                        minSize=(30, 30)
                    )
                    
                    if len(faces) > 0:
                        print(f"✅ Visage détecté par OpenCV: {len(faces)} visage(s)")
                        # Prendre le plus grand visage
                        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                        face_img = image_pil.crop((x, y, x+w, y+h))
                        return face_img
                    else:
                        print("⚠️ Aucun visage détecté par OpenCV")
                        
                except Exception as cv_error:
                    print(f"⚠️ OpenCV échoué: {cv_error}")
            
            # Priorité 2 : MTCNN (si disponible et OpenCV échoue)
            if self.use_mtcnn and self.use_face_detection and self.detector_face is not None:
                try:
                    face = self.detector_face(image_pil)
                    
                    if face is not None:
                        print(f"✅ Visage détecté par MTCNN: {face.shape}")
                        # Convertir le tensor en image PIL
                        if hasattr(face, 'permute'):
                            face = face.permute(1, 2, 0).byte().cpu().numpy()
                            face_img = Image.fromarray(face)
                        else:
                            face_img = face
                        return face_img
                    else:
                        print("⚠️ Aucun visage détecté par MTCNN")
                        
                except Exception as mtcnn_error:
                    print(f"⚠️ MTCNN échoué: {mtcnn_error}")
            elif not self.use_mtcnn:
                print("🔄 MTCNN désactivé, passage à l'image complète")
            
            # Dernier fallback : retourner l'image complète
            print("🔄 Aucun visage détecté, utilisation de l'image complète")
            return image_pil
                
        except Exception as e:
            print(f"❌ Erreur crop_face: {e}")
            print(f"🔍 Type d'image: {type(image_pil)}")
            print(f"🔍 Taille image: {image_pil.size if hasattr(image_pil, 'size') else 'N/A'}")
            return image_pil

    def preprocess_image(self, image):
        try:
            if isinstance(image, str):
                if 'base64,' in image:
                    image_data = base64.b64decode(image.split(',')[1])
                else:
                    image_data = base64.b64decode(image)
                image = Image.open(io.BytesIO(image_data))
            elif isinstance(image, np.ndarray):
                image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            image = image.convert('RGB')
            
            # Crop face: utiliser OpenCV (toujours disponible) ou MTCNN
            if self.use_face_detection:
                image = self.crop_face(image)
            else:
                print("🔄 Détection faciale désactivée, utilisation de l'image complète")

            image_tensor = self.transform(image).unsqueeze(0)
            return image_tensor.to(self.device)
        except Exception as e:
            print(f"Erreur lors du préprocessing: {e}")
            raise

    def extract_eye_features(self, image):
        if not self.use_landmarks:
            return None

        try:
            if isinstance(image, Image.Image):
                image_array = np.array(image)
            else:
                image_array = image

            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            faces = self.face_detector(gray)

            eye_features = []
            for face in faces:
                landmarks = self.predictor(gray, face)
                left_eye = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(36, 42)]
                right_eye = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(42, 48)]

                left_ear = self.eye_aspect_ratio(left_eye)
                right_ear = self.eye_aspect_ratio(right_eye)
                ear = (left_ear + right_ear) / 2.0
                eye_features.append(ear)

            return eye_features
        except Exception as e:
            print(f"Erreur extraction features: {e}")
            return None

    def eye_aspect_ratio(self, eye):
        try:
            A = np.linalg.norm(np.array(eye[1]) - np.array(eye[5]))
            B = np.linalg.norm(np.array(eye[2]) - np.array(eye[4]))
            C = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))
            return (A + B) / (2.0 * C) if C != 0 else 0
        except:
            return 0

    def predict(self, image, threshold: float = 0.5, buffer_size: int = None):
        try:
            # Vérifier le cache d'abord
            image_hash = get_image_hash(image)
            if image_hash in prediction_cache:
                cached_result = prediction_cache[image_hash]
                print(f"✅ Cache hit pour image {image_hash[:8]}...")
                return cached_result
            
            input_tensor = self.preprocess_image(image)

            with torch.no_grad():
                # Utiliser mixed precision si CUDA disponible
                if torch.cuda.is_available() and hasattr(self, 'scaler'):
                    with torch.cuda.amp.autocast():
                        outputs = self.model(input_tensor)
                else:
                    outputs = self.model(input_tensor)
                    
                probability = torch.sigmoid(outputs)
                prob_value = float(probability.item())
                confidence_score = prob_value * 100
                # Utiliser le seuil fourni (par défaut 0.5)
                predicted_class = 'drowsy' if prob_value > float(threshold) else 'awake'

            # Stocker la prédiction brute dans le buffer interne
            self.prediction_buffer.append((predicted_class, confidence_score))

            # Construire la fenêtre de décision en respectant buffer_size si fourni
            recent_predictions = list(self.prediction_buffer)
            if buffer_size is not None:
                try:
                    bsize = int(buffer_size)
                    if bsize > 0:
                        recent_predictions = recent_predictions[-bsize:]
                except Exception:
                    pass

            drowsy_count = sum(1 for pred, _ in recent_predictions if pred == 'drowsy')

            # Décision finale : majorité simple sur la fenêtre
            final_prediction = 'drowsy' if drowsy_count >= len(recent_predictions) // 2 else 'awake'
            avg_confidence = np.mean([conf for _, conf in recent_predictions]) if recent_predictions else confidence_score

            result = {
                'prediction': final_prediction,
                'confidence': round(avg_confidence, 2),
                'raw_prediction': predicted_class,
                'raw_confidence': round(confidence_score, 2),
                'buffer_size': len(self.prediction_buffer),
                'used_threshold': float(threshold),
                'used_window': len(recent_predictions)
            }
            
            # Mettre en cache le résultat
            if len(prediction_cache) >= CACHE_SIZE:
                # Supprimer le plus ancien
                oldest_key = next(iter(prediction_cache))
                del prediction_cache[oldest_key]
            
            prediction_cache[image_hash] = result
            print(f"💾 Cache miss, nouvelle prédiction mise en cache")

            return result

        except Exception as e:
            print(f"Erreur lors de la prédiction: {e}")
            return {
                'prediction': 'awake',
                'confidence': 0.0,
                'error': str(e)
            }

# Initialiser le détecteur
detector = None

def init_detector():
    global detector
    if detector is None:
        detector = DrowsinessDetector(model_path='mobilenet_drowsiness.pth')

    return detector


# Routes API

# Routes d'authentification
@app.route('/auth/register', methods=['POST'])
def register():
    """Créer un nouveau compte utilisateur"""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ['username', 'email', 'password']):
            return jsonify({'error': 'Tous les champs sont requis'}), 400
        
        username = data['username']
        email = data['email']
        password = data['password']
        
        # Vérifier si l'utilisateur existe déjà
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Nom d\'utilisateur ou email déjà utilisé'}), 400
        
        # Créer le nouvel utilisateur
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role) 
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, 'user'))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Compte créé avec succès'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """Connexion utilisateur"""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ['username', 'password']):
            return jsonify({'error': 'Nom d\'utilisateur et mot de passe requis'}), 400
        
        username = data['username']
        password = data['password']
        
        # Vérifier les identifiants
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, password_hash, role FROM users WHERE username = ? AND is_active = 1', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not verify_password(password, user[3]):
            return jsonify({'error': 'Identifiants invalides'}), 401
        
        # Générer un token
        token = generate_token()
        active_tokens[token] = True
        user_tokens[token] = {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'role': user[4]
        }
        
        # Mettre à jour la dernière connexion
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user[0],))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[4]
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/profile', methods=['GET'])
@require_auth
def profile():
    """Récupérer le profil de l'utilisateur connecté"""
    return jsonify({
        'success': True,
        'user': request.current_user
    })

# Routes d'administration
@app.route('/admin/users', methods=['GET'])
@require_admin
def admin_users():
    """Récupérer tous les utilisateurs (admin seulement)"""
    try:
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, role, created_at, last_login, is_active FROM users ORDER BY created_at DESC')
        users = cursor.fetchall()
        conn.close()
        
        user_list = []
        for user in users:
            user_list.append({
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[3],
                'created_at': user[4],
                'last_login': user[5],
                'is_active': bool(user[6])
            })
        
        return jsonify({'success': True, 'users': user_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/users/<int:user_id>/sessions', methods=['GET'])
@require_admin
def admin_user_sessions(user_id):
    """Récupérer les sessions d'un utilisateur spécifique (admin seulement)"""
    try:
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, user_id, start_time, end_time, duration, awake_count, drowsy_count, alert_count, avg_confidence, client_session_id, created_at
            FROM sessions WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        sessions = cursor.fetchall()
        conn.close()
        
        session_list = []
        for session in sessions:
            session_list.append({
                'id': session[0],
                'user_id': session[1],
                'start_time': session[2],
                'end_time': session[3],
                'duration': session[4],
                'awake_count': session[5],
                'drowsy_count': session[6],
                'alert_count': session[7],
                'avg_confidence': session[8],
                'client_session_id': session[9],
                'created_at': session[10]
            })
        
        return jsonify({'success': True, 'sessions': session_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
@require_admin
def admin_delete_user(user_id):
    """Supprimer un utilisateur (admin seulement)"""
    try:
        # Empêcher la suppression de l'admin principal
        if user_id == 1:
            return jsonify({'error': 'Impossible de supprimer l\'administrateur principal'}), 400
        
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        
        # Supprimer les sessions et frames de l'utilisateur
        cursor.execute('DELETE FROM session_frames WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
        
        # Supprimer l'utilisateur
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Utilisateur supprimé avec succès'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Routes API
@app.route('/')
def index():
    """Page d'accueil avec documentation de l'API"""
    detector = init_detector()
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Détection de Somnolence</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold; }
            .post { background: #28a745; }
            .get { background: #007bff; }
            .delete { background: #dc3545; }
            code { background: #e9ecef; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 API Détection de Somnolence</h1>
            <p>API Flask pour la détection de somnolence en temps réel avec PyTorch.</p>
            
            <h2>📋 Endpoints disponibles</h2>
            
            <h3>🔐 Authentification</h3>
            <div class="endpoint">
                <span class="method post">POST</span> <code>/auth/register</code>
                <p>Créer un nouveau compte utilisateur</p>
                <strong>Body:</strong> <code>{"username": "...", "email": "...", "password": "..."}</code>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/auth/login</code>
                <p>Se connecter</p>
                <strong>Body:</strong> <code>{"username": "...", "password": "..."}</code>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/auth/profile</code>
                <p>Récupérer le profil utilisateur (authentification requise)</p>
            </div>
            
            <h3>👑 Administration (Admin seulement)</h3>
            <div class="endpoint">
                <span class="method get">GET</span> <code>/admin/users</code>
                <p>Lister tous les utilisateurs</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/admin/users/&lt;user_id&gt;/sessions</code>
                <p>Voir les sessions d'un utilisateur</p>
            </div>
            
            <div class="endpoint">
                <span class="method delete">DELETE</span> <code>/admin/users/&lt;user_id&gt;</code>
                <p>Supprimer un utilisateur</p>
            </div>
            
            <h3>📊 Détection et Sessions</h3>
            <div class="endpoint">
                <span class="method post">POST</span> <code>/predict</code>
                <p>Analyser une image pour détecter la somnolence</p>
                <strong>Body:</strong> <code>{"image": "data:image/jpeg;base64,..."}</code>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/save_session</code>
                <p>Sauvegarder une session de détection (authentification requise)</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/get_sessions</code>
                <p>Récupérer l'historique des sessions (authentification requise)</p>
            </div>
            
            <div class="endpoint">
                <span class="method delete">DELETE</span> <code>/delete_session/&lt;session_id&gt;</code>
                <p>Supprimer une session spécifique (authentification requise)</p>
            </div>
            
            <div class="endpoint">
                <span class="method delete">DELETE</span> <code>/clear_sessions</code>
                <p>Supprimer toutes vos sessions (authentification requise)</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/get_session_frames/&lt;id&gt;</code>
                <p>Récupérer les frames vidéo d'une session (authentification requise)</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/save_frame</code>
                <p>Sauvegarder une frame vidéo (authentification requise)</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/health</code>
                <p>Vérifier l'état de l'API</p>
            </div>
            
            <h2>🔧 Status</h2>
            <p><strong>Device:</strong> {{ device }}</p>
            <p><strong>Modèle:</strong> {{ model_loaded }}</p>
            <p><strong>Landmarks:</strong> {{ landmarks_available }}</p>
        </div>
    </body>
    </html>
    """, 
    device=str(detector.device),
    model_loaded="Chargé" if os.path.exists('cnn_drowsiness (1).pth') else "Non entraîné",
    landmarks_available="Disponibles" if detector.use_landmarks else "Non disponibles"
    )


@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint pour prédire l'état de somnolence"""
    start_time = datetime.now()
    
    try:
        detector = init_detector()
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({
                'error': 'Image manquante dans la requête',
                'success': False
            }), 400
        # Extraire options optionnelles
        threshold = data.get('threshold', 0.5)
        buffer_size = data.get('buffer_size', None)

        # Analyser l'image (possibilité d'overrider threshold et buffer_size par requête)
        result = detector.predict(data['image'], threshold=threshold, buffer_size=buffer_size)
        
        # Calculer la latence
        end_time = datetime.now()
        latency_ms = (end_time - start_time).total_seconds() * 1000
        
        # Ajouter des métadonnées de performance
        result.update({
            'success': True,
            'timestamp': start_time.isoformat(),
            'device': str(detector.device),
            'latency_ms': round(latency_ms, 2),
            'cache_size': len(prediction_cache),
            'model_optimized': hasattr(detector.model, '_get_methods'),  # TorchScript
            'used_threshold': float(threshold) if threshold is not None else None,
            'used_buffer_size': int(buffer_size) if buffer_size is not None else None
        })
        
        # Log de performance
        print(f"⚡ Prédiction en {latency_ms:.1f}ms (cache: {len(prediction_cache)}/{CACHE_SIZE})")
        
        return jsonify(result)
        
    except Exception as e:
        end_time = datetime.now()
        latency_ms = (end_time - start_time).total_seconds() * 1000
        
        return jsonify({
            'error': f'Erreur lors de la prédiction: {str(e)}',
            'success': False,
            'timestamp': start_time.isoformat(),
            'latency_ms': round(latency_ms, 2)
        }), 500


@app.route('/save_session', methods=['POST'])
@require_auth
def save_session():
    """Sauvegarder une session"""
    try:
        data = request.get_json()
        
        # Validation des données
        required_fields = ['start_time', 'end_time', 'duration', 'awake_count', 
                          'drowsy_count', 'alert_count', 'avg_confidence']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Champ manquant: {field}',
                    'success': False
                }), 400
        
        session_data = {
            'user_id': request.current_user['id'],
            'start_time': data['start_time'],
            'end_time': data['end_time'],
            'duration': data['duration'],
            'awake_count': data['awake_count'],
            'drowsy_count': data['drowsy_count'],
            'alert_count': data['alert_count'],
            'avg_confidence': data['avg_confidence']
        }

        client_session_id = data.get('client_session_id')
        
        db = SessionDatabase()
        # Inclure client_session_id dans la session persistée pour permettre la résolution ultérieure
        if client_session_id is not None:
            session_data['client_session_id'] = client_session_id
        new_session_id = db.insert_session(session_data)
        
        # Si un client_session_id a été fourni, relier les frames orphelines
        if client_session_id is not None:
            try:
                conn = sqlite3.connect(db.db_path)
                cursor = conn.cursor()
                
                # Mapper les frames avec ce client_session_id vers le nouveau session_id
                # Cas 1: session_id est NULL ou 0 (frames orphelines normales)
                cursor.execute('''
                    UPDATE session_frames
                    SET session_id = ?
                    WHERE client_session_id = ? AND (session_id IS NULL OR session_id = 0)
                ''', (new_session_id, client_session_id))
                
                updated_count = cursor.rowcount
                print(f"✅ {updated_count} frames liées à la session {new_session_id} via client_session_id={client_session_id}")
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"⚠️ Erreur lors du mapping des frames: {e}")
        
        return jsonify({
            'message': 'Session enregistrée avec succès',
            'success': True,
            'session_id': new_session_id
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Erreur lors de la sauvegarde: {str(e)}',
            'success': False
        }), 500


@app.route('/get_sessions', methods=['GET'])
@require_auth
def get_sessions():
    """Récupérer les sessions"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        db = SessionDatabase()
        # Sélection explicite des colonnes pour éviter les décalages d'index après migration
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, start_time, end_time, duration, awake_count, drowsy_count, alert_count, avg_confidence, client_session_id, created_at
            FROM sessions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (request.current_user['id'], limit,))
        rows = cursor.fetchall()
        conn.close()

        sessions_list = []
        for row in rows:
            sessions_list.append({
                'id': row[0],
                'start_time': row[1],
                'end_time': row[2],
                'duration': row[3],
                'awake_count': row[4],
                'drowsy_count': row[5],
                'alert_count': row[6],
                'avg_confidence': row[7],
                'client_session_id': row[8],
                'created_at': row[9]
            })
        
        return jsonify({
            'sessions': sessions_list,
            'success': True
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Erreur lors de la récupération: {str(e)}',
            'success': False
        }), 500


@app.route('/delete_session/<int:session_id>', methods=['DELETE'])
@require_auth
def delete_session(session_id):
    """Supprimer une session spécifique"""
    try:
        # Vérifier que l'utilisateur peut supprimer cette session
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM sessions WHERE id = ?', (session_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Session non trouvée'}), 404
        
        if result[0] != request.current_user['id'] and request.current_user['role'] != 'admin':
            return jsonify({'error': 'Accès non autorisé'}), 403
        
        db = SessionDatabase()
        db.delete_session(session_id)
        
        return jsonify({
            'success': True, 
            'message': 'Session supprimée avec succès'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Erreur lors de la suppression: {str(e)}',
            'success': False
        }), 500


@app.route('/clear_sessions', methods=['DELETE'])
@require_auth
def clear_sessions():
    """Effacer toutes les sessions de l'utilisateur connecté"""
    try:
        # Supprimer seulement les sessions de l'utilisateur connecté
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        
        # Supprimer d'abord les frames
        cursor.execute('DELETE FROM session_frames WHERE user_id = ?', (request.current_user['id'],))
        # Puis les sessions
        cursor.execute('DELETE FROM sessions WHERE user_id = ?', (request.current_user['id'],))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Toutes vos sessions ont été supprimées'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Erreur lors de la suppression: {str(e)}',
            'success': False
        }), 500


@app.route('/get_session_frames/<int:session_id>', methods=['GET'])
@require_auth
def get_session_frames(session_id):
    """Récupérer les frames vidéo d'une session"""
    try:
        # Vérifier que l'utilisateur peut accéder à cette session
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM sessions WHERE id = ?', (session_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Session non trouvée'}), 404
        
        if result[0] != request.current_user['id'] and request.current_user['role'] != 'admin':
            return jsonify({'error': 'Accès non autorisé'}), 403
        
        db = SessionDatabase()
        frames = db.get_session_frames(session_id)
        
        # Si aucune frame trouvée, tenter un mappage automatique à partir de client_session_id
        if not frames:
            try:
                conn = sqlite3.connect(db.db_path)
                cursor = conn.cursor()
                # Récupérer le client_session_id de la session
                cursor.execute('SELECT client_session_id FROM sessions WHERE id = ?', (session_id,))
                row = cursor.fetchone()
                if row and row[0] is not None:
                    client_sid = row[0]
                    # Mapper toutes les frames orphelines vers cette session
                    cursor.execute('''
                        UPDATE session_frames
                        SET session_id = ?
                        WHERE (session_id IS NULL OR session_id = 0 OR session_id = ?) AND client_session_id = ?
                    ''', (session_id, client_sid, client_sid))
                    conn.commit()

                # Recharger les frames après mappage
                cursor.execute('''
                    SELECT frame_data, timestamp, prediction, confidence, frame_number
                    FROM session_frames 
                    WHERE session_id = ? 
                    ORDER BY frame_number ASC
                ''', (session_id,))
                frames = cursor.fetchall()

                # Fallback ultime: retourner les frames trouvées uniquement via client_session_id égal à l'ID demandé
                if not frames:
                    cursor.execute('''
                        SELECT frame_data, timestamp, prediction, confidence, frame_number
                        FROM session_frames 
                        WHERE client_session_id = ? 
                        ORDER BY frame_number ASC
                    ''', (session_id,))
                    frames = cursor.fetchall()

                conn.close()
            except Exception as e:
                print(f"⚠️ get_session_frames: mappage automatique échoué: {e}")
        
        # Convertir en format JSON-friendly
        frames_list = []
        for frame in frames:
            frames_list.append({
                'frame_data': frame[0],  # base64 image
                'timestamp': frame[1],   # timestamp
                'prediction': frame[2],  # prediction
                'confidence': frame[3],  # confidence
                'frame_number': frame[4] # frame number
            })
        
        return jsonify({
            'frames': frames_list,
            'success': True,
            'session_id': session_id
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Erreur lors de la récupération des frames: {str(e)}',
            'success': False
        }), 500


@app.route('/save_frame', methods=['POST'])
@require_auth
def save_frame():
    """Sauvegarder une frame vidéo"""
    try:
        data = request.get_json()
        # Log brut pour debug en cas d'erreur (n'affiche pas de secrets)
        try:
            print(f"/save_frame payload keys: {list(data.keys()) if isinstance(data, dict) else 'non-dict'}")
        except Exception:
            print("/save_frame: impossible d'afficher les clés de la payload")

        # Accept both snake_case and camelCase from clients to be tolerant
        def pick(d, *names):
            for n in names:
                if isinstance(d, dict) and n in d:
                    return d[n]
            return None

        # Validation des données: accepter frame_data|frameData, timestamp, prediction, confidence, frame_number|frameNumber
        required_fields = [
            (('frame_data', 'frameData'), 'frame_data'),
            (('timestamp',), 'timestamp'),
            (('prediction',), 'prediction'),
            (('confidence',), 'confidence'),
            (('frame_number', 'frameNumber'), 'frame_number')
        ]

        normalized = {}
        missing = []
        for names, out_key in required_fields:
            val = None
            for n in names:
                if isinstance(data, dict) and n in data:
                    val = data[n]
                    break
            if val is None:
                missing.append(out_key)
            else:
                normalized[out_key] = val

        # session_id can be provided as session_id or sessionId
        session_id = pick(data, 'session_id', 'sessionId')
        client_session_id = pick(data, 'client_session_id', 'clientSessionId')

        if missing:
            return jsonify({
                'error': f'Champ(s) manquant(s): {", ".join(missing)}',
                'received_keys': list(data.keys()) if isinstance(data, dict) else None,
                'success': False
            }), 400

        if not session_id and not client_session_id:
            return jsonify({
                'error': 'session_id ou client_session_id requis',
                'received_keys': list(data.keys()) if isinstance(data, dict) else None,
                'success': False
            }), 400

        frame_data = {
            'session_id': session_id,
            'user_id': request.current_user['id'],
            'client_session_id': client_session_id,
            'frame_data': normalized['frame_data'],
            'timestamp': normalized['timestamp'],
            'prediction': normalized['prediction'],
            'confidence': normalized['confidence'],
            'frame_number': normalized['frame_number']
        }

        db = SessionDatabase()
        # Résoudre immédiatement l'ID de session si possible via client_session_id
        resolved_session_id = frame_data['session_id']
        if not resolved_session_id and frame_data['client_session_id']:
            try:
                conn = sqlite3.connect(db.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM sessions WHERE client_session_id = ? ORDER BY id DESC LIMIT 1', (frame_data['client_session_id'],))
                row = cursor.fetchone()
                conn.close()
                if row:
                    resolved_session_id = row[0]
            except Exception as e:
                print(f"⚠️ Résolution session immédiate échouée: {e}")

        db.insert_frame(
            resolved_session_id,
            frame_data['frame_data'],
            frame_data['timestamp'],
            frame_data['prediction'],
            frame_data['confidence'],
            frame_data['frame_number'],
            client_session_id=frame_data['client_session_id'],
            user_id=frame_data['user_id']
        )
        
        return jsonify({
            'message': 'Frame enregistrée avec succès',
            'success': True
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Erreur lors de la sauvegarde de la frame: {str(e)}',
            'success': False
        }), 500


@app.route('/performance', methods=['GET'])
def performance_metrics():
    """Métriques de performance de l'API"""
    try:
        detector = init_detector()
        
        # Statistiques du cache
        cache_stats = {
            'size': len(prediction_cache),
            'max_size': CACHE_SIZE,
            'hit_rate': 0.0,  # À calculer si on garde des stats
            'memory_usage_mb': len(prediction_cache) * 0.1  # Estimation
        }
        
        # Informations sur le modèle
        model_info = {
            'device': str(detector.device),
            'torchscript_optimized': hasattr(detector.model, '_get_methods'),
            'mixed_precision': hasattr(detector, 'scaler'),
            'cuda_available': torch.cuda.is_available(),
            'model_parameters': sum(p.numel() for p in detector.model.parameters()) if hasattr(detector.model, 'parameters') else 0
        }
        
        # Statistiques système
        try:
            import psutil
            system_stats = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            }
        except ImportError:
            # Fallback si psutil n'est pas disponible
            system_stats = {
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'note': 'psutil non disponible - métriques système simulées'
            }
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'cache': cache_stats,
            'model': model_info,
            'system': system_stats
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Erreur lors de la récupération des métriques: {str(e)}',
            'success': False
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Vérifier l'état de l'API"""
    try:
        detector = init_detector()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'device': str(detector.device),
            'model_loaded': os.path.exists('cnn_drowsiness (1).pth'),
            'landmarks_available': detector.use_landmarks,
            'dlib_available': DLIB_AVAILABLE,
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }), 500


@app.route('/model_info', methods=['GET'])
def model_info():
    """Informations sur le modèle"""
    try:
        detector = init_detector()
        
        model_stats = {
            'architecture': 'CNN Custom',
            'input_size': '128x128x3',
            'classes': detector.classes,
            'device': str(detector.device),
            'buffer_size': detector.prediction_buffer.maxlen,
            'current_buffer': len(detector.prediction_buffer)
        }
        
        if hasattr(detector.model, 'parameters'):
            total_params = sum(p.numel() for p in detector.model.parameters())
            trainable_params = sum(p.numel() for p in detector.model.parameters() if p.requires_grad)
            model_stats.update({
                'total_parameters': total_params,
                'trainable_parameters': trainable_params
            })
        
        return jsonify({
            'success': True,
            'model_info': model_stats
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Erreur lors de la récupération des infos: {str(e)}',
            'success': False
        }), 500


@app.route('/face_detection_test', methods=['POST'])
def face_detection_test():
    """Tester la détection faciale sur une image"""
    try:
        detector = init_detector()
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({
                'error': 'Image manquante dans la requête',
                'success': False
            }), 400
        
        # Test de détection faciale
        image_data = data['image']
        if 'base64,' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image_pil = Image.open(io.BytesIO(image_bytes))
        
        # Test MTCNN
        mtcnn_result = None
        if detector.use_face_detection and detector.detector_face:
            try:
                face = detector.detector_face(image_pil)
                mtcnn_result = {
                    'detected': face is not None,
                    'shape': str(face.shape) if face is not None else None
                }
            except Exception as e:
                mtcnn_result = {'error': str(e)}
        
        # Test OpenCV fallback
        opencv_result = None
        try:
            import cv2
            import numpy as np
            
            img_array = np.array(image_pil)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=3, 
                minSize=(30, 30)
            )
            
            opencv_result = {
                'detected': len(faces) > 0,
                'count': len(faces),
                'faces': faces.tolist() if len(faces) > 0 else []
            }
        except Exception as e:
            opencv_result = {'error': str(e)}
        
        return jsonify({
            'success': True,
            'image_size': image_pil.size,
            'mtcnn': mtcnn_result,
            'opencv': opencv_result,
            'face_detection_enabled': detector.use_face_detection
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Erreur lors du test: {str(e)}',
            'success': False
        }), 500


# Gestion des erreurs
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint non trouvé',
        'success': False,
        'available_endpoints': [
            'GET /',
            'POST /predict',
            'POST /save_session',
            'GET /get_sessions',
            'DELETE /delete_session/<id>',
            'DELETE /clear_sessions',
            'GET /get_session_frames/<id>',
            'POST /save_frame',
            'GET /health',
            'GET /model_info'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Erreur interne du serveur',
        'success': False
    }), 500


# Point d'entrée principal
if __name__ == '__main__':
    # Créer les dossiers nécessaires
    os.makedirs('models', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    # Configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Démarrage de l'API sur le port {port}")
    print(f"📱 Interface frontend disponible à: http://localhost:{port}")
    print(f"💡 PyTorch disponible: {torch.__version__}")
    print(f"🔍 CUDA disponible: {torch.cuda.is_available()}")
    
    # Initialiser le détecteur
    detector = init_detector()
    print(f"💡 Device utilisé: {detector.device}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )