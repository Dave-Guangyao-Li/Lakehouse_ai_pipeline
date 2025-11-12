#!/bin/bash
# Start Streamlit Dashboard with REAL-TIME data from Kafka

echo "📊 Starting AI Trend Monitor Dashboard (REAL-TIME VERSION)..."
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

echo "🔴 Launching REAL-TIME dashboard (connected to Kafka)..."
echo ""
echo "   URL: http://localhost:8501"
echo ""
echo "   This dashboard will show REAL data from Kafka!"
echo "   Make sure collectors are running to see live updates."
echo ""
echo "   Press Ctrl+C to stop the dashboard"
echo ""

# Start Streamlit with real-time app
streamlit run dashboard/app_realtime.py
