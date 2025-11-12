"""
Streamlit Dashboard for AI Trend Monitoring - 完全重构版本
- 真正的5秒倒计时
- NLP提取真实关键词
- 词云可视化
- Reddit卡片样式
- 现代化UI设计
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import sys
import os
from collections import Counter
import re

# NLP imports
try:
    import spacy
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    import nltk
    from nltk.corpus import stopwords

    NLP_AVAILABLE = True

    # 加载spacy模型
    try:
        nlp = spacy.load('en_core_web_sm')
    except:
        NLP_AVAILABLE = False

    # 下载stopwords（如果没有）
    try:
        STOP_WORDS = set(stopwords.words('english'))
    except LookupError:
        try:
            nltk.download('stopwords', quiet=True)
            STOP_WORDS = set(stopwords.words('english'))
        except:
            STOP_WORDS = set()

    # 自定义扩展停用词（虚词、代词、常见无意义词）
    CUSTOM_STOP_WORDS = {
        'that', 'this', 'these', 'those', 'them', 'they', 'their', 'theirs',
        'people', 'anyone', 'someone', 'something', 'anything', 'everything',
        'which', 'what', 'where', 'when', 'who', 'whom', 'whose',
        'the us', 'the model', 'the future', 'the world', 'the company',
        'a lot', 'lot', 'thing', 'things', 'stuff', 'way', 'ways',
        'time', 'times', 'question', 'thanks', 'thank',
        # 常见Reddit/社交媒体词
        'post', 'comment', 'thread', 'subreddit', 'user', 'upvote',
        # 通用代词和限定词
        'anyone', 'everyone', 'someone', 'nobody', 'anybody', 'somebody',
        'all', 'some', 'many', 'few', 'much', 'none',
    }
    STOP_WORDS.update(CUSTOM_STOP_WORDS)

except:
    NLP_AVAILABLE = False
    STOP_WORDS = set()

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

# 增强CSS - 现代化设计
st.markdown("""
<style>
    /* 整体背景 */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
    }

    /* 主标题 */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 1rem 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }

    /* 实时状态灯 */
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    .live-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: #FF5252;
        border-radius: 50%;
        margin-right: 8px;
        animation: blink 1.5s infinite;
        box-shadow: 0 0 10px rgba(255, 82, 82, 0.5);
    }

    /* 倒计时样式 */
    .countdown-container {
        background: white;
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .countdown {
        font-size: 1.1rem;
        color: #FF9800;
        font-weight: bold;
    }

    /* 实时时钟 */
    .realtime-clock {
        font-size: 1.1rem;
        font-weight: 500;
        color: #424242;
        background: white;
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Metric卡片美化 */
    div[data-testid="stMetric"] {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        transition: transform 0.2s, box-shadow 0.2s;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.12);
    }

    /* 进度条美化 */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #1E88E5, #42A5F5);
    }

    /* Reddit卡片样式 */
    .reddit-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        transition: all 0.2s;
    }

    .reddit-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateY(-2px);
        border-color: #FF4500;
    }

    .card-header {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        gap: 8px;
    }

    .source-badge {
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
        color: white;
    }

    .badge-reddit {
        background: #FF4500;
    }

    .badge-twitter {
        background: #1DA1F2;
    }

    .card-meta {
        color: #787C7E;
        font-size: 0.875rem;
    }

    .card-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #1c1c1c;
        margin: 10px 0;
        line-height: 1.4;
    }

    .card-footer {
        display: flex;
        gap: 16px;
        color: #787C7E;
        font-size: 0.875rem;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #f0f0f0;
    }

    /* Tab样式美化 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: white;
        border-radius: 8px;
        padding: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 4px;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)


# 初始化 session_state
if 'previous_count' not in st.session_state:
    st.session_state.previous_count = 0
if 'refresh_count' not in st.session_state:
    st.session_state.refresh_count = 0


@st.cache_data(ttl=300)  # 缓存5分钟
def load_real_data():
    """从Kafka加载实时数据"""
    if not KAFKA_AVAILABLE:
        return None, 0

    try:
        reader = KafkaDataReader(
            bootstrap_servers='localhost:9092',
            topic='ai-social-raw'
        )

        # 获取总消息数
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


def extract_real_keywords(df, top_n=20):
    """使用NLP提取真实的AI主题词（过滤虚词和停用词）"""
    if df is None or df.empty or not NLP_AVAILABLE:
        return pd.DataFrame()

    try:
        # 合并所有文本
        all_text = ' '.join(df['text'].astype(str).tolist())

        # 清理文本
        all_text = re.sub(r'http\S+|www\S+|https\S+', '', all_text)  # 移除URL
        all_text = re.sub(r'[^\w\s]', ' ', all_text)  # 移除标点

        # 使用spacy处理（限制长度避免超时）
        doc = nlp(all_text[:200000])

        # 提取有意义的词（只保留名词和专有名词）
        keywords = []

        for token in doc:
            # 词性过滤：只保留名词(NOUN)和专有名词(PROPN)
            if token.pos_ in ['NOUN', 'PROPN']:
                # 词形还原（将复数变单数、动词变原形等）
                word = token.lemma_.lower()

                # 严格过滤条件
                if (len(word) >= 3  # 至少3个字符
                    and word not in STOP_WORDS  # 不在停用词表
                    and not word.isdigit()  # 不是纯数字
                    and token.is_alpha  # 只包含字母
                    and word not in ['artificial intelligence', 'machine learning', 'deep learning']  # 过滤通用AI词
                    and not word.startswith('ai')  # 过滤ai开头的词
                    ):
                    keywords.append(word)

        # 统计频率
        keyword_counts = Counter(keywords).most_common(top_n)

        if not keyword_counts:
            return pd.DataFrame()

        return pd.DataFrame(keyword_counts, columns=['keyword', 'mentions'])

    except Exception as e:
        print(f"❌ 关键词提取错误: {e}")
        return pd.DataFrame()


def check_reddit_collector_status():
    """检查Reddit采集器运行状态"""
    log_file = 'logs/reddit_collector.log'

    try:
        # 检查日志文件是否存在
        if not os.path.exists(log_file):
            return {
                'status': 'unknown',
                'message': '日志文件不存在',
                'rate_limited': False,
                'last_success': False
            }

        # 读取最后100行日志
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()[-100:]

        if not lines:
            return {'status': 'unknown', 'message': '日志为空', 'rate_limited': False, 'last_success': False}

        # 检查rate limit（最近的日志）
        recent_lines = lines[-20:]
        has_rate_limit = any(
            'rate limit' in line.lower()
            or '429' in line
            or 'too many requests' in line.lower()
            for line in recent_lines
        )

        # 检查最近是否有成功采集
        has_success = any(
            'successfully' in line.lower()
            or '✅' in line
            or 'sent to kafka' in line.lower()
            for line in recent_lines
        )

        # 检查是否有错误
        has_error = any(
            'error' in line.lower()
            or '❌' in line
            or 'failed' in line.lower()
            for line in recent_lines
        )

        # 判断状态
        if has_rate_limit:
            status = 'limited'
            message = 'API调用受限，等待恢复中...'
        elif has_success:
            status = 'running'
            message = '正常运行'
        elif has_error:
            status = 'error'
            message = '采集出现错误'
        else:
            status = 'idle'
            message = '空闲或等待中'

        return {
            'status': status,
            'message': message,
            'rate_limited': has_rate_limit,
            'last_success': has_success
        }

    except Exception as e:
        return {
            'status': 'unknown',
            'message': f'无法读取状态: {str(e)}',
            'rate_limited': False,
            'last_success': False
        }


def create_word_cloud(df):
    """生成词云"""
    if df is None or df.empty or not NLP_AVAILABLE:
        st.info("词云功能需要NLP库支持")
        return

    try:
        keywords_df = extract_real_keywords(df, top_n=100)

        if keywords_df.empty:
            st.warning("无法生成词云：没有提取到关键词")
            return

        word_freq = dict(zip(keywords_df['keyword'], keywords_df['mentions']))

        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap='Blues',
            max_words=50,
            relative_scaling=0.5,
            min_font_size=12,
            collocations=False
        ).generate_from_frequencies(word_freq)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

    except Exception as e:
        st.error(f"词云生成错误: {e}")


def render_reddit_card(row):
    """渲染Reddit风格卡片"""
    source = row.get('source', 'Unknown')
    author = row.get('author', 'Unknown')
    text = str(row.get('text', ''))[:200]
    engagement = row.get('engagement', 0)
    subreddit = row.get('subreddit', '')

    badge_class = 'badge-reddit' if source == 'Reddit' else 'badge-twitter'

    card_html = f"""
    <div class="reddit-card">
        <div class="card-header">
            <span class="source-badge {badge_class}">{source}</span>
            <span class="card-meta">
                {'r/' + subreddit if subreddit else ''} {'• ' if subreddit else ''}by u/{author}
            </span>
        </div>

        <div class="card-title">{text}...</div>

        <div class="card-footer">
            <span>👍 {engagement:,}</span>
            <span>💬 评论</span>
            <span>🔗 分享</span>
        </div>
    </div>
    """

    return card_html


def main():
    """主应用"""

    # === 顶部状态栏 ===
    col_time, col_countdown, col_btn = st.columns([2, 2, 1])

    with col_time:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.markdown(f'<div class="realtime-clock">⏰ <b>当前时间</b>: {current_time}</div>',
                   unsafe_allow_html=True)

    # 创建倒计时占位符
    countdown_placeholder = col_countdown.empty()
    progress_placeholder = col_countdown.empty()

    with col_btn:
        if st.button("🔄 立即刷新", use_container_width=True):
            st.cache_data.clear()
            st.session_state.refresh_count += 1
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

        st.subheader("🤖 Collectors Status")

        # Twitter状态（暂停）
        st.markdown("- 🐦 **Twitter**: ⏸️ 暂停")

        # Reddit状态（动态检查）
        reddit_status = check_reddit_collector_status()

        if reddit_status['status'] == 'limited':
            st.markdown("- 🤖 **Reddit**: ⚠️ Rate Limited")
            st.caption(f"   {reddit_status['message']}")
        elif reddit_status['status'] == 'running':
            st.markdown("- 🤖 **Reddit**: ✅ 正常运行")
            st.caption("   📡 采集频率: 60秒/次")
        elif reddit_status['status'] == 'error':
            st.markdown("- 🤖 **Reddit**: ❌ 出现错误")
            st.caption(f"   {reddit_status['message']}")
        elif reddit_status['status'] == 'idle':
            st.markdown("- 🤖 **Reddit**: ⏸️ 空闲中")
            st.caption(f"   {reddit_status['message']}")
        else:
            st.markdown("- 🤖 **Reddit**: ❓ 状态未知")
            st.caption(f"   {reddit_status['message']}")

        if NLP_AVAILABLE:
            st.success("✅ NLP功能可用")
        else:
            st.warning("⚠️ NLP功能不可用")

    # === 加载数据 ===
    with st.spinner("📊 Loading real-time data from Kafka..."):
        df, total_count = load_real_data()

    # === 计算新增数据 ===
    new_data_count = total_count - st.session_state.previous_count
    if new_data_count != 0:
        st.session_state.previous_count = total_count

    # === 显示新增提示 ===
    if new_data_count > 0:
        st.success(f"🆕 新增 +{new_data_count} 条数据！")

    # === 数据检查 ===
    if df is None or df.empty:
        st.error("⚠️ No data available")
        st.info("💡 数据正在采集中，请稍等...")
        st.markdown(f"**Kafka总消息数**: {total_count}")

        # 倒计时循环（即使没数据也显示）
        if auto_refresh:
            for remaining in range(60, 0, -1):
                # 格式化显示时间
                if remaining >= 60:
                    time_str = f"{remaining // 60}分{remaining % 60}秒"
                else:
                    time_str = f"{remaining}秒"

                with countdown_placeholder:
                    st.markdown(f'<div class="countdown-container"><div class="countdown">⏳ <b>下次刷新</b>: {time_str}</div></div>',
                               unsafe_allow_html=True)
                with progress_placeholder:
                    progress = (60 - remaining) / 60
                    st.progress(progress)
                time.sleep(1)

            st.rerun()
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

    # === Tabs组织内容 ===
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "🔥 Trending Keywords", "📝 Recent Posts"])

    with tab1:
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

    with tab2:
        col_cloud, col_list = st.columns([2, 1])

        with col_cloud:
            st.subheader("☁️ Topic Word Cloud")
            create_word_cloud(df)

        with col_list:
            st.subheader("🔥 Top 10 Keywords")
            keywords_df = extract_real_keywords(df, 10)

            if not keywords_df.empty:
                # 柱状图
                fig = px.bar(
                    keywords_df,
                    x='mentions',
                    y='keyword',
                    orientation='h',
                    title='',
                    color='mentions',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("正在提取关键词...")

    with tab3:
        st.subheader("📝 Recent Posts")

        # 显示最近20条，按时间排序
        if 'created_at' in df.columns:
            recent_df = df.sort_values('created_at', ascending=False).head(20)
        else:
            recent_df = df.head(20)

        # 渲染卡片
        for idx, row in recent_df.iterrows():
            st.markdown(render_reddit_card(row), unsafe_allow_html=True)

    # === 页脚 ===
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption(f"🔄 Last updated: {current_time}")

    with col2:
        st.caption(f"📊 Kafka messages: {total_count:,}")

    with col3:
        st.caption("💾 Data source: Kafka | ⚡ Powered by Spark")

    # === 倒计时循环（60秒真实倒计时） ===
    if auto_refresh:
        for remaining in range(60, 0, -1):
            # 格式化显示时间
            if remaining >= 60:
                time_str = f"{remaining // 60}分{remaining % 60}秒"
            else:
                time_str = f"{remaining}秒"

            with countdown_placeholder:
                st.markdown(f'<div class="countdown-container"><div class="countdown">⏳ <b>下次刷新</b>: {time_str}</div></div>',
                           unsafe_allow_html=True)

            with progress_placeholder:
                progress = (60 - remaining) / 60
                st.progress(progress)

            time.sleep(1)

        # 60秒后自动刷新
        st.session_state.refresh_count += 1
        st.rerun()


if __name__ == "__main__":
    main()
