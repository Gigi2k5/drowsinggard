#!/usr/bin/env python3
"""Script de test pour vérifier la base de données"""

import sqlite3
import os

def test_database():
    """Tester la base de données"""
    db_path = 'sessions.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données {db_path} n'existe pas")
        return False
    
    print(f"✅ Base de données {db_path} existe")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier la table users
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            print("✅ Table 'users' existe")
            
            # Vérifier la structure
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            print(f"📋 Colonnes de la table 'users':")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Vérifier les utilisateurs existants
            cursor.execute("SELECT id, username, email, role FROM users")
            users = cursor.fetchall()
            print(f"👥 Utilisateurs existants: {len(users)}")
            for user in users:
                print(f"  - ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Role: {user[3]}")
        else:
            print("❌ Table 'users' n'existe pas")
        
        # Vérifier la table sessions
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
        if cursor.fetchone():
            print("✅ Table 'sessions' existe")
            
            # Vérifier la structure
            cursor.execute("PRAGMA table_info(sessions)")
            columns = cursor.fetchall()
            print(f"📋 Colonnes de la table 'sessions':")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print("❌ Table 'sessions' n'existe pas")
        
        # Vérifier la table session_frames
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_frames'")
        if cursor.fetchone():
            print("✅ Table 'session_frames' existe")
            
            # Vérifier la structure
            cursor.execute("PRAGMA table_info(session_frames)")
            columns = cursor.fetchall()
            print(f"📋 Colonnes de la table 'session_frames':")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print("❌ Table 'session_frames' n'existe pas")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Test de la base de données...")
    test_database()
