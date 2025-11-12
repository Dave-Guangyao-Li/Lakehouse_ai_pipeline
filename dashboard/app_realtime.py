"""
Streamlit Dashboard for AI Trend Monitoring - REAL-TIME DYNAMIC VERSION
连接Kafka实时数据，包含所有动态元素
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

# Page configuration
st.set_page_config(
    page_title="AI Trend Monitor - Live",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 增强CSS - 添加动画效果
st.markdown("""
<style>
    /* 主标题 */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 1rem 0;
    }

    /* 数字滚动动画 */
    @keyframes countUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .metric-value {
        animation: countUp 0.5s ease-out;
    }

    /* 新数据闪烁动画 */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    .new-badge {
        background: linear-gradient(45deg, #4CAF50, #8BC34A);
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.9rem;
        font-weight: bold;
        animation: pulse 2s infinite;
        display: inline-block;
    }

    /* 实时状态灯 */
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    .live-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #FF5252;
        border-radius: 50%;
        margin-right: 8px;
        animation: blink 1.5s infinite;
    }

    /* 进度条样式 */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #1E88E5, #42A5F5);
    }

    /* 高亮新数据行 */
    .recent-data-highlight {
        background-color: #E8F5E9 !important;
        border-left: 4px solid #4CAF50 !important;
        animation: fadeIn 0.5s ease-in;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    /* 实时时钟样式 */
    .realtime-clock {
        font-size: 1.1rem;
        font-weight: 500;
        color: #424242;
    }

    /* 倒计时样式 */
    .countdown {
        font-size: 1.0rem;
        color: #FF9800;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# 初始化 session_state
if 'previous_count' not in st.session_state:
    st.session_state.previous_count = 0
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()


@st.cache_data(ttl=5)  # 缓存5秒（快速刷新）
def load_real_data():
    """从Kafka加载实时数据"""
    if not KAFKA_AVAILABLE:
        return None, 0

    try:
        reader = KafkaDataReader(
            bootstrap_servers='localhost:9092',
            topic='ai-social-raw'
            # 移除 max_messages 限制，读取全部数据
        )

        # 获取总消息数（快速）
        total_count = reader.get_message_count()

        # 获取所有消息
        messages = reader.get_all_messages()

        if not messages:
            return None, total_count

        df = reader.parse_to_dataframe(messages)

        if df.empty:
            return None, total_count

        return df, total_count

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, 0


def analyze_trending_topics(df):
    """分析热门话题"""
    if df is None or df.empty:
        return pd.DataFrame()

    keywords = ['GPT', 'Claude', 'LLM', 'ChatGPT', 'OpenAI', 'AI', 'Anthropic',
                'Gemini', 'Llama', 'Machine Learning', 'Deep Learning']

    topic_counts = []

    for keyword in keywords:
        count = df['text'].str.contains(keyword, case=False, na=False).sum()
        if count > 0:
            topic_counts.append({
                'topic': keyword,
                'mentions': count
            })

    return pd.DataFrame(topic_counts).sort_values('mentions', ascending=False)


def main():
    """主应用"""

    # === 顶部状态栏 ===
    col_time, col_countdown, col_btn = st.columns([2, 2, 1])

    with col_time:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.markdown(f'<div class="realtime-clock">⏰ <b>当前时间</b>: {current_time}</div>',
                   unsafe_allow_html=True)

    with col_countdown:
        # 计算下次刷新倒计时
        elapsed = time.time() - st.session_state.last_refresh
        next_refresh = max(0, 5 - int(elapsed))
        st.markdown(f'<div class="countdown">⏳ <b>下次刷新</b>: {next_refresh} 秒</div>',
                   unsafe_allow_html=True)

        # 进度条
        progress = min(1.0, elapsed / 5)
        st.progress(progress)

    with col_btn:
        if st.button("🔄 立即刷新"):
            st.cache_data.clear()
            st.session_state.last_refresh = time.time()
            st.rerun()

    st.markdown("---")

    # === 主标题 ===
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="main-header">🤖 AI Trend Monitor</div>', unsafe_allow_html=True)
        st.markdown("""
            <center>
                <span class="live-indicator"></span>
                <span style="font-size: 1.1rem; font-weight: 600; color: #FF5252;">LIVE DATA</span>
            </center>
        """, unsafe_allow_html=True)

    st.markdown("Real-time monitoring of AI discussions from Twitter and Reddit")

    # === 侧边栏 ===
    with st.sidebar:
        st.header("⚙️ Settings")

        auto_refresh = st.checkbox("Auto-refresh", value=True)

        st.markdown("---")

        st.subheader("📊 Data Sources")

        if KAFKA_AVAILABLE:
            st.success("✅ Kafka Connected")
        else:
            st.error("❌ Kafka Unavailable")

        st.markdown("---")

        # 显示采集器状态
        st.subheader("🤖 Collectors Status")
        st.markdown("- 🐦 **Twitter**: ⏸️ 暂停（避免限流）")
        st.markdown("- 🤖 **Reddit**: ✅ 运行中")
        st.caption("📡 采集频率: 60秒/次")

    # === 加载数据 ===
    with st.spinner("📊 Loading real-time data from Kafka..."):
        df, total_count = load_real_data()

    # === 计算新增数据 ===
    new_data_count = total_count - st.session_state.previous_count
    if new_data_count != 0:
        st.session_state.previous_count = total_count

    # === 显示新增提示 ===
    if new_data_count > 0:
        st.markdown(f"""
            <div style="text-align: center; margin: 1rem 0;">
                <span class="new-badge">🆕 新增 +{new_data_count} 条数据！</span>
            </div>
        """, unsafe_allow_html=True)

    # === 数据检查 ===
    if df is None or df.empty:
        st.error("⚠️ No data available")
        st.info("💡 数据正在采集中，请稍等...")
        st.markdown(f"**Kafka总消息数**: {total_count}")
        return

    # === 数据统计 ===
    total_posts = len(df)
    twitter_count = len(df[df['source'] == 'Twitter'])
    reddit_count = len(df[df['source'] == 'Reddit'])
    total_engagement = df['engagement'].sum()

    # === 核心指标 ===
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        delta_str = f"+{new_data_count}" if new_data_count > 0 else None
        st.metric(
            label="📊 Total Posts",
            value=f"{total_posts:,}",
            delta=delta_str
        )

    with col2:
        pct = f"{twitter_count/total_posts*100:.1f}%" if total_posts > 0 else "0%"
        st.metric(
            label="🐦 Twitter Posts",
            value=f"{twitter_count:,}",
            delta=pct
        )

    with col3:
        pct = f"{reddit_count/total_posts*100:.1f}%" if total_posts > 0 else "0%"
        st.metric(
            label="🤖 Reddit Posts",
            value=f"{reddit_count:,}",
            delta=pct
        )

    with col4:
        st.metric(
            label="💬 Total Engagement",
            value=f"{total_engagement:,}",
            delta="Live"
        )

    st.markdown("---")

    # === 主要内容区 ===
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("🔥 Trending Topics (from Real Data)")

        topics_df = analyze_trending_topics(df)

        if not topics_df.empty:
            # 带动画的柱状图
            fig = px.bar(
                topics_df.head(10),
                x='topic',
                y='mentions',
                title='Most Mentioned Topics',
                labels={'mentions': 'Mentions', 'topic': 'Topic'},
                color='mentions',
                color_continuous_scale='Blues'
            )

            fig.update_layout(
                xaxis_tickangle=-45,
                showlegend=False,
                height=400,
                transition_duration=500  # 过渡动画
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trending topics found yet")

    with col_right:
        st.subheader("📊 Data Source Distribution")

        # 饼图
        source_counts = df['source'].value_counts()

        fig = px.pie(
            values=source_counts.values,
            names=source_counts.index,
            title='Twitter vs Reddit',
            color_discrete_map={'Twitter': '#1DA1F2', 'Reddit': '#FF4500'}
        )

        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # === 显示最近数据（高亮最近5分钟） ===
    st.subheader("👥 Most Active Authors")

    if 'author' in df.columns:
        top_authors = df.groupby('author').agg({
            'post_id': 'count',
            'engagement': 'sum'
        }).rename(columns={'post_id': 'posts', 'engagement': 'total_engagement'})
        top_authors = top_authors.sort_values('posts', ascending=False).head(10)

        st.dataframe(top_authors, use_container_width=True)

    st.markdown("---")

    # === 最新帖子列表（高亮最近数据） ===
    st.subheader("📝 Recent Posts")

    # 标记最近5分钟的数据
    if 'created_at' in df.columns:
        try:
            df['created_at_parsed'] = pd.to_datetime(df['created_at'], errors='coerce')
            current_time = datetime.now()
            df['is_recent'] = (current_time - df['created_at_parsed']) < timedelta(minutes=5)
        except:
            df['is_recent'] = False
    else:
        df['is_recent'] = False

    # 显示最近20条
    recent_df = df.sort_values('created_at', ascending=False).head(20) if 'created_at' in df.columns else df.head(20)

    # 显示列
    display_cols = ['source', 'author', 'text', 'engagement']
    if 'subreddit' in recent_df.columns:
        display_cols.append('subreddit')

    display_df = recent_df[display_cols].copy()
    display_df['text'] = display_df['text'].str[:100] + '...'  # 截断长文本

    st.dataframe(
        display_df,
        use_container_width=True,
        height=400
    )

    # === 页脚信息 ===
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption(f"🔄 Last updated: {current_time}")

    with col2:
        st.caption(f"📊 Kafka messages: {total_count:,}")

    with col3:
        st.caption("💾 Data source: Kafka | ⚡ Powered by Spark")

    # === 自动刷新逻辑 ===
    if auto_refresh:
        # 每5秒自动刷新
        if time.time() - st.session_state.last_refresh >= 5:
            st.session_state.last_refresh = time.time()
            time.sleep(0.1)
            st.rerun()


if __name__ == "__main__":
    main()
