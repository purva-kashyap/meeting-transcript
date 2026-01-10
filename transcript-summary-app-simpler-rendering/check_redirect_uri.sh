#!/bin/bash

echo "🔍 Redirect URI Configuration Check"
echo "===================================="
echo ""

# Check .env file
if [ -f .env ]; then
    REDIRECT_URI=$(grep "^MICROSOFT_REDIRECT_URI=" .env 2>/dev/null | cut -d '=' -f2- | tr -d '"' | tr -d "'")
    
    if [ -n "$REDIRECT_URI" ]; then
        echo "✅ .env MICROSOFT_REDIRECT_URI:"
        echo "   $REDIRECT_URI"
        echo ""
        
        # Check if using localhost or 127.0.0.1
        if echo "$REDIRECT_URI" | grep -q "localhost"; then
            echo "📍 Using: localhost"
            echo ""
            echo "✅ Recommended browser URL: http://localhost:5001"
            echo "⚠️  Avoid using: http://127.0.0.1:5001 (cookie mismatch)"
        elif echo "$REDIRECT_URI" | grep -q "127.0.0.1"; then
            echo "📍 Using: 127.0.0.1"
            echo ""
            echo "✅ Recommended browser URL: http://127.0.0.1:5001"
            echo "⚠️  Avoid using: http://localhost:5001 (cookie mismatch)"
        else
            echo "⚠️  Using custom domain"
        fi
    else
        echo "❌ MICROSOFT_REDIRECT_URI not set in .env"
    fi
else
    echo "❌ .env file not found"
fi

echo ""
echo "═══════════════════════════════════════════"
echo "Azure Portal Configuration"
echo "═══════════════════════════════════════════"
echo ""
echo "Make sure your Azure redirect URI matches EXACTLY:"
echo ""
if [ -n "$REDIRECT_URI" ]; then
    echo "   $REDIRECT_URI"
else
    echo "   <check your .env file first>"
fi
echo ""
echo "Steps:"
echo "1. Azure Portal → Azure AD → App registrations → Your app"
echo "2. Click 'Authentication'"
echo "3. Under 'Platform configurations' → 'Web'"
echo "4. Verify redirect URI matches above"
echo "5. Make sure it's under 'Web' platform (NOT 'Mobile and desktop')"
echo ""
echo "═══════════════════════════════════════════"
echo "Test URLs"
echo "═══════════════════════════════════════════"
echo ""

if [ -n "$REDIRECT_URI" ]; then
    if echo "$REDIRECT_URI" | grep -q "localhost"; then
        BASE_URL="http://localhost:5001"
    elif echo "$REDIRECT_URI" | grep -q "127.0.0.1"; then
        BASE_URL="http://127.0.0.1:5001"
    else
        BASE_URL="http://localhost:5001"
    fi
    
    echo "✅ Use these URLs (all should work):"
    echo ""
    echo "   Home page:    $BASE_URL"
    echo "   Debug config: $BASE_URL/debug/msal-config"
    echo "   Debug session:$BASE_URL/debug/session"
    echo ""
    
    # Test if app is running
    if curl -s "$BASE_URL" > /dev/null 2>&1; then
        echo "✅ App is running!"
        echo ""
        echo "Testing configuration..."
        CONFIG=$(curl -s "$BASE_URL/debug/msal-config" 2>/dev/null)
        
        if [ -n "$CONFIG" ]; then
            echo ""
            echo "MSAL Configuration:"
            echo "$CONFIG" | python3 -m json.tool 2>/dev/null || echo "$CONFIG"
        fi
    else
        echo "⚠️  App is not running"
        echo ""
        echo "Start with: ./start_fresh.sh"
    fi
fi

echo ""
echo "═══════════════════════════════════════════"
echo "Quick Test"
echo "═══════════════════════════════════════════"
echo ""
echo "1. Open browser to: $BASE_URL"
echo "2. Click 'Login to Post in Teams'"
echo "3. Observe the URL after Microsoft login"
echo "4. Should redirect to: $REDIRECT_URI"
echo "5. Should NOT see 'redirect URI mismatch' error"
echo ""
