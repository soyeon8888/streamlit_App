import streamlit as st
import feedparser
from urllib.parse import quote
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer

# 페이지 기본 설정
st.set_page_config(page_title="API 키 없는 뉴스 요약기", layout="wide", page_icon="📰")

# 텍스트 추출 및 요약 함수 (API 키 필요 없음)
def summarize_text(text, sentence_count=3):
    if not text or len(text) < 50:
        return "요약할 본문 내용이 충분하지 않습니다."
    
    try:
        # sumy 라이브러리를 사용한 문장 알고리즘 요약
        parser = PlaintextParser.from_string(text, Tokenizer("korean"))
        summarizer = LexRankSummarizer()
        summary = summarizer(parser.document, sentence_count)
        
        result = [f"• {str(sentence)}" for sentence in summary]
        return "\n".join(result) if result else text
    except Exception:
        # 한국어 토크나이저 예외 시 간단한 줄바꿈 처리
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 10]
        return "\n".join([f"• {s}." for s in sentences[:3]])

# Google News RSS 수집 함수
def get_google_news(keyword):
    encoded_keyword = quote(keyword)
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)
    return feed.entries

# UI 화면 구성
st.title("📰 실시간 뉴스 3줄 요약기")
st.caption("회원가입이나 API 키 발급 없이 Google News RSS와 텍스트 분석 알고리즘으로 뉴스를 요약합니다.")

# 사이드바
with st.sidebar:
    st.header("🔍 검색 설정")
    keyword = st.text_input("뉴스 검색어", value="인공지능")
    news_count = st.slider("불러올 뉴스 개수", min_value=1, max_value=5, value=3)
    search_btn = st.button("뉴스 검색 & 요약")

# 실행 로직
if search_btn:
    if not keyword.strip():
        st.warning("검색어를 입력해 주세요.")
    else:
        with st.spinner(f"'{keyword}' 뉴스를 가져오는 중..."):
            articles = get_google_news(keyword)
            
            if not articles:
                st.info("검색 결과가 없습니다.")
            else:
                st.success(f"최신 뉴스 {min(news_count, len(articles))}개를 찾았습니다!")
                st.markdown("---")
                
                for idx, item in enumerate(articles[:news_count], 1):
                    title = item.title
                    link = item.link
                    published = getattr(item, 'published', '날짜 정보 없음')
                    snippet = getattr(item, 'summary', title)
                    
                    # 뉴스요약 수행
                    summary = summarize_text(snippet, sentence_count=3)
                    
                    # 결과 출력
                    st.subheader(f"{idx}. {title}")
                    st.caption(f"📅 작성일: {published} | [🔗 원문 보기]({link})")
                    
                    st.markdown("**📌 핵심 3줄 요약**")
                    st.info(summary)
                    st.markdown("---")
