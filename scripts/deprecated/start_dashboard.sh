#!/bin/bash
# Start Streamlit Dashboard

echo "📊 Starting AI Trend Monitor Dashboard..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "🚀 Launching Streamlit dashboard..."
echo ""
echo "   URL: http://localhost:8501"
echo ""
echo "   Press Ctrl+C to stop the dashboard"
echo ""

# Start Streamlit
streamlit run dashboard/app.py
