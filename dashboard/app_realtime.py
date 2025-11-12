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

    .badge-bluesky {
        background: #0085FF;
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
            print(f"⚠️ Warning: get_all_messages() returned empty list, but total_count={total_count}")
            return None, total_count

        df = reader.parse_to_dataframe(messages)

        if df.empty:
            print(f"⚠️ Warning: parse_to_dataframe() returned empty DataFrame from {len(messages)} messages")
            return None, total_count

        print(f"✅ Successfully loaded {len(df)} rows from Kafka (total_count={total_count})")
        return df, total_count

    except Exception as e:
        print(f"❌ Error loading data: {e}")
        import traceback
        traceback.print_exc()
        st.error(f"Error loading data: {e}")
        return None, 0


def extract_real_keywords(df, top_n=20):
    """使用NLP提取真实的AI概念短语（多词组合）"""
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

        # 通用词黑名单（过滤单个通用词）
        GENERIC_WORDS_BLACKLIST = {
            'data', 'image', 'model', 'tool', 'system', 'code', 'language',
            'result', 'problem', 'example', 'project', 'paper', 'test',
            'work', 'performance', 'version', 'feature', 'issue', 'user',
            'file', 'application', 'platform', 'service', 'product',
            'company', 'technology', 'solution', 'method', 'process',
            'source', 'experience', 'knowledge', 'context', 'inference',
            'search', 'noise', 'year', 'day', 'app', 'human', 'generation'
        }

        # 提取名词短语（noun chunks）
        phrases = []

        for chunk in doc.noun_chunks:
            phrase = chunk.text.lower().strip()
            words = phrase.split()
            num_words = len(words)

            # 过滤规则：
            # 1. 长度：2-4个词（我们要的是短语，不是单词）
            # 2. 不是纯停用词组合
            # 3. 不以通用词开头或结尾
            # 4. 不包含数字
            # 5. 过滤掉纯通用AI词

            if (2 <= num_words <= 4  # 多词短语
                and all(w not in STOP_WORDS for w in words)  # 不是停用词
                and words[0] not in GENERIC_WORDS_BLACKLIST  # 首词不是通用词
                and words[-1] not in GENERIC_WORDS_BLACKLIST  # 尾词不是通用词
                and not any(w.isdigit() for w in words)  # 不包含数字
                and phrase not in ['artificial intelligence', 'machine learning', 'deep learning', 'neural network']  # 过滤通用AI词
                and len(phrase) >= 8  # 总字符数至少8（避免太短的短语）
                ):
                phrases.append(phrase)

        # 统计频率
        phrase_counts = Counter(phrases).most_common(top_n)

        # 如果短语太少，降低标准，允许单个有意义的技术词
        if len(phrase_counts) < 5:
            keywords = []
            for token in doc:
                if token.pos_ in ['NOUN', 'PROPN']:
                    word = token.lemma_.lower()
                    if (len(word) >= 4
                        and word not in STOP_WORDS
                        and word not in GENERIC_WORDS_BLACKLIST
                        and not word.isdigit()
                        and token.is_alpha
                        and not word.startswith('ai')):
                        keywords.append(word)

            keyword_counts = Counter(keywords).most_common(top_n)
            # 合并短语和关键词，短语优先
            all_counts = phrase_counts + keyword_counts
            all_counts = dict(all_counts).items()
            phrase_counts = sorted(all_counts, key=lambda x: x[1], reverse=True)[:top_n]

        if not phrase_counts:
            return pd.DataFrame()

        return pd.DataFrame(phrase_counts, columns=['keyword', 'mentions'])

    except Exception as e:
        print(f"❌ 关键词提取错误: {e}")
        return pd.DataFrame()


def check_bluesky_collector_status():
    """检查Bluesky采集器运行状态"""
    log_file = 'logs/bluesky_collector.log'

    try:
        if not os.path.exists(log_file):
            return {
                'status': 'idle',
                'message': '日志文件不存在，采集器可能未启动',
                'rate_limited': False,
                'last_success': False
            }

        # 读取最近10行日志
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            recent_lines = lines[-10:] if len(lines) > 10 else lines

        recent_text = ''.join(recent_lines)

        # 检查最后修改时间
        last_modified = os.path.getmtime(log_file)
        time_diff = time.time() - last_modified

        # 超过5分钟没有更新
        if time_diff > 300:
            return {
                'status': 'idle',
                'message': f'采集器已空闲 {int(time_diff/60)} 分钟',
                'rate_limited': False,
                'last_success': False
            }

        # 检查是否有采集成功的记录
        if 'Collected and sent' in recent_text or '✅' in recent_text:
            return {
                'status': 'running',
                'message': '正在采集 Bluesky 帖子',
                'rate_limited': False,
                'last_success': True
            }

        # 检查是否有认证或连接错误
        if 'authentication failed' in recent_text.lower() or 'connection' in recent_text.lower():
            return {
                'status': 'error',
                'message': 'API认证或连接错误',
                'rate_limited': False,
                'last_success': False
            }

        # 默认运行状态
        return {
            'status': 'running',
            'message': '监控中',
            'rate_limited': False,
            'last_success': False
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'无法读取状态: {str(e)}',
            'rate_limited': False,
            'last_success': False
        }


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

        # 清理关键词文本：移除换行符和多余空格，确保是单行文本
        clean_keywords = {}
        for keyword, count in zip(keywords_df['keyword'], keywords_df['mentions']):
            # 将多行文本转为单行，移除换行符
            clean_keyword = ' '.join(str(keyword).split())
            clean_keywords[clean_keyword] = count

        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap='Blues',
            max_words=50,
            relative_scaling=0.5,
            min_font_size=12,
            collocations=False,
            prefer_horizontal=0.7  # 优先水平显示，避免多行问题
        ).generate_from_frequencies(clean_keywords)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
        plt.close(fig)  # 关闭图形释放内存

    except Exception as e:
        st.warning(f"词云暂时无法生成")
        st.info("💡 提示: 当前关键词数据较少或格式不兼容，请稍后刷新查看")


def format_time_ago(timestamp_str):
    """
    将时间戳转换为相对时间显示

    Args:
        timestamp_str: ISO格式时间戳字符串或Unix时间戳

    Returns:
        相对时间字符串 (如 "2小时前", "3天前")
    """
    if not timestamp_str:
        return ''

    try:
        # 尝试解析不同的时间格式
        if isinstance(timestamp_str, (int, float)):
            # Unix时间戳
            post_time = datetime.fromtimestamp(timestamp_str)
        elif 'T' in str(timestamp_str):
            # ISO格式 (如 "2025-01-10T15:30:00")
            post_time = datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
        else:
            # 尝试作为字符串解析
            post_time = datetime.fromisoformat(str(timestamp_str))

        now = datetime.now()
        delta = now - post_time

        # 计算相对时间
        if delta.days > 365:
            years = delta.days // 365
            return f"{years}年前"
        elif delta.days > 30:
            months = delta.days // 30
            return f"{months}月前"
        elif delta.days > 0:
            return f"{delta.days}天前"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours}小时前"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes}分钟前"
        else:
            return "刚刚"

    except Exception as e:
        # 解析失败,返回原始值
        return str(timestamp_str)


def render_reddit_card(row):
    """渲染Reddit风格卡片"""
    import html
    import pandas as pd

    # 安全获取字段，处理NaN和None
    source = str(row.get('source', 'Unknown'))
    author = str(row.get('author', 'Unknown'))

    # 获取subreddit，处理NaN
    subreddit = row.get('subreddit', '')
    if pd.isna(subreddit) or subreddit == 'nan':
        subreddit = ''
    else:
        subreddit = str(subreddit)

    # 获取并清理文本（移除HTML标签）
    text_raw = str(row.get('text', ''))
    # 1. 解码HTML实体
    text_clean = html.unescape(text_raw)
    # 2. 移除HTML标签
    text_clean = re.sub(r'<[^>]+>', '', text_clean)
    # 3. 移除多余空白
    text_clean = ' '.join(text_clean.split())
    # 4. 截取前200字符
    text = text_clean[:200]

    # 获取engagement，处理NaN
    engagement = row.get('engagement', 0)
    if pd.isna(engagement):
        engagement = 0
    else:
        engagement = int(engagement)

    created_at = row.get('created_at', '')

    # 根据来源设置badge样式
    if source == 'Reddit':
        badge_class = 'badge-reddit'
    elif source == 'Bluesky':
        badge_class = 'badge-bluesky'
    else:  # Twitter
        badge_class = 'badge-twitter'

    # 格式化时间戳
    time_display = format_time_ago(created_at)

    # 构建metadata字符串（安全拼接）
    meta_parts = []
    if subreddit:
        meta_parts.append(f'r/{subreddit}')
    meta_parts.append(f'by u/{author}')
    if time_display:
        meta_parts.append(time_display)
    meta_string = ' • '.join(meta_parts)

    card_html = f"""
    <div class="reddit-card">
        <div class="card-header">
            <span class="source-badge {badge_class}">{source}</span>
            <span class="card-meta">{meta_string}</span>
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

        # Bluesky状态（动态检查）
        bluesky_status = check_bluesky_collector_status()

        if bluesky_status['status'] == 'running':
            st.markdown("- 🔵 **Bluesky**: ✅ 正常运行")
            st.caption(f"   📡 {bluesky_status['message']}")
        elif bluesky_status['status'] == 'error':
            st.markdown("- 🔵 **Bluesky**: ❌ 出现错误")
            st.caption(f"   {bluesky_status['message']}")
        elif bluesky_status['status'] == 'idle':
            st.markdown("- 🔵 **Bluesky**: ⏸️ 未启动")
            st.caption(f"   {bluesky_status['message']}")
        else:
            st.markdown("- 🔵 **Bluesky**: ❓ 状态未知")

        # Reddit状态（动态检查）
        reddit_status = check_reddit_collector_status()

        if reddit_status['status'] == 'limited':
            st.markdown("- 🤖 **Reddit**: ⚠️ Rate Limited")
            st.caption(f"   {reddit_status['message']}")
        elif reddit_status['status'] == 'running':
            st.markdown("- 🤖 **Reddit**: ✅ 正常运行")
            st.caption("   📡 采集频率: 120秒/次")
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

        # === 筛选器控制 ===
        col_filter1, col_filter2, col_filter3 = st.columns(3)

        with col_filter1:
            # 日期筛选
            date_filter = st.selectbox(
                "📅 时间范围",
                ["所有", "今天", "昨天", "本周", "本月"],
                index=0
            )

        with col_filter2:
            # 来源筛选
            source_filter = st.selectbox(
                "📡 来源",
                ["所有"] + list(df['source'].unique()) if 'source' in df.columns else ["所有"],
                index=0
            )

        with col_filter3:
            # 排序选项
            sort_by = st.selectbox(
                "📊 排序",
                ["最新", "最热", "参与度最高"],
                index=0
            )

        # Subreddit筛选 (仅当有Reddit数据时显示)
        if 'subreddit' in df.columns:
            subreddits = df[df['subreddit'].notna()]['subreddit'].unique()
            if len(subreddits) > 0:
                selected_subreddits = st.multiselect(
                    "🔍 Subreddit筛选",
                    options=subreddits,
                    default=None,
                    placeholder="选择subreddit (可多选)"
                )
            else:
                selected_subreddits = []
        else:
            selected_subreddits = []

        st.markdown("---")

        # === 应用筛选条件 ===
        filtered_df = df.copy()

        # 日期筛选
        if 'created_at' in df.columns and date_filter != "所有":
            # 先统一转换时间格式，支持多种格式（ISO8601, Unix timestamp等）
            # utc=True 处理带时区的时间，errors='coerce' 将无效值转为 NaT
            filtered_df['created_at_parsed'] = pd.to_datetime(
                filtered_df['created_at'],
                utc=True,
                errors='coerce'
            )

            now = datetime.now()
            if date_filter == "今天":
                filtered_df = filtered_df[
                    filtered_df['created_at_parsed'].dt.tz_localize(None).dt.date == now.date()
                ]
            elif date_filter == "昨天":
                yesterday = now - timedelta(days=1)
                filtered_df = filtered_df[
                    filtered_df['created_at_parsed'].dt.tz_localize(None).dt.date == yesterday.date()
                ]
            elif date_filter == "本周":
                week_ago = now - timedelta(days=7)
                filtered_df = filtered_df[
                    filtered_df['created_at_parsed'].dt.tz_localize(None) >= week_ago
                ]
            elif date_filter == "本月":
                month_ago = now - timedelta(days=30)
                filtered_df = filtered_df[
                    filtered_df['created_at_parsed'].dt.tz_localize(None) >= month_ago
                ]

            # 移除临时列
            filtered_df = filtered_df.drop('created_at_parsed', axis=1)

        # 来源筛选
        if source_filter != "所有":
            filtered_df = filtered_df[filtered_df['source'] == source_filter]

        # Subreddit筛选
        if selected_subreddits:
            filtered_df = filtered_df[filtered_df['subreddit'].isin(selected_subreddits)]

        # 排序
        if 'created_at' in filtered_df.columns:
            if sort_by == "最新":
                # 转换时间格式后排序，确保正确处理各种时间格式
                filtered_df['_sort_time'] = pd.to_datetime(
                    filtered_df['created_at'],
                    utc=True,
                    errors='coerce'
                )
                filtered_df = filtered_df.sort_values('_sort_time', ascending=False)
                filtered_df = filtered_df.drop('_sort_time', axis=1)
            elif sort_by == "最热" or sort_by == "参与度最高":
                filtered_df = filtered_df.sort_values('engagement', ascending=False)
        else:
            if sort_by == "最热" or sort_by == "参与度最高":
                filtered_df = filtered_df.sort_values('engagement', ascending=False)

        # 限制显示数量
        filtered_df = filtered_df.head(50)

        # === 按日期分组显示 ===
        if len(filtered_df) == 0:
            st.info("🔍 没有找到符合条件的帖子")
        else:
            st.caption(f"📊 找到 {len(filtered_df)} 条帖子")

            # 按日期分组
            if 'created_at' in filtered_df.columns:
                # 统一转换时间格式，支持带时区的时间
                filtered_df['date'] = pd.to_datetime(
                    filtered_df['created_at'],
                    utc=True,
                    errors='coerce'
                ).dt.tz_localize(None).dt.date
                grouped = filtered_df.groupby('date')

                for date, group in grouped:
                    # 计算相对日期
                    today = datetime.now().date()
                    if date == today:
                        date_label = "今天"
                    elif date == today - timedelta(days=1):
                        date_label = "昨天"
                    elif date >= today - timedelta(days=7):
                        days_ago = (today - date).days
                        date_label = f"{days_ago}天前"
                    else:
                        date_label = date.strftime("%Y-%m-%d")

                    # 显示日期分组头部
                    st.markdown(f"### 📅 {date_label} ({len(group)} 条)")

                    # 渲染该日期的所有卡片
                    for idx, row in group.iterrows():
                        st.markdown(render_reddit_card(row), unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
            else:
                # 如果没有时间字段，直接显示
                for idx, row in filtered_df.iterrows():
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
