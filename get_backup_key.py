
#!/usr/bin/env python3
"""
Utility script to retrieve the backup encryption key from the database.
Run this to get the key value to add to Replit Secrets.
"""

import sqlite3
import base64
import os

def get_backup_key():
    """Retrieve the backup encryption key from the database."""
    db_path = "tradesense.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found. No backup key available.")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT encrypted_key FROM encryption_keys 
            WHERE key_id = ? AND is_active = TRUE
        ''', ('master_backup',))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Deobfuscate the stored key
            obfuscated_key = result[0]
            backup_key = base64.b64decode(obfuscated_key).decode()
            return backup_key
        else:
            print("❌ No backup key found in database.")
            return None
            
    except Exception as e:
        print(f"❌ Error retrieving backup key: {str(e)}")
        return None

if __name__ == "__main__":
    print("🔍 Retrieving backup encryption key...")
    print("=" * 50)
    
    backup_key = get_backup_key()
    
    if backup_key:
        print("✅ Backup key found!")
        print("📋 Copy this key value:")
        print("=" * 50)
        print(backup_key)
        print("=" * 50)
        print()
        print("📝 Instructions:")
        print("1. Copy the key value above")
        print("2. Go to Replit Secrets (🔒 icon in sidebar)")
        print("3. Click '+ New Secret'")
        print("4. Key: TRADESENSE_MASTER_KEY")
        print("5. Value: (paste the key above)")
        print("6. Click 'Add Secret'")
        print()
        print("✅ Once added, the 'Restored encryption key from backup' message will stop appearing.")
    else:
        print("❌ No backup key available.")
        print("💡 The system will generate a new key when you restart the app.")
