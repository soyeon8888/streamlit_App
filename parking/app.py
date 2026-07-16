import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import plotly.express as px

st.set_page_config(
    page_title="서울 공영주차장 정보",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 서울 공영주차장 정보 시스템")

uploaded_file = st.sidebar.file_uploader(
    "CSV 업로드",
    type=["csv"]
)

if uploaded_file is None:
    st.info("공영주차장 CSV를 업로드하세요.")
    st.stop()

# -----------------------
# CSV 읽기
# -----------------------

try:
    df = pd.read_csv(uploaded_file, encoding="utf-8")
except:
    try:
        df = pd.read_csv(uploaded_file, encoding="cp949")
    except:
        df = pd.read_csv(uploaded_file)

# -----------------------
# 컬럼 자동 변경
# -----------------------

rename = {}

for c in df.columns:

    if "주차장" in c:
        rename[c] = "주차장명"

    elif "주소" in c:
        rename[c] = "주소"

    elif "자치구" in c:
        rename[c] = "자치구"

    elif "요금" in c and "기본" in c:
        rename[c] = "기본요금"

    elif "무료" in c:
        rename[c] = "무료"

    elif "주말" in c:
        rename[c] = "주말운영"

    elif "운영시간" in c:
        rename[c] = "운영시간"

df.rename(columns=rename, inplace=True)

# -----------------------
# 검색
# -----------------------

st.sidebar.header("검색")

keyword = st.sidebar.text_input("주차장 검색")

if "자치구" in df.columns:

    gu = st.sidebar.selectbox(
        "자치구",
        ["전체"] + sorted(df["자치구"].dropna().unique().tolist())
    )

else:
    gu = "전체"

free_only = st.sidebar.checkbox("무료만")

weekend_only = st.sidebar.checkbox("주말운영")

# -----------------------
# 필터
# -----------------------

result = df.copy()

if keyword != "" and "주차장명" in result.columns:

    result = result[
        result["주차장명"].astype(str).str.contains(keyword)
    ]

if gu != "전체":

    result = result[
        result["자치구"] == gu
    ]

if free_only and "무료" in result.columns:

    result = result[
        result["무료"].astype(str).isin(
            ["Y","예","무료","TRUE","True"]
        )
    ]

if weekend_only and "주말운영" in result.columns:

    result = result[
        result["주말운영"].astype(str).isin(
            ["Y","운영","예"]
        )
    ]

st.success(f"{len(result)}개의 주차장")

# -----------------------
# 통계
# -----------------------

c1,c2,c3,c4 = st.columns(4)

c1.metric("검색결과", len(result))

if "기본요금" in result.columns:

    result["기본요금"] = pd.to_numeric(
        result["기본요금"],
        errors="coerce"
    )

    c2.metric(
        "평균요금",
        f"{int(result['기본요금'].mean()):,}원"
    )

    c3.metric(
        "최저요금",
        f"{int(result['기본요금'].min()):,}원"
    )

if "무료" in result.columns:

    c4.metric(
        "무료주차장",
        len(
            result[
                result["무료"].astype(str).isin(
                    ["Y","무료","예"]
                )
            ]
        )
    )

# -----------------------
# 좌표 생성
# -----------------------

if "위도" not in result.columns:

    geo = Nominatim(user_agent="parking")

    geocode = RateLimiter(
        geo.geocode,
        min_delay_seconds=1
    )

    lat = []
    lon = []

    with st.spinner("주소를 좌표로 변환중..."):

        for addr in result["주소"]:

            try:

                loc = geocode(addr)

                if loc:

                    lat.append(loc.latitude)
                    lon.append(loc.longitude)

                else:

                    lat.append(None)
                    lon.append(None)

            except:

                lat.append(None)
                lon.append(None)

    result["위도"] = lat
    result["경도"] = lon

result = result.dropna(
    subset=["위도","경도"]
)

# -----------------------
# 지도
# -----------------------

m = folium.Map(
    location=[37.5665,126.9780],
    zoom_start=11
)

for _,row in result.iterrows():

    color="blue"

    if "무료" in row:

        if str(row["무료"]) in ["Y","무료","예"]:

            color="green"

    elif "주말운영" in row:

        if str(row["주말운영"]) in ["Y","운영","예"]:

            color="orange"

    text = f"""
<b>{row['주차장명']}</b><br>

주소 : {row['주소']}<br>
    if "기본요금" in row:
        text += f"💰 기본요금 : {row['기본요금']}원<br>"

    if "무료" in row:
        text += f"🆓 무료 : {row['무료']}<br>"

    if "주말운영" in row:
        text += f"📅 주말운영 : {row['주말운영']}<br>"

    if "운영시간" in row:
        text += f"🕒 운영시간 : {row['운영시간']}<br>"

    folium.CircleMarker(
        location=[row["위도"], row["경도"]],
        radius=7,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.9,
        tooltip=text,
        popup=text
    ).add_to(m)

st.subheader("🗺️ 공영주차장 지도")

st_folium(
    m,
    width=None,
    height=700
)

# -----------------------
# 추천
# -----------------------

st.divider()

st.subheader("🏆 가장 저렴한 공영주차장")

if "기본요금" in result.columns:

    recommend = result.sort_values("기본요금").head(5)

    st.dataframe(
        recommend[
            ["주차장명","자치구","기본요금","주소"]
        ],
        use_container_width=True
    )

# -----------------------
# 그래프
# -----------------------

if "기본요금" in result.columns:

    st.divider()

    st.subheader("📊 요금 분포")

    fig = px.histogram(
        result,
        x="기본요금",
        nbins=30
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

if "자치구" in result.columns and "기본요금" in result.columns:

    st.subheader("🏙 자치구 평균요금")

    avg = (
        result
        .groupby("자치구")["기본요금"]
        .mean()
        .reset_index()
    )

    fig = px.bar(
        avg,
        x="자치구",
        y="기본요금",
        color="기본요금"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# -----------------------
# CSV 다운로드
# -----------------------

csv = result.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    "📥 결과 CSV 다운로드",
    csv,
    "parking_result.csv",
    "text/csv"
)

# -----------------------
# 원본 데이터
# -----------------------

with st.expander("원본 데이터 보기"):

    st.dataframe(
        result,
        use_container_width=True
    )
