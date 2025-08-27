import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration de base"""
    
    # Configuration SQLite pour la base de données locale
    LOCAL_DB_PATH = os.environ.get('LOCAL_DB_PATH', 'sessions.db')  # Fichier DB SQLite local
    MAX_SESSIONS_STORED = int(os.environ.get('MAX_SESSIONS_STORED', 100))  # Limite du nombre de sessions sauvegardées

    # Autres configurations de base
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Configuration de l'IA
    MODEL_PATH = os.environ.get('MODEL_PATH', 'cnn_drowsiness (1).pth')
    
    # Configuration du cache
    CACHE_ENABLED = os.environ.get('CACHE_ENABLED', 'True').lower() == 'true'
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', 30))
    
    # Configuration des logs
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')

class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    DEBUG = True
    LOCAL_DB_PATH = 'test_sessions.db'

# Dictionnaire des configurations
config = {
    'development': DevelopmentConfig(),
    'production': ProductionConfig(),
    'testing': TestingConfig(),
    'default': DevelopmentConfig()
}

def get_config():
    """Retourne la configuration selon l'environnement"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
