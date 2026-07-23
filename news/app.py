import re
import requests
import streamlit as st
from bs4 import BeautifulSoup
from google import genai

# Page Config
st.set_page_config(page_title="실시간 뉴스 3줄 요약기", layout="wide", page_icon="📰")

# 1. API 키 불러오기
try:
    NAVER_CLIENT_ID = st.secrets["NAVER_CLIENT_ID"]
    NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("Streamlit Secrets 설정에서 API 키들을 확인해 주세요.")
    st.stop()

# Gemini 클라이언트 초기화
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# HTML 태그 제거 함수
def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.replace(""", '"').replace("&", '&').replace("<", '<').replace(">", '>')

# 2. 네이버 뉴스 검색 API 호출
def search_naver_news(query, display=5):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {
        "query": query,
        "display": display,
        "sort": "sim" # sim: 유사도순, date: 날짜순
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        st.error(f"뉴스 검색 실패 (에러 코드: {response.status_code})")
        return []

# 3. 본문 크롤링 (네이버 뉴스 URL인 경우)
def get_article_body(link):
    try:
        if "news.naver.com" in link:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(link, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            # 네이버 뉴스 본문 아이디
            article_body = soup.find('article', id='dic_area')
            if article_body:
                return article_body.get_text(strip=True)
    except Exception:
        pass
    return None

# 4. Gemini AI 3줄 요약 함수
def summarize_text(title, description, full_body=None):
    text_to_summarize = full_body if full_body else f"제목: {title}\n요약문: {description}"
    
    prompt = f"""
    다음 뉴스 기사 내용을 바탕으로 핵심 내용을 딱 3줄로 알기 쉽게 요약해줘.
    
    [기사 내용]
    {text_to_summarize[:1500]}
    
    [작성 조건]
    1. 각 줄은 "• " 으로 시작할 것.
    2. 명확하고 읽기 편한 한국어 말투로 작성할 것.
    3. 과장이나 왜곡 없이 기사의 사실만 요약할 것.
    """
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"요약 생성 중 오류 발생: {e}"

# --- UI 레이아웃 ---
st.title("📰 실시간 이슈 뉴스 3줄 AI 요약기")
st.caption("관심 있는 키워드를 검색하면 최신 뉴스를 수집하여 Gemini AI가 핵심을 3줄로 요약해 드립니다.")

with st.sidebar:
    st.header("🔍 검색 설정")
    keyword = st.text_input("뉴스 검색어", value="인공지능")
    news_count = st.slider("불러올 뉴스 개수", min_value=1, max_value=10, value=3)
    search_btn = st.button("뉴스 검색 & 요약 실행")

if search_btn:
    if not keyword.strip():
        st.warning("검색어를 입력해 주세요.")
    else:
        with st.spinner(f"'{keyword}' 관련 뉴스를 검색하고 AI로 요약하는 중..."):
            news_items = search_naver_news(keyword, news_count)
            
            if not news_items:
                st.info("검색 결과가 없습니다.")
            else:
                st.success(f"총 {len(news_items)}개의 뉴스를 가져왔습니다!")
                st.markdown("---")
                
                for idx, item in enumerate(news_items, 1):
                    title = clean_html(item['title'])
                    description = clean_html(item['description'])
                    link = item['link']
                    pub_date = item['pubDate']
                    
                    # 본문 스크래핑 시도
                    full_body = get_article_body(link)
                    
                    # AI 요약 생성
                    summary = summarize_text(title, description, full_body)
                    
                    # UI 카드 형태로 출력
                    with st.container():
                        st.subheader(f"{idx}. {title}")
                        st.caption(f"📅 작성일: {pub_date} | [🔗 원문 기사 보기]({link})")
                        
                        st.markdown("**🤖 AI 3줄 요약**")
                        st.info(summary)
                        st.markdown("---")
