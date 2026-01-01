#!/bin/bash

echo "🚀 Starting Meeting Transcript Summary App..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Start the app
echo ""
echo "🎉 Starting Flask app..."
echo "📱 Open your browser and go to: http://localhost:5000"
echo ""
echo "Test email addresses:"
echo "  - user@example.com"
echo "  - test@test.com"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
