"""
Script de migration pour corriger le type de la colonne client_session_id
De INTEGER vers TEXT pour supporter les UUIDs
"""
import sqlite3
import os

DB_PATH = 'sessions.db'

def migrate_database():
    """Migrer la colonne client_session_id de INTEGER vers TEXT"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de données {DB_PATH} non trouvée")
        return
    
    print(f"🔧 Migration de la base de données {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 0. Nettoyage des tables temporaires si elles existent
        print("🧹 Nettoyage des tables temporaires...")
        try:
            cursor.execute('DROP TABLE IF EXISTS session_frames_new')
            cursor.execute('DROP TABLE IF EXISTS sessions_new')
            conn.commit()
        except Exception as e:
            print(f"⚠️ Nettoyage: {e}")
        
        # 1. Créer une nouvelle table temporaire avec le bon schéma
        print("📝 Création de la table temporaire...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_frames_new (
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
        
        # 2. Copier les données de l'ancienne table vers la nouvelle
        print("📋 Copie des données...")
        cursor.execute('''
            INSERT INTO session_frames_new 
                (id, session_id, user_id, client_session_id, frame_data, timestamp, prediction, confidence, frame_number)
            SELECT 
                id, 
                session_id, 
                user_id, 
                CAST(client_session_id AS TEXT), 
                frame_data, 
                timestamp, 
                prediction, 
                confidence, 
                frame_number
            FROM session_frames
        ''')
        
        # 3. Supprimer l'ancienne table
        print("🗑️ Suppression de l'ancienne table...")
        cursor.execute('DROP TABLE session_frames')
        
        # 4. Renommer la nouvelle table
        print("✏️ Renommage de la nouvelle table...")
        cursor.execute('ALTER TABLE session_frames_new RENAME TO session_frames')
        
        # 5. Créer un index sur client_session_id pour améliorer les performances
        print("🔍 Création d'index...")
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_client_session_id 
            ON session_frames(client_session_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_session_id 
            ON session_frames(session_id)
        ''')
        
        conn.commit()
        print("✅ Migration réussie !")
        
        # 6. Vérifier le schéma
        cursor.execute("PRAGMA table_info(session_frames)")
        columns = cursor.fetchall()
        print("\n📊 Nouveau schéma de la table session_frames:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # 7. Compter les frames
        cursor.execute("SELECT COUNT(*) FROM session_frames")
        count = cursor.fetchone()[0]
        print(f"\n📈 Total de frames: {count}")
        
        # 8. Migrer aussi la table sessions si nécessaire
        print("\n🔧 Vérification de la table sessions...")
        cursor.execute("PRAGMA table_info(sessions)")
        sessions_columns = cursor.fetchall()
        
        has_client_session_id = any(col[1] == 'client_session_id' for col in sessions_columns)
        client_session_id_type = None
        
        for col in sessions_columns:
            if col[1] == 'client_session_id':
                client_session_id_type = col[2]
                break
        
        if has_client_session_id and client_session_id_type != 'TEXT':
            print(f"⚠️ La colonne client_session_id dans sessions est de type {client_session_id_type}, migration...")
            
            # Obtenir la liste des colonnes existantes avec leurs types
            cursor.execute("PRAGMA table_info(sessions)")
            existing_columns_info = cursor.fetchall()
            print(f"📋 Colonnes existantes dans sessions: {[col[1] for col in existing_columns_info]}")
            
            # Construire la liste des colonnes pour la nouvelle table
            column_definitions = []
            column_names = []
            
            for col_info in existing_columns_info:
                col_name = col_info[1]
                col_type = col_info[2]
                col_notnull = col_info[3]
                col_default = col_info[4]
                col_pk = col_info[5]
                
                column_names.append(col_name)
                
                # Construction de la définition de colonne
                if col_pk:
                    column_definitions.append(f'{col_name} {col_type} PRIMARY KEY AUTOINCREMENT')
                elif col_name == 'client_session_id':
                    # Changement de type pour cette colonne
                    column_definitions.append(f'{col_name} TEXT')
                else:
                    col_def = f'{col_name} {col_type}'
                    if col_notnull:
                        col_def += ' NOT NULL'
                    if col_default is not None:
                        col_def += f' DEFAULT {col_default}'
                    column_definitions.append(col_def)
            
            # Créer nouvelle table sessions
            create_sql = f'''
                CREATE TABLE sessions_new (
                    {', '.join(column_definitions)}
                )
            '''
            print(f"📝 SQL création: {create_sql}")
            cursor.execute(create_sql)
            
            # Construire la requête SELECT dynamiquement
            select_columns = []
            for col in column_names:
                if col == 'client_session_id':
                    select_columns.append('CAST(client_session_id AS TEXT)')
                else:
                    select_columns.append(col)
            
            # Copier les données
            insert_sql = f'''
                INSERT INTO sessions_new ({', '.join(column_names)})
                SELECT {', '.join(select_columns)}
                FROM sessions
            '''
            cursor.execute(insert_sql)
            
            # Remplacer la table
            cursor.execute('DROP TABLE sessions')
            cursor.execute('ALTER TABLE sessions_new RENAME TO sessions')
            
            # Index
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_client_session_id 
                ON sessions(client_session_id)
            ''')
            
            conn.commit()
            print("✅ Table sessions migrée !")
        else:
            print("✅ Table sessions déjà correcte")
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("🔧 MIGRATION DE LA BASE DE DONNÉES")
    print("=" * 60)
    print()
    
    response = input("⚠️  Cette opération va modifier la structure de la base de données.\nContinuer ? (oui/non): ")
    
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        migrate_database()
    else:
        print("❌ Migration annulée")
