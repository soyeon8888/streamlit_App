import re
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from konlpy.tag import Okt
from googleapiclient.discovery import build

# Page Configuration
st.set_page_config(page_title="유튜브 댓글 분석기", layout="wide")

# 1. YouTube API 연결 (Secrets 활용)
@st.cache_resource
def get_youtube_client():
    try:
        api_key = st.secrets["YOUTUBE_API_KEY"]
        return build('youtube', 'v3', developerKey=api_key)
    except Exception as e:
        st.error("Streamlit Secrets에서 YOUTUBE_API_KEY를 찾을 수 없거나 올바르지 않습니다.")
        st.stop()

youtube = get_youtube_client()

# 2. YouTube URL에서 Video ID 추출
def extract_video_id(url):
    pattern = r'(?:v=|\/([0-9A-Za-z_-]{11}).*|maybe\?v=|^([0-9A-Za-z_-]{11})$)'
    match = re.search(pattern, url)
    if match:
        return match.group(1) or match.group(2)
    return None

# 3. 댓글 수집 함수
def get_comments(video_id, max_comments):
    comments_data = []
    next_page_token = None
    
    while len(comments_data) < max_comments:
        fetch_count = min(100, max_comments - len(comments_data))
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=fetch_count,
            pageToken=next_page_token,
            order="time"
        )
        response = request.execute()
        
        for item in response.get('items', []):
            snippet = item['snippet']['topLevelComment']['snippet']
            comments_data.append({
                'author': snippet['authorDisplayName'],
                'comment': snippet['textOriginal'],
                'published_at': snippet['publishedAt'],
                'like_count': snippet['likeCount']
            })
            
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
            
    df = pd.DataFrame(comments_data)
    if not df.empty:
        df['published_at'] = pd.to_datetime(df['published_at'])
    return df

# 4. 워드클라우드 생성 함수 (한글 형태소 분석)
def create_wordcloud(text_data, font_path='NanumGothic.ttf'):
    okt = Okt()
    nouns_list = []
    
    for text in text_data:
        # 단어 길이가 2자 이상인 명사만 추출
        nouns = okt.nouns(text)
        nouns = [n for n in nouns if len(n) > 1]
        nouns_list.extend(nouns)
        
    all_words = ' '.join(nouns_list)
    
    if not all_words.strip():
        return None
        
    try:
        wc = WordCloud(
            font_path=font_path,
            background_color='white',
            width=800,
            height=500,
            max_words=100
        ).generate(all_words)
        return wc
    except Exception as e:
        st.warning(f"폰트 로드 실패 ({e}). GitHub에 'NanumGothic.ttf' 파일이 있는지 확인해 주세요.")
        return None

# UI 화면 구성
st.title("📹 유튜브 댓글 종합 분석기")
st.caption("영상 URL을 입력하고 댓글 작성 추이, 반응도, 키워드를 한눈에 분석해 보세요.")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 분석 설정")
    video_url = st.text_input("유튜브 영상 URL 입력", placeholder="https://www.youtube.com/watch?v=...")
    max_count = st.slider("수집할 댓글 개수", min_value=10, max_value=1000, value=200, step=10)
    analyze_btn = st.button("댓글 분석 시작")

# 메인 실행 로직
if analyze_btn:
    if not video_url:
        st.warning("유튜브 URL을 입력해 주세요.")
    else:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.error("유효하지 않은 유튜브 URL입니다.")
        else:
            # 1. 영상 임베드 표시
            st.subheader("📺 분석 대상 영상")
            st.video(f"https://www.youtube.com/watch?v={video_id}")
            
            # 2. 댓글 데이터 로드
            with st.spinner("댓글 데이터를 수집하는 중..."):
                df = get_comments(video_id, max_count)
                
            if df.empty:
                st.info("댓글이 없거나 댓글 수집을 활성화할 수 없는 영상입니다.")
            else:
                st.success(f"총 {len(df)}개의 댓글을 성공적으로 수집했습니다!")
                
                #탭 구성
                tab1, tab2, tab3, tab4 = st.tabs(["📈 시간대별 작성 추이", "👍 댓글 반응도 Analysis", "☁️ 한글 워드클라우드", "📋 원본 데이터"])
                
                # Tab 1: 시간대별 작성 추이
                with tab1:
                    st.markdown("### 시간 흐름에 따른 댓글 작성량")
                    df_time = df.set_index('published_at').resample('D').size().reset_index(name='count')
                    fig_time = px.line(df_time, x='published_at', y='count', 
                                       labels={'published_at': '날짜', 'count': '댓글 수'},
                                       markers=True)
                    st.plotly_chart(fig_time, use_container_width=True)
                
                # Tab 2: 댓글 반응도 (좋아요 수 분포)
                with tab2:
                    st.markdown("### 가장 반응이 좋았던 상위 댓글 Top 5")
                    top_likes = df.sort_values(by='like_count', ascending=False).head(5)
                    for idx, row in top_likes.iterrows():
                        st.info(f"👍 **좋아요 {row['like_count']}개** | 작성자: {row['author']}\n\n{row['comment']}")
                    
                    st.markdown("---")
                    st.markdown("### 댓글 좋아요 수 분포")
                    fig_like = px.histogram(df, x='like_count', nbins=20, 
                                            labels={'like_count': '좋아요 수'},
                                            title="좋아요 분포 현황")
                    st.plotly_chart(fig_like, use_container_width=True)
                
                # Tab 3: 한글 워드클라우드
                with tab3:
                    st.markdown("### 주요 키워드 워드클라우드")
                    with st.spinner("한글 형태소를 분석하여 워드클라우드를 생성 중..."):
                        wc = create_wordcloud(df['comment'])
                        if wc:
                            fig, ax = plt.subplots(figsize=(10, 6))
                            ax.imshow(wc, interpolation='bilinear')
                            ax.axis('off')
                            st.pyplot(fig)
                        else:
                            st.warning("워드클라우드를 생성할 충분한 명사 키워드가 없습니다.")
                
                # Tab 4: 원본 데이터
                with tab4:
                    st.dataframe(df[['author', 'comment', 'like_count', 'published_at']])
