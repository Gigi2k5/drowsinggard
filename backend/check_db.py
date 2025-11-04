"""
Script pour vérifier le contenu de la base de données
"""
import sqlite3

DB_PATH = 'sessions.db'

def check_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("📊 VÉRIFICATION DE LA BASE DE DONNÉES")
    print("=" * 60)
    print()
    
    # 1. Structure de la table sessions
    print("📋 Structure de la table sessions:")
    cursor.execute("PRAGMA table_info(sessions)")
    for col in cursor.fetchall():
        print(f"  {col[1]}: {col[2]}")
    print()
    
    # 2. Structure de la table session_frames
    print("📋 Structure de la table session_frames:")
    cursor.execute("PRAGMA table_info(session_frames)")
    for col in cursor.fetchall():
        print(f"  {col[1]}: {col[2]}")
    print()
    
    # 3. Compter les sessions
    cursor.execute("SELECT COUNT(*) FROM sessions")
    session_count = cursor.fetchone()[0]
    print(f"📈 Nombre de sessions: {session_count}")
    print()
    
    # 4. Compter les frames
    cursor.execute("SELECT COUNT(*) FROM session_frames")
    frame_count = cursor.fetchone()[0]
    print(f"📈 Nombre total de frames: {frame_count}")
    print()
    
    # 5. Détails de la session 17
    print("🔍 Détails de la session 17:")
    cursor.execute("SELECT * FROM sessions WHERE id = 17")
    session = cursor.fetchone()
    if session:
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [col[1] for col in cursor.fetchall()]
        for i, col_name in enumerate(columns):
            print(f"  {col_name}: {session[i]}")
    else:
        print("  ❌ Session 17 non trouvée")
    print()
    
    # 6. Frames de la session 17
    print("🎬 Frames de la session 17:")
    cursor.execute("""
        SELECT id, session_id, client_session_id, timestamp, prediction, confidence, frame_number
        FROM session_frames 
        WHERE session_id = 17
        LIMIT 5
    """)
    frames = cursor.fetchall()
    print(f"  📊 Trouvées avec session_id = 17: {len(frames)}")
    for frame in frames:
        print(f"    - Frame {frame[0]}: session_id={frame[1]}, client_session_id={frame[2]}, frame_number={frame[6]}")
    print()
    
    # 7. Frames avec client_session_id qui pourrait correspondre
    if session:
        client_sid = session[columns.index('client_session_id')]
        print(f"🔍 client_session_id de la session 17: {client_sid} (type: {type(client_sid)})")
        
        # Essayer de trouver des frames avec ce client_session_id
        cursor.execute("""
            SELECT id, session_id, client_session_id, timestamp, prediction, confidence, frame_number
            FROM session_frames 
            WHERE client_session_id = ?
            LIMIT 5
        """, (client_sid,))
        frames_by_client = cursor.fetchall()
        print(f"  📊 Trouvées avec client_session_id = {client_sid}: {len(frames_by_client)}")
        for frame in frames_by_client:
            print(f"    - Frame {frame[0]}: session_id={frame[1]}, client_session_id={frame[2]}, frame_number={frame[6]}")
        print()
    
    # 8. Frames orphelines (sans session_id ou session_id = 0)
    print("🔍 Frames orphelines:")
    cursor.execute("""
        SELECT id, session_id, client_session_id, timestamp, prediction, confidence, frame_number
        FROM session_frames 
        WHERE session_id IS NULL OR session_id = 0
        LIMIT 10
    """)
    orphan_frames = cursor.fetchall()
    print(f"  📊 Total frames orphelines: {len(orphan_frames)}")
    for frame in orphan_frames[:5]:
        print(f"    - Frame {frame[0]}: session_id={frame[1]}, client_session_id={frame[2]} (type: {type(frame[2])}), frame_number={frame[6]}")
    print()
    
    # 9. Distribution des client_session_id
    print("📊 Distribution des client_session_id dans session_frames:")
    cursor.execute("""
        SELECT client_session_id, COUNT(*) as count
        FROM session_frames
        GROUP BY client_session_id
        ORDER BY count DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"  client_session_id={row[0]} (type: {type(row[0])}): {row[1]} frames")
    
    conn.close()

if __name__ == '__main__':
    check_database()
