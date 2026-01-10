#!/usr/bin/env python3
"""
Azure AD Configuration Verifier
This script checks your Azure AD app registration and local configuration
to identify the cause of the "public client" error.
"""

import os
import sys
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_env_variables():
    """Check if required environment variables are set"""
    print_section("1. Environment Variables Check")
    
    required_vars = [
        'AZURE_CLIENT_ID',
        'AZURE_CLIENT_SECRET',
        'AZURE_TENANT_ID',
        'REDIRECT_URI'
    ]
    
    all_present = True
    for var in required_vars:
        value = os.getenv(var, '')
        if value:
            # Show partial value for security
            if var == 'AZURE_CLIENT_SECRET':
                display_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            elif var == 'AZURE_CLIENT_ID':
                display_value = value
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
            print(f"✓ {var}: {display_value}")
        else:
            print(f"✗ {var}: NOT SET")
            all_present = False
    
    return all_present

def check_client_secret_format():
    """Check if client secret looks valid"""
    print_section("2. Client Secret Format Check")
    
    client_secret = os.getenv('AZURE_CLIENT_SECRET', '')
    
    if not client_secret:
        print("✗ Client secret is not set")
        return False
    
    # Azure client secrets are typically 40+ characters and contain alphanumeric + special chars
    if len(client_secret) < 20:
        print(f"⚠ WARNING: Client secret seems too short ({len(client_secret)} chars)")
        print("  This might be the Secret ID instead of the Secret VALUE")
        print("  In Azure Portal, when you create a new secret, copy the VALUE immediately!")
        return False
    
    print(f"✓ Client secret length: {len(client_secret)} characters")
    print(f"  First 4 chars: {client_secret[:4]}")
    print(f"  Last 4 chars: {client_secret[-4:]}")
    
    # Check if it looks like a GUID (which would be wrong)
    if len(client_secret) == 36 and client_secret.count('-') == 4:
        print("✗ ERROR: This looks like a GUID (Secret ID), not a secret value!")
        print("  You need the SECRET VALUE from Azure Portal")
        return False
    
    return True

def check_redirect_uri_format():
    """Check if redirect URI is properly formatted"""
    print_section("3. Redirect URI Format Check")
    
    redirect_uri = os.getenv('REDIRECT_URI', '')
    
    if not redirect_uri:
        print("✗ REDIRECT_URI is not set")
        return False
    
    print(f"✓ REDIRECT_URI: {redirect_uri}")
    
    # Check common issues
    issues = []
    if not redirect_uri.startswith(('http://localhost', 'https://localhost', 'http://127.0.0.1', 'https://127.0.0.1', 'https://')):
        issues.append("Should start with http://localhost, https://localhost, or https://yourdomain.com")
    
    if redirect_uri.endswith('/'):
        issues.append("Should NOT end with a trailing slash")
    
    if not '/auth/callback' in redirect_uri:
        issues.append("Path should be /auth/callback")
    
    if issues:
        print("\n⚠ Potential issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    return True

def check_azure_ad_config():
    """Check if we can reach Azure AD and get app info"""
    print_section("4. Azure AD App Configuration Check")
    
    client_id = os.getenv('AZURE_CLIENT_ID', '')
    tenant_id = os.getenv('AZURE_TENANT_ID', '')
    
    if not client_id or not tenant_id:
        print("✗ Cannot check Azure AD - missing client_id or tenant_id")
        return False
    
    # Try to get OpenID configuration
    try:
        config_url = f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration"
        print(f"\nFetching Azure AD configuration...")
        response = requests.get(config_url, timeout=5)
        
        if response.status_code == 200:
            print("✓ Successfully connected to Azure AD")
            config = response.json()
            print(f"  Authorization endpoint: {config.get('authorization_endpoint', 'N/A')[:60]}...")
            print(f"  Token endpoint: {config.get('token_endpoint', 'N/A')[:60]}...")
        else:
            print(f"✗ Failed to get Azure AD config: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error connecting to Azure AD: {e}")
        return False
    
    return True

def print_recommendations():
    """Print recommendations for fixing the public client error"""
    print_section("RECOMMENDATIONS TO FIX 'PUBLIC CLIENT' ERROR")
    
    print("""
The "public client" error occurs when Azure AD thinks your app is a
public client (mobile/desktop app) instead of a confidential client (web app).

TO FIX THIS:

1. Go to Azure Portal (portal.azure.com)
   
2. Navigate to: Azure Active Directory → App registrations → [Your App]

3. Check AUTHENTICATION settings:
   
   a) Under "Platform configurations":
      ✓ You MUST have "Web" platform configured
      ✓ Add redirect URI: """ + os.getenv('REDIRECT_URI', 'http://localhost:5000/auth/callback') + """
      ✗ Remove any "Mobile and desktop applications" platform
   
   b) Under "Advanced settings" → "Allow public client flows":
      ✓ This MUST be set to "No"
      ✗ If it's "Yes", change it to "No" and SAVE

4. Check CERTIFICATES & SECRETS:
   
   a) Under "Client secrets":
      - You should have at least one active secret
      - When you create a new secret, copy the VALUE immediately
      - The value is only shown ONCE when created
      - If you didn't copy it, create a new secret
   
   b) In your .env file:
      - AZURE_CLIENT_SECRET should be the SECRET VALUE (not the ID)
      - The value is typically 40+ characters
      - It contains letters, numbers, and special characters

5. RESTART your Flask app after making changes

6. Test the authentication flow again
""")

    # Check specific issues
    client_secret = os.getenv('AZURE_CLIENT_SECRET', '')
    if len(client_secret) == 36 and client_secret.count('-') == 4:
        print("\n⚠ CRITICAL: Your AZURE_CLIENT_SECRET looks like a Secret ID, not the VALUE!")
        print("   Action needed:")
        print("   1. Go to Azure Portal → Your App → Certificates & secrets")
        print("   2. Delete the old secret (or let it expire)")
        print("   3. Click 'New client secret'")
        print("   4. Copy the VALUE (the long string in the 'Value' column)")
        print("   5. Paste it into your .env file as AZURE_CLIENT_SECRET")
        print("   6. Restart your app")

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("  AZURE AD CONFIGURATION DIAGNOSTIC TOOL")
    print("="*60)
    
    results = {
        'env_vars': check_env_variables(),
        'client_secret': check_client_secret_format(),
        'redirect_uri': check_redirect_uri_format(),
        'azure_ad': check_azure_ad_config()
    }
    
    print_section("SUMMARY")
    
    all_passed = all(results.values())
    
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check.replace('_', ' ').title()}")
    
    if all_passed:
        print("\n✓ All checks passed!")
        print("  If you're still getting 'public client' error, check Azure Portal settings:")
        print("  1. Platform should be 'Web' (not 'Mobile and desktop')")
        print("  2. 'Allow public client flows' should be 'No'")
        print("  3. Client secret should be fresh and valid")
    else:
        print("\n✗ Some checks failed. See recommendations below.")
    
    print_recommendations()

if __name__ == "__main__":
    main()
