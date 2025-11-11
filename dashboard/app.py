"""
Streamlit Dashboard for AI Trend Monitoring
Real-time visualization of trending AI topics from social media
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Page configuration
st.set_page_config(
    page_title="AI Trend Monitor",
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
</style>
""", unsafe_allow_html=True)


def generate_sample_data():
    """Generate sample data for demonstration (replace with real Delta Lake queries)"""
    # Trending topics
    topics = pd.DataFrame({
        'topic': ['GPT-5', 'Claude 3.5', 'Llama 3', 'Gemini Ultra', 'Open Source LLMs',
                  'AI Safety', 'RAG Systems', 'AI Agents', 'Multimodal AI', 'Fine-tuning'],
        'mentions': [850, 720, 650, 580, 520, 480, 450, 420, 380, 350],
        'engagement': [12500, 10800, 9200, 8600, 7800, 7200, 6800, 6400, 5900, 5400],
        'trend_score': [95.2, 88.5, 82.1, 76.8, 71.3, 68.5, 65.2, 62.1, 58.7, 55.3]
    })

    # Time series data
    hours = pd.date_range(end=datetime.now(), periods=24, freq='H')
    timeseries = pd.DataFrame({
        'hour': hours,
        'twitter': [120, 135, 145, 132, 128, 156, 178, 192, 210, 225, 242, 258,
                   275, 268, 255, 248, 265, 285, 295, 312, 328, 342, 358, 375],
        'reddit': [45, 52, 48, 55, 62, 68, 72, 78, 85, 92, 98, 105,
                  112, 108, 102, 98, 105, 118, 125, 132, 138, 145, 152, 160]
    })

    # Recent posts
    recent_posts = pd.DataFrame({
        'source': ['Twitter', 'Reddit', 'Twitter', 'Reddit', 'Twitter'],
        'text': [
            'GPT-5 rumors suggest massive improvements in reasoning capabilities...',
            'Claude 3.5 is amazing for code generation! Just tried it and...',
            'Open source LLMs are catching up fast. Llama 3 performance is...',
            'Discussion: Best RAG architecture for production systems?',
            'New paper on AI agents shows promising results in...'
        ],
        'engagement': [1250, 890, 756, 642, 589],
        'timestamp': pd.date_range(end=datetime.now(), periods=5, freq='5min')
    })

    # Source distribution
    sources = pd.DataFrame({
        'source': ['Twitter', 'Reddit', 'HackerNews'],
        'count': [2450, 1380, 0]  # HackerNews not implemented yet
    })

    return topics, timeseries, recent_posts, sources


def main():
    """Main dashboard application"""

    # Header
    st.markdown('<div class="main-header">🤖 AI Trend Monitor Dashboard</div>', unsafe_allow_html=True)
    st.markdown("Real-time monitoring of AI discussions across social media")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 30)

        st.markdown("---")

        # Time range filter
        st.subheader("📅 Time Range")
        time_range = st.selectbox(
            "Select period",
            ["Last 1 hour", "Last 6 hours", "Last 24 hours", "Last 7 days"]
        )

        st.markdown("---")

        # Source filter
        st.subheader("📊 Data Sources")
        show_twitter = st.checkbox("Twitter", value=True)
        show_reddit = st.checkbox("Reddit", value=True)

        st.markdown("---")

        # Statistics
        st.subheader("📈 System Stats")
        st.metric("Total Posts", "3,830")
        st.metric("Active Topics", "47")
        st.metric("Uptime", "2d 14h")

    # Generate sample data
    topics_df, timeseries_df, posts_df, sources_df = generate_sample_data()

    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🔥 Hottest Topic",
            value="GPT-5",
            delta="+23% mentions"
        )

    with col2:
        st.metric(
            label="📊 Total Posts (24h)",
            value="3,830",
            delta="+12.5%"
        )

    with col3:
        st.metric(
            label="💬 Avg Engagement",
            value="8,450",
            delta="+8.3%"
        )

    with col4:
        st.metric(
            label="⚡ Trending Score",
            value="95.2",
            delta="+5.7"
        )

    st.markdown("---")

    # Main content - two columns
    left_col, right_col = st.columns([2, 1])

    with left_col:
        # Trending topics chart
        st.subheader("🔥 Top Trending Topics")

        fig_topics = px.bar(
            topics_df.head(10),
            x='trend_score',
            y='topic',
            orientation='h',
            color='trend_score',
            color_continuous_scale='Blues',
            labels={'trend_score': 'Trend Score', 'topic': 'Topic'}
        )
        fig_topics.update_layout(
            showlegend=False,
            height=400,
            yaxis={'categoryorder': 'total ascending'}
        )
        st.plotly_chart(fig_topics, use_container_width=True)

        # Time series chart
        st.subheader("📈 Post Volume Over Time")

        fig_timeseries = go.Figure()
        if show_twitter:
            fig_timeseries.add_trace(go.Scatter(
                x=timeseries_df['hour'],
                y=timeseries_df['twitter'],
                mode='lines+markers',
                name='Twitter',
                line=dict(color='#1DA1F2', width=2)
            ))
        if show_reddit:
            fig_timeseries.add_trace(go.Scatter(
                x=timeseries_df['hour'],
                y=timeseries_df['reddit'],
                mode='lines+markers',
                name='Reddit',
                line=dict(color='#FF4500', width=2)
            ))

        fig_timeseries.update_layout(
            xaxis_title="Time",
            yaxis_title="Number of Posts",
            hovermode='x unified',
            height=350
        )
        st.plotly_chart(fig_timeseries, use_container_width=True)

    with right_col:
        # Source distribution pie chart
        st.subheader("📊 Data Source Distribution")

        fig_sources = px.pie(
            sources_df,
            values='count',
            names='source',
            color='source',
            color_discrete_map={
                'Twitter': '#1DA1F2',
                'Reddit': '#FF4500',
                'HackerNews': '#FF6600'
            }
        )
        fig_sources.update_traces(textposition='inside', textinfo='percent+label')
        fig_sources.update_layout(height=300)
        st.plotly_chart(fig_sources, use_container_width=True)

        # Topic engagement
        st.subheader("💬 Engagement by Topic")

        fig_engagement = px.scatter(
            topics_df.head(10),
            x='mentions',
            y='engagement',
            size='trend_score',
            color='trend_score',
            hover_data=['topic'],
            color_continuous_scale='Viridis',
            labels={'mentions': 'Mentions', 'engagement': 'Total Engagement'}
        )
        fig_engagement.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_engagement, use_container_width=True)

    st.markdown("---")

    # Recent posts table
    st.subheader("📝 Recent Posts")

    # Format the dataframe
    posts_display = posts_df.copy()
    posts_display['timestamp'] = posts_display['timestamp'].dt.strftime('%H:%M:%S')
    posts_display = posts_display.rename(columns={
        'source': 'Source',
        'text': 'Content',
        'engagement': 'Engagement',
        'timestamp': 'Time'
    })

    st.dataframe(
        posts_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Engagement": st.column_config.NumberColumn(
                format="%d 👍"
            )
        }
    )

    # Footer with last update time
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.caption(f"🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption("💾 Data stored in Delta Lake | ⚡ Powered by Spark Streaming")

    # Auto-refresh logic
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
