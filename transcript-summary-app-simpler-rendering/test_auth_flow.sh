#!/bin/bash

# Test Script for Authentication Fix
# This script helps test the authentication flow end-to-end

echo "🧪 Testing Authentication Flow Fix"
echo "===================================="
echo ""

# Check if the app is running
APP_URL="http://localhost:5001"
if ! curl -s "$APP_URL" > /dev/null 2>&1; then
    echo "⚠️  App is not running. Starting it now..."
    cd "$(dirname "$0")"
    ./start_fresh.sh &
    sleep 3
fi

echo "✅ App is running at $APP_URL"
echo ""

echo "📋 Test Steps:"
echo "1. Open browser to: $APP_URL"
echo "2. Enter email: user@example.com"
echo "3. Click 'Microsoft Teams'"
echo "4. Select date range and click 'View Meetings'"
echo "5. Click 'View Summary' on any meeting"
echo ""
echo "Expected Initial State:"
echo "  - Button shows: '🔐 Login to Post in Teams'"
echo "  - No user indicator in header"
echo ""
echo "6. Click '🔐 Login to Post in Teams'"
echo "7. Click 'Accept & Sign In' on mock login page"
echo ""
echo "Expected After Login:"
echo "  - Redirected back to summary page"
echo "  - Button shows: '📤 Send in Teams'"
echo "  - User indicator shows: '👤 Mock User'"
echo ""
echo "8. Click '📤 Send in Teams'"
echo "9. Confirm in dialog"
echo ""
echo "Expected After Send:"
echo "  - Alert: '✅ Summary sent successfully to Teams!'"
echo ""

echo "🔍 Debug Commands:"
echo "  - Check session: curl -s $APP_URL/debug/session | jq"
echo "  - View logs: tail -f nohup.out"
echo "  - List sessions: ls -la flask_session/"
echo ""

# Open browser (macOS)
if command -v open > /dev/null 2>&1; then
    echo "🌐 Opening browser..."
    open "$APP_URL"
fi

echo ""
echo "✨ Test the flow manually following the steps above"
echo "📝 Report any issues you find"
