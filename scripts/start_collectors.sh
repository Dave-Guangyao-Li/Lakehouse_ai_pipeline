#!/bin/bash
# Start data collectors (Twitter and Reddit)

echo "🔍 Starting Data Collectors..."
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

# Check if .env file exists and has API keys
if [ ! -f "config/.env" ]; then
    echo "❌ config/.env not found. Please create it from config/env.example"
    exit 1
fi

# Create logs directory
mkdir -p logs

echo "📊 Starting collectors in background..."
echo ""
echo "⚠️  快速演示模式: 仅启动Reddit采集器"
echo "   Twitter暂时禁用（避免API限流）"
echo ""

# Twitter collector - 暂时禁用
# echo "🐦 Starting Twitter collector..."
# python data_ingestion/twitter/collector.py > logs/twitter_collector.log 2>&1 &
# TWITTER_PID=$!
# echo "   PID: $TWITTER_PID"

# Start Reddit collector
echo "🤖 Starting Reddit collector..."
python data_ingestion/reddit/collector.py > logs/reddit_collector.log 2>&1 &
REDDIT_PID=$!
echo "   PID: $REDDIT_PID"

echo ""
echo "✅ Reddit collector started!"
echo ""
echo "📝 Process IDs:"
echo "   Reddit:  $REDDIT_PID"
echo ""
echo "📊 View logs:"
echo "   Reddit:  tail -f logs/reddit_collector.log"
echo ""
echo "🛑 To stop collector:"
echo "   kill $REDDIT_PID"
echo "   or use: ./scripts/stop_collectors.sh"
echo ""

# Save PID to file for easy stopping
echo "$REDDIT_PID" > logs/reddit.pid

echo "💾 PIDs saved to logs/*.pid"
echo ""
