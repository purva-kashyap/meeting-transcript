#!/usr/bin/env python3
"""
Session Cookie Test Script
Run this to verify your session cookie configuration is correct
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_app_config():
    """Check if app.py has the correct session configuration"""
    print_header("1. Checking app.py Configuration")
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        checks = {
            'SESSION_COOKIE_SAMESITE': 'SESSION_COOKIE_SAMESITE' in content,
            'SESSION_COOKIE_SECURE': 'SESSION_COOKIE_SECURE' in content,
            'SESSION_COOKIE_HTTPONLY': 'SESSION_COOKIE_HTTPONLY' in content,
            'BYPASS_STATE_CHECK': 'BYPASS_STATE_CHECK' in content,
        }
        
        all_good = True
        for key, found in checks.items():
            status = "✓" if found else "✗"
            print(f"{status} {key}: {'Found' if found else 'NOT FOUND'}")
            if not found:
                all_good = False
        
        return all_good
    
    except FileNotFoundError:
        print("✗ app.py not found!")
        return False

def check_env_settings():
    """Check .env settings"""
    print_header("2. Checking .env Settings")
    
    bypass = os.getenv('BYPASS_STATE_CHECK', 'false').lower()
    
    if bypass == 'true':
        print("⚠️  WARNING: BYPASS_STATE_CHECK is enabled!")
        print("   This disables CSRF protection - only use for debugging!")
        print("   Set BYPASS_STATE_CHECK=false after fixing session cookies")
    else:
        print("✓ BYPASS_STATE_CHECK is disabled (secure)")
    
    session_type = os.getenv('SESSION_TYPE', 'filesystem')
    print(f"✓ SESSION_TYPE: {session_type}")
    
    return True

def check_session_files():
    """Check session file directory"""
    print_header("3. Checking Session Files")
    
    if os.path.exists('flask_session'):
        files = os.listdir('flask_session')
        file_count = len([f for f in files if not f.startswith('.')])
        print(f"ℹ  Found {file_count} session file(s)")
        
        if file_count > 5:
            print(f"⚠  You have many old sessions. Consider clearing them:")
            print(f"   rm -rf flask_session/*")
    else:
        print("ℹ  No flask_session directory yet (will be created on first run)")
    
    return True

def print_instructions():
    """Print testing instructions"""
    print_header("Testing Instructions")
    
    print("""
To test if session cookies work:

1. Start your Flask app:
   python app.py

2. Open browser (Chrome recommended) and go to:
   http://localhost:5000  (or your configured URL)

3. Open DevTools (F12) → Application → Cookies

4. Look for cookie named 'flask_session' with these settings:
   - Name: flask_session
   - SameSite: Lax
   - Secure: (empty/unchecked for localhost)
   - HttpOnly: ✓

5. Click "Post to Teams" to trigger OAuth login

6. Check terminal output for:
   DEBUG /auth/login: Generated state: [uuid]
   DEBUG: Received state: [uuid]
   DEBUG: Session state: [uuid]  ← Should match!

If session state is None → Session cookie was lost
If states match → Everything works! ✓
""")

def main():
    print("\n" + "="*60)
    print("  SESSION COOKIE CONFIGURATION TEST")
    print("="*60)
    
    results = {
        'app_config': check_app_config(),
        'env_settings': check_env_settings(),
        'session_files': check_session_files(),
    }
    
    print_header("Summary")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("✓ Configuration looks good!")
    else:
        print("✗ Some checks failed - see above for details")
    
    print_instructions()
    
    # Check if bypass is enabled
    if os.getenv('BYPASS_STATE_CHECK', 'false').lower() == 'true':
        print("\n" + "!"*60)
        print("  SECURITY WARNING")
        print("!"*60)
        print("BYPASS_STATE_CHECK is enabled!")
        print("This disables CSRF protection.")
        print("Only use this temporarily for debugging.")
        print("Set BYPASS_STATE_CHECK=false in .env when done.")
        print("!"*60)

if __name__ == "__main__":
    main()
