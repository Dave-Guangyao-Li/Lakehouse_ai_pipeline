#!/bin/bash
# Stop data collectors

echo "🛑 Stopping Data Collectors..."
echo ""

# Check for PID files
if [ -f "logs/twitter.pid" ]; then
    TWITTER_PID=$(cat logs/twitter.pid)
    if ps -p $TWITTER_PID > /dev/null 2>&1; then
        echo "🐦 Stopping Twitter collector (PID: $TWITTER_PID)..."
        kill $TWITTER_PID
        echo "   ✅ Twitter collector stopped"
    else
        echo "   ℹ️  Twitter collector is not running"
    fi
    rm logs/twitter.pid
else
    echo "   ℹ️  No Twitter PID file found"
fi

if [ -f "logs/reddit.pid" ]; then
    REDDIT_PID=$(cat logs/reddit.pid)
    if ps -p $REDDIT_PID > /dev/null 2>&1; then
        echo "🤖 Stopping Reddit collector (PID: $REDDIT_PID)..."
        kill $REDDIT_PID
        echo "   ✅ Reddit collector stopped"
    else
        echo "   ℹ️  Reddit collector is not running"
    fi
    rm logs/reddit.pid
else
    echo "   ℹ️  No Reddit PID file found"
fi

echo ""
echo "✅ All collectors stopped"
echo ""
