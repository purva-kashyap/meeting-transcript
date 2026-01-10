#!/bin/bash

echo "🔍 Azure App Configuration Diagnostic"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "   Create .env file from .env.example"
    exit 1
fi

echo "✅ .env file found"
echo ""

# Load and check environment variables
echo "📋 Environment Variables:"
echo "------------------------"

# Function to check env var
check_env() {
    local var_name=$1
    local var_value=$(grep "^$var_name=" .env 2>/dev/null | cut -d '=' -f2- | tr -d '"' | tr -d "'")
    
    if [ -z "$var_value" ]; then
        echo "❌ $var_name: NOT SET"
        return 1
    else
        # Show first 10 chars for secrets
        if [[ $var_name == *"SECRET"* ]]; then
            echo "✅ $var_name: ${var_value:0:10}... (length: ${#var_value})"
        else
            echo "✅ $var_name: $var_value"
        fi
        return 0
    fi
}

# Check required variables
check_env "USE_MOCK_DATA"
USE_MOCK=$(grep "^USE_MOCK_DATA=" .env 2>/dev/null | cut -d '=' -f2 | tr -d '"' | tr -d "'")

if [ "$USE_MOCK" = "false" ]; then
    echo ""
    echo "🔴 Production Mode (USE_MOCK_DATA=false)"
    echo "   The following must be set:"
    echo ""
    
    ALL_SET=true
    
    check_env "MICROSOFT_CLIENT_ID" || ALL_SET=false
    check_env "MICROSOFT_CLIENT_SECRET" || ALL_SET=false
    check_env "MICROSOFT_TENANT_ID" || ALL_SET=false
    check_env "MICROSOFT_REDIRECT_URI" || ALL_SET=false
    check_env "MICROSOFT_AUTHORITY" || ALL_SET=false
    
    echo ""
    
    if [ "$ALL_SET" = true ]; then
        echo "✅ All required variables are set"
    else
        echo "❌ Some required variables are missing!"
        echo ""
        echo "Quick fix:"
        echo "  1. Go to Azure Portal"
        echo "  2. Find your app registration"
        echo "  3. Copy Client ID, Tenant ID, and create Client Secret"
        echo "  4. Update .env file"
        exit 1
    fi
else
    echo ""
    echo "🟢 Mock Mode (USE_MOCK_DATA=true)"
    echo "   Real Azure credentials not required for testing"
fi

echo ""
echo "═══════════════════════════════════════════"
echo "🔧 Azure Portal Configuration Checklist"
echo "═══════════════════════════════════════════"
echo ""
echo "If you're getting 'Client is public' error:"
echo ""
echo "1. Go to: Azure Portal → Azure AD → App registrations → Your app"
echo ""
echo "2. Click 'Authentication' (left menu)"
echo ""
echo "3. Scroll to 'Advanced settings'"
echo ""
echo "4. Find 'Allow public client flows'"
echo "   ⚠️  Current: Probably 'Yes' (causing error)"
echo "   ✅ Should be: 'No' (for server apps)"
echo ""
echo "5. Change to 'No' and click 'Save'"
echo ""
echo "6. Click 'Certificates & secrets' (left menu)"
echo ""
echo "7. Under 'Client secrets' tab:"
echo "   - Verify you have an active secret (not expired)"
echo "   - If not, create new secret"
echo "   - Copy the VALUE (not the ID)"
echo ""
echo "8. Update your .env file:"
echo "   MICROSOFT_CLIENT_SECRET=<paste-secret-value-here>"
echo ""
echo "9. Restart the app:"
echo "   ./start_fresh.sh"
echo ""
echo "═══════════════════════════════════════════"
echo ""

# Check if app is running
if curl -s http://localhost:5001/debug/msal-config > /dev/null 2>&1; then
    echo "🌐 App is running - Checking configuration..."
    echo ""
    
    CONFIG=$(curl -s http://localhost:5001/debug/msal-config)
    echo "MSAL Configuration:"
    echo "$CONFIG" | python3 -m json.tool 2>/dev/null || echo "$CONFIG"
    echo ""
    
    # Check if client_secret_set is true
    if echo "$CONFIG" | grep -q '"client_secret_set": true'; then
        echo "✅ Client secret is loaded in app"
    else
        echo "❌ Client secret is NOT loaded in app"
        echo "   Restart app after updating .env: ./start_fresh.sh"
    fi
else
    echo "ℹ️  App is not running"
    echo "   Start with: ./start_fresh.sh"
    echo "   Then check: http://localhost:5001/debug/msal-config"
fi

echo ""
echo "═══════════════════════════════════════════"
echo "📚 Documentation:"
echo "   - TROUBLESHOOT_PUBLIC_CLIENT_ERROR.md"
echo "   - REDIRECT_URI_GUIDE.md"
echo "   - PRODUCTION_CHECKLIST.md"
echo "═══════════════════════════════════════════"
