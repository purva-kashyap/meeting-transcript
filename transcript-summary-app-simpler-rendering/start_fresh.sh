#!/bin/bash

# Clear old session data for fresh start
echo "🧹 Clearing old session data..."
rm -rf flask_session/

echo "🚀 Starting Flask app..."
echo ""
echo "📍 App will be available at: http://localhost:5001"
echo "🔍 Debug session endpoint: http://localhost:5001/debug/session"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python app.py
