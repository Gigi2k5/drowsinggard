from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import datetime

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    """Vérifier l'état de l'API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'device': 'cpu',
        'model_loaded': False,
        'numpy_available': True,
        'version': '1.0.0-simple'
    })

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint pour prédire l'état de somnolence (simulation)"""
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({
                'error': 'Image manquante dans la requête',
                'success': False
            }), 400
        
        # Simulation de prédiction (sans PyTorch)
        import random
        is_drowsy = random.random() < 0.3  # 30% de chance d'être somnolent
        confidence = random.uniform(70, 95)
        
        result = {
            'prediction': 'drowsy' if is_drowsy else 'awake',
            'confidence': round(confidence, 2),
            'success': True,
            'timestamp': datetime.datetime.now().isoformat(),
            'device': 'cpu',
            'note': 'Simulation (PyTorch non disponible)'
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': f'Erreur lors de la prédiction: {str(e)}',
            'success': False,
            'timestamp': datetime.datetime.now().isoformat()
        }), 500

@app.route('/save_session', methods=['POST'])
def save_session():
    """Sauvegarder une session (simulation)"""
    try:
        data = request.get_json()
        return jsonify({
            'message': 'Session enregistrée avec succès (simulation)',
            'success': True
        }), 200
    except Exception as e:
        return jsonify({
            'error': f'Erreur lors de la sauvegarde: {str(e)}',
            'success': False
        }), 500

@app.route('/get_sessions', methods=['GET'])
def get_sessions():
    """Récupérer les sessions (simulation)"""
    return jsonify({
        'sessions': [],
        'success': True
    }), 200

if __name__ == '__main__':
    print("🚀 Démarrage de l'API Flask simplifiée")
    print("📱 Interface frontend disponible à: http://localhost:5000")
    print("💡 Numpy disponible:", np.__version__)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
