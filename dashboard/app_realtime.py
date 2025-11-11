"""
Streamlit Dashboard for AI Trend Monitoring - REAL-TIME VERSION
Connected to Kafka for real data
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from kafka_reader import KafkaDataReader
    KAFKA_AVAILABLE = True
except Exception as e:
    KAFKA_AVAILABLE = False
    st.error(f"Kafka connection unavailable: {e}")

# Page configuration
st.set_page_config(
    page_title="AI Trend Monitor - Real-time",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1E88E5;
    }
    .realtime-badge {
        background-color: #4CAF50;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=30)  # Cache for 30 seconds
def load_real_data():
    """Load real data from Kafka"""
    if not KAFKA_AVAILABLE:
        return None

    try:
        reader = KafkaDataReader(
            bootstrap_servers='localhost:9092',
            topic='ai-social-raw',
            max_messages=500
        )

        messages = reader.get_all_messages()

        if not messages:
            st.warning("No messages found in Kafka. Make sure collectors are running.")
            return None

        df = reader.parse_to_dataframe(messages)

        if df.empty:
            return None

        return df

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def analyze_trending_topics(df):
    """Analyze trending topics from text"""
    if df is None or df.empty:
        return pd.DataFrame()

    # Simple keyword extraction
    keywords = ['GPT', 'Claude', 'LLM', 'ChatGPT', 'OpenAI', 'AI', 'Anthropic',
                'Gemini', 'Llama', 'Machine Learning', 'Deep Learning']

    topic_counts = []

    for keyword in keywords:
        count = df['text'].str.contains(keyword, case=False, na=False).sum()
        if count > 0:
            topic_counts.append({
                'topic': keyword,
                'mentions': count,
                'engagement': df[df['text'].str.contains(keyword, case=False, na=False)]['engagement'].sum(),
                'trend_score': count * 10  # Simple scoring
            })

    return pd.DataFrame(topic_counts).sort_values('trend_score', ascending=False)


def main():
    """Main dashboard application"""

    # Header with real-time badge
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="main-header">🤖 AI Trend Monitor Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<center><span class="realtime-badge">🔴 LIVE DATA</span></center>', unsafe_allow_html=True)

    st.markdown("Real-time monitoring of AI discussions from Twitter and Reddit")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        refresh_interval = st.slider("Refresh interval (seconds)", 10, 120, 30)

        st.markdown("---")

        # Data source status
        st.subheader("📊 Data Sources")

        if KAFKA_AVAILABLE:
            st.success("✅ Kafka Connected")
        else:
            st.error("❌ Kafka Unavailable")

        st.markdown("---")

        # Manual refresh button
        if st.button("🔄 Refresh Now"):
            st.cache_data.clear()
            st.rerun()

    # Load real data
    with st.spinner("Loading real-time data from Kafka..."):
        df = load_real_data()

    if df is None or df.empty:
        st.error("⚠️ No data available. Please check:")
        st.markdown("""
        1. Kafka is running: `docker ps | grep kafka`
        2. Collectors are running: `tail -f logs/twitter_collector.log`
        3. Data exists in Kafka: `docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic ai-social-raw --from-beginning --max-messages 5`
        """)
        return

    # Data statistics
    total_posts = len(df)
    twitter_count = len(df[df['source'] == 'Twitter'])
    reddit_count = len(df[df['source'] == 'Reddit'])
    total_engagement = df['engagement'].sum()

    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📊 Total Posts",
            value=f"{total_posts:,}",
            delta="Real-time"
        )

    with col2:
        st.metric(
            label="🐦 Twitter Posts",
            value=f"{twitter_count:,}",
            delta=f"{twitter_count/total_posts*100:.1f}%"
        )

    with col3:
        st.metric(
            label="🤖 Reddit Posts",
            value=f"{reddit_count:,}",
            delta=f"{reddit_count/total_posts*100:.1f}%"
        )

    with col4:
        st.metric(
            label="💬 Total Engagement",
            value=f"{total_engagement:,}",
            delta="Live"
        )

    st.markdown("---")

    # Main content - two columns
    left_col, right_col = st.columns([2, 1])

    with left_col:
        # Trending topics
        st.subheader("🔥 Trending Topics (from Real Data)")

        topics_df = analyze_trending_topics(df)

        if not topics_df.empty:
            fig_topics = px.bar(
                topics_df.head(10),
                x='mentions',
                y='topic',
                orientation='h',
                color='mentions',
                color_continuous_scale='Blues',
                labels={'mentions': 'Mentions', 'topic': 'Topic'},
                title='Most Mentioned Topics'
            )
            fig_topics.update_layout(
                showlegend=False,
                height=400,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig_topics, use_container_width=True)
        else:
            st.info("Not enough data yet for topic analysis")

        # Engagement by source
        st.subheader("📈 Engagement by Source")

        engagement_by_source = df.groupby('source')['engagement'].sum().reset_index()

        fig_engagement = px.bar(
            engagement_by_source,
            x='source',
            y='engagement',
            color='source',
            color_discrete_map={'Twitter': '#1DA1F2', 'Reddit': '#FF4500'},
            labels={'engagement': 'Total Engagement', 'source': 'Platform'}
        )
        fig_engagement.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_engagement, use_container_width=True)

    with right_col:
        # Source distribution pie chart
        st.subheader("📊 Data Source Distribution")

        source_counts = df['source'].value_counts().reset_index()
        source_counts.columns = ['source', 'count']

        fig_sources = px.pie(
            source_counts,
            values='count',
            names='source',
            color='source',
            color_discrete_map={
                'Twitter': '#1DA1F2',
                'Reddit': '#FF4500'
            }
        )
        fig_sources.update_traces(textposition='inside', textinfo='percent+label')
        fig_sources.update_layout(height=300)
        st.plotly_chart(fig_sources, use_container_width=True)

        # Top authors
        st.subheader("👥 Most Active Authors")

        top_authors = df['author'].value_counts().head(10).reset_index()
        top_authors.columns = ['author', 'posts']

        st.dataframe(
            top_authors,
            use_container_width=True,
            hide_index=True,
            column_config={
                "author": "Author",
                "posts": st.column_config.NumberColumn("Posts", format="%d 📝")
            }
        )

    st.markdown("---")

    # Recent posts table
    st.subheader("📝 Recent Posts (Real-time)")

    # Show latest 20 posts
    recent_posts = df.sort_values('created_at', ascending=False).head(20) if 'created_at' in df.columns else df.head(20)

    display_df = recent_posts[['source', 'author', 'text', 'engagement']].copy()
    display_df['text'] = display_df['text'].str[:100] + '...'  # Truncate

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "source": "Platform",
            "author": "Author",
            "text": "Content",
            "engagement": st.column_config.NumberColumn(
                "Engagement",
                format="%d 👍"
            )
        }
    )

    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.caption(f"🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption(f"📊 Total messages in Kafka: {total_posts}")
        st.caption("💾 Data source: Apache Kafka | 🔴 Real-time streaming")

    # Auto-refresh logic
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
