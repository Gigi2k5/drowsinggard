# 🚨 DrowsingGard - Détection de Somnolence en Temps Réel

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.5+-green.svg)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1+-red.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**DrowsingGard** est une application de détection de somnolence en temps réel utilisant l'intelligence artificielle pour analyser les expressions faciales via webcam et détecter les signes de fatigue. L'application est conçue pour améliorer la sécurité routière, la productivité au travail et la surveillance médicale.

## ✨ Fonctionnalités Principales

### 🔍 Détection IA Avancée
- **Analyse en temps réel** des expressions faciales via webcam
- **Modèle PyTorch** optimisé pour la détection de somnolence
- **Détection des landmarks** faciaux avec dlib (optionnel)
- **Cache intelligent** pour optimiser les performances

### 📊 Surveillance et Statistiques
- **Métriques en temps réel** : taux d'éveil, somnolence, alertes
- **Historique des sessions** avec enregistrement vidéo
- **Statistiques détaillées** : durée, confiance, latence
- **Export des données** et vidéos (format WebM)

### 🔐 Système d'Authentification
- **Gestion des utilisateurs** avec rôles (admin/utilisateur)
- **Sécurité renforcée** : hachage SHA-256, tokens JWT
- **Contrôle d'accès** basé sur les rôles
- **Panneau d'administration** pour la gestion des comptes

### 🎥 Enregistrement et Lecture
- **Capture automatique** des frames pendant la surveillance
- **Stockage en base de données** SQLite
- **Lecteur vidéo intégré** avec contrôles avancés
- **Export des sessions** en format vidéo et données

## 🏗️ Architecture

```
DrowsingGard/
├── frontend/                 # Interface Vue.js 3
│   ├── src/
│   │   ├── components/      # Composants Vue
│   │   ├── services/        # Services API
│   │   └── App.vue         # Composant principal
│   ├── package.json
│   └── vite.config.js
├── backend/                  # API Flask
│   ├── app1.py             # Application principale
│   ├── models/             # Modèles IA
│   ├── requirements.txt    # Dépendances Python
│   └── sessions.db        # Base de données SQLite
└── README.md
```

### Technologies Utilisées

#### Backend
- **Flask 3.1+** : Framework web Python
- **PyTorch 2.2+** : Deep learning et modèles IA
- **OpenCV 4.8+** : Traitement d'images
- **SQLite3** : Base de données légère
- **dlib** : Détection des landmarks faciaux

#### Frontend
- **Vue.js 3.5+** : Framework JavaScript progressif
- **Vite** : Build tool moderne
- **Composition API** : Architecture Vue.js moderne

## 🚀 Installation

### Prérequis
- **Python 3.10+**
- **Node.js 18+**
- **Webcam** fonctionnelle
- **Git**

### 1. Cloner le Repository
```bash
git clone https://github.com/votre-username/drowsinggard.git
cd drowsinggard
```

### 2. Configuration du Backend

#### Installation des Dépendances Python
```bash
cd backend
pip install -r requirements.txt
```

#### Installation de dlib (Optionnel)
```bash
# Windows
pip install dlib-19.22.99-cp310-cp310-win_amd64.whl

# Linux/Mac
pip install dlib
```

#### Initialisation de la Base de Données
```bash
python init_db.py
```

#### Lancement du Serveur
```bash
python app1.py
```

Le serveur sera accessible sur `http://localhost:5000`

### 3. Configuration du Frontend

#### Installation des Dépendances Node.js
```bash
cd frontend
npm install
```

#### Lancement en Mode Développement
```bash
npm run dev
```

L'application sera accessible sur `http://localhost:5173`

## 📖 Utilisation

### 1. Première Connexion
- **Compte Admin** : `admin` / `admin123`
- **Compte Utilisateur** : `user` / `user123`

### 2. Surveillance en Temps Réel
1. **Se connecter** avec un compte utilisateur
2. **Autoriser l'accès** à la webcam
3. **Démarrer la surveillance** avec le bouton "Démarrer"
4. **Observer les métriques** en temps réel
5. **Arrêter la session** quand nécessaire

### 3. Consultation de l'Historique
- **Accéder à l'onglet** "Historique"
- **Consulter les sessions** passées
- **Lire les vidéos** enregistrées
- **Exporter les données** (admin uniquement)

### 4. Administration (Admin uniquement)
- **Gérer les utilisateurs** : création, suppression
- **Consulter les sessions** de tous les utilisateurs
- **Exporter les données** et vidéos
- **Surveiller l'activité** globale

## 🔧 Configuration

### Variables d'Environnement
```bash
# Backend
export SECRET_KEY="votre-clé-secrète"
export FLASK_ENV="development"
export FLASK_DEBUG=1

# Frontend
export VITE_API_URL="http://localhost:5000"
```

### Paramètres de l'IA
```python
# backend/app1.py
CONFIDENCE_THRESHOLD = 0.6      # Seuil de confiance
FRAME_CAPTURE_INTERVAL = 0.5    # Intervalle de capture (secondes)
CACHE_SIZE = 100                # Taille du cache des prédictions
```

## 📊 API Endpoints

### Authentification
- `POST /auth/register` - Inscription utilisateur
- `POST /auth/login` - Connexion
- `GET /auth/profile` - Profil utilisateur

### Sessions
- `POST /save_session` - Sauvegarder une session
- `GET /get_sessions` - Récupérer les sessions
- `DELETE /delete_session/<id>` - Supprimer une session

### Frames
- `POST /save_frame` - Sauvegarder une frame
- `GET /get_session_frames/<id>` - Récupérer les frames d'une session

### Administration
- `GET /admin/users` - Liste des utilisateurs
- `DELETE /admin/users/<id>` - Supprimer un utilisateur
- `GET /admin/users/<id>/sessions` - Sessions d'un utilisateur

### Système
- `GET /health` - État du serveur
- `GET /performance` - Métriques de performance

## 🧪 Tests

### Tests Backend
```bash
cd backend
python test_auth.py      # Tests d'authentification
python test_db.py        # Tests de base de données
python test_session.py   # Tests des sessions
python test_frame.py     # Tests des frames
```

### Tests Frontend
```bash
cd frontend
npm run build           # Build de production
npm run preview         # Prévisualisation du build
```

## 🚨 Dépannage

### Problèmes Courants

#### Webcam non détectée
- Vérifier les permissions du navigateur
- Redémarrer l'application
- Vérifier qu'aucune autre application n'utilise la webcam

#### Erreurs de Modèle IA
- Vérifier que `mobilenet_drowsiness.pth` est présent
- Redémarrer le serveur backend
- Vérifier la version de PyTorch

#### Problèmes de Base de Données
- Supprimer `sessions.db` et relancer `init_db.py`
- Vérifier les permissions d'écriture
- Vérifier l'espace disque disponible

### Logs et Debug
```bash
# Backend
export FLASK_DEBUG=1
python app1.py

# Frontend
npm run dev -- --debug
```

## 📈 Performance

### Optimisations Actuelles
- **Cache LRU** pour les prédictions
- **Compression des images** avant stockage
- **Requêtes SQL optimisées** avec index
- **Lazy loading** des composants Vue

### Métriques Typiques
- **Latence de prédiction** : 50-150ms
- **Utilisation mémoire** : 200-500MB
- **Utilisation CPU** : 20-40%
- **FPS de capture** : 2-5 FPS

## 🔒 Sécurité

### Mesures Implémentées
- **Hachage des mots de passe** (SHA-256)
- **Tokens JWT** avec expiration
- **Validation des entrées** côté serveur
- **CORS configuré** pour le développement
- **Isolation des données** par utilisateur

### Recommandations Production
- **Changer la SECRET_KEY** par défaut
- **Utiliser HTTPS** en production
- **Limiter les tentatives de connexion**
- **Auditer régulièrement** les logs
- **Sauvegarder** la base de données

## 🤝 Contribution

### Comment Contribuer
1. **Fork** le projet
2. **Créer une branche** pour votre fonctionnalité
3. **Commiter** vos changements
4. **Pousser** vers la branche
5. **Ouvrir une Pull Request**

### Standards de Code
- **Python** : PEP 8, docstrings
- **JavaScript** : ESLint, Prettier
- **Vue.js** : Composition API, TypeScript (optionnel)
- **Tests** : Pytest pour Python, Jest pour JavaScript

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- **PyTorch** pour le framework de deep learning
- **OpenCV** pour le traitement d'images
- **Vue.js** pour le framework frontend
- **Flask** pour le framework backend
- **dlib** pour la détection des landmarks faciaux

## 📞 Support

### Contact
- **Issues** : [GitHub Issues](https://github.com/votre-username/drowsinggard/issues)
- **Discussions** : [GitHub Discussions](https://github.com/votre-username/drowsinggard/discussions)
- **Wiki** : [Documentation détaillée](https://github.com/votre-username/drowsinggard/wiki)

### Documentation
- **API Reference** : [docs/API.md](docs/API.md)
- **User Guide** : [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
- **Developer Guide** : [docs/DEVELOPER.md](docs/DEVELOPER.md)

---

**DrowsingGard** - Votre gardien contre la somnolence 🚨

*Développé avec ❤️ pour la sécurité et la productivité*
