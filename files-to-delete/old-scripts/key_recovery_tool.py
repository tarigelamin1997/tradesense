
#!/usr/bin/env python3
"""
Key Recovery Tool - Find your TradeSense encryption keys
"""

import os
import sqlite3
import base64
from credential_manager import CredentialManager

def find_encryption_keys():
    """Find all available encryption keys."""
    print("🔍 TradeSense Key Recovery Tool")
    print("=" * 50)
    
    # Check environment variable
    env_key = os.environ.get('TRADESENSE_MASTER_KEY')
    if env_key:
        print("✅ Environment Key Found:")
        print(f"   Key: {env_key}")
        print(f"   Source: Environment variable (TRADESENSE_MASTER_KEY)")
    else:
        print("❌ No environment key found")
    
    print()
    
    # Check database backup
    try:
        conn = sqlite3.connect("tradesense.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT encrypted_key, created_at FROM encryption_keys 
            WHERE key_id = ? AND is_active = TRUE
        ''', ('master_backup',))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            obfuscated_key = result[0]
            created_at = result[1]
            # Deobfuscate the stored key
            backup_key = base64.b64decode(obfuscated_key).decode()
            
            print("✅ Backup Key Found:")
            print(f"   Key: {backup_key}")
            print(f"   Source: Database backup")
            print(f"   Created: {created_at}")
        else:
            print("❌ No backup key found in database")
            
    except Exception as e:
        print(f"❌ Error accessing database: {str(e)}")
    
    print()
    
    # Test key validation
    try:
        credential_manager = CredentialManager()
        status = credential_manager.validate_encryption_key()
        
        print("🔐 Key Validation Status:")
        print(f"   Valid: {'✅' if status['is_valid'] else '❌'}")
        print(f"   Has Environment Key: {'✅' if status['has_env_key'] else '❌'}")
        print(f"   Has Backup Key: {'✅' if status['has_backup'] else '❌'}")
        
        if status['error']:
            print(f"   Error: {status['error']}")
            
    except Exception as e:
        print(f"❌ Error validating keys: {str(e)}")
    
    print()
    print("📋 Next Steps:")
    if env_key:
        print("   • Your environment key is working correctly")
        print("   • No action needed")
    else:
        if result:
            backup_key = base64.b64decode(result[0]).decode()
            print("   • Add the backup key to Replit Secrets:")
            print("   • 1. Click the 🔒 Secrets tool in Replit sidebar")
            print("   • 2. Click '+ New Secret'")
            print("   • 3. Key: TRADESENSE_MASTER_KEY")
            print(f"   • 4. Value: {backup_key}")
            print("   • 5. Click 'Add Secret'")
        else:
            print("   • No keys found - a new key will be generated on next startup")
            print("   • Make sure to save it to Replit Secrets when prompted")

if __name__ == "__main__":
    find_encryption_keys()
