import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# 페이지 기본 설정
st.set_page_config(
    page_title="공영주차장 정보 안내 서비스",
    page_icon="🚗",
    layout="wide"
)

# ----------------------------------------------------
# 1. 파일 업로드 및 데이터 로드 기능 (인코딩 우회 추가)
# ----------------------------------------------------
st.title("🚗 전국 공영주차장 정보 서비스")
st.markdown("전국의 공영주차장 위치를 확인하고 자치구별로 가장 저렴한 주차장을 찾아보세요!")

st.sidebar.header("📁 데이터 업로드")
uploaded_file = st.sidebar.file_uploader(
    "공영주차장 CSV 파일을 업로드하세요.", 
    type=["csv"]
)

df = None

# 사용자가 파일을 업로드한 경우
if uploaded_file is not None:
    try:
        # 다양한 한글 인코딩 대응 (euc-kr, cp949, utf-8, utf-8-sig 등 순차 시도)
        for encoding in ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']:
            try:
                df = pd.read_csv(uploaded_file, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        if df is not None:
            st.sidebar.success("성공적으로 업로드되었습니다!")
    except Exception as e:
        st.sidebar.error(f"파일을 읽는 중 에러가 발생했습니다: {e}")

# 파일 업로드가 없을 경우 주변에 있는 기존 CSV 파일 자동 탐색 및 기본 더미데이터 구성
if df is None:
    # 현재 폴더에 있는 csv 파일 리스트 검색
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if csv_files:
        target_file = csv_files[0]
        for encoding in ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']:
            try:
                df = pd.read_csv(target_file, encoding=encoding)
                st.sidebar.info(f"💡 현재 폴더의 `{target_file}` 파일을 자동으로 불러왔습니다.")
                break
            except Exception:
                continue

# 여전히 데이터가 없는 경우를 위한 내장 기본 샘플 데이터 제공
if df is None:
    default_data = {
        '주차장명': [
            '서울역 공영주차장', '용산구청 주차장', '강남역 공영주차장', 
            '홍대 서측 공영주차장', '마포유수지 주차장', '신촌역 공영주차장',
            '여의도 한강공원 주차장', '영등포역 주차장', '가산디지털단지역 주차장'
        ],
        '자치구': ['중구', '용산구', '강남구', '마포구', '마포구', '서대문구', '영등포구', '영등포구', '금천구'],
        '주소': [
            '서울특별시 중구 한강대로 405', '서울특별시 용산구 백범로 329', '서울특별시 강남구 강남대로 396', 
            '서울특별시 마포구 어울마당로 120', '서울특별시 마포구 마포대로1길 9', '서울특별시 서대문구 신촌역로 30',
            '서울특별시 영등포구 여의동로 330', '서울특별시 영등포구 경인로 846', '서울특별시 금천구 벚꽃로 309'
        ],
        '위도': [37.5546, 37.5326, 37.4980, 37.5542, 37.5392, 37.5598, 37.5284, 37.5156, 37.4812],
        '경도': [126.9706, 126.9904, 127.0276, 126.9218, 126.9416, 126.9422, 126.9332, 126.9073, 126.8827],
        '기본요금': [3000, 1000, 4000, 2000, 1500, 1800, 2000, 2500, 1200],
        '무료여부': ['유료', '유료', '유료', '유료', '무료', '유료', '유료', '유료', '무료'],
        '주말운영': ['운영', '운영', '미운영', '운영', '운영', '미운영', '운영', '운영', '운영'],
        '상세설명': [
            '평일/주말 상시 운영', '구청 이용객 할인', '강남역 2번 출구 인근', 
            '홍대 걷고싶은거리 인근', '마포역 인근 무료개방 시간 있음', '신촌 로터리 인근',
            '한강공원 이용객 다수', '영등포역 후문 인근', '디지털단지 직장인 전용'
        ]
    }
    df = pd.DataFrame(default_data)
    st.sidebar.warning("⚠️ CSV 파일이 로드되지 않아 샘플 데이터를 표시합니다. 파일을 업로드해 주세요.")

# ----------------------------------------------------
# 2. 업로드된 CSV의 열 이름 표준화 (사용자 파일 맞춤형 유연한 맵핑)
# ----------------------------------------------------
# 사용자의 파일 내 컬럼명이 한글/영문 등이 다르게 들어가 있어도 자동으로 매칭되도록 규칙을 정의합니다.
column_mapping = {
    '주차장명': '주차장명', '주차장 이름': '주차장명', '명칭': '주차장명', '이름': '주차장명', 'parking_name': '주차장명',
    '자치구': '자치구', '구': '자치구', '시군구': '자치구', '구명': '자치구', 'district': '자치구',
    '주소': '주소', '소재지도로명주소': '주소', '소재지주소': '주소', '도로명주소': '주소', '지번주소': '주소', 'address': '주소',
    '위도': '위도', 'latitude': '위도', 'lat': '위도', 'Y좌표': '위도', 'y': '위도',
    '경도': '경도', 'longitude': '경도', 'lng': '경도', 'X좌표': '경도', 'x': '경도',
    '기본요금': '기본요금', '요금': '기본요금', '주차요금': '기본요금', '기본 주차 요금': '기본요금', 'price': '기본요금', 'fee': '기본요금',
    '무료여부': '무료여부', '무료구분': '무료여부', '유무료': '무료여부', '무료': '무료여부', 'is_free': '무료여부',
    '주말운영': '주말운영', '주말운영여부': '주말운영', '주말': '주말운영', 'weekend': '주말운영'
}

# 공백 등을 포함한 매핑 규칙 적용 및 이름 표준화
renamed_cols = {}
for col in df.columns:
    clean_col = col.strip()
    if clean_col in column_mapping:
        renamed_cols[col] = column_mapping[clean_col]
df = df.rename(columns=renamed_cols)

# 필수 컬럼이 매핑 후에도 누락되었을 때의 기본 처리
# (이전 코드에서 이어집니다...)

# 필수 컬럼이 매핑 후에도 누락되었을 때의 기본 처리 및 기본값 할당
required_cols = ['주차장명', '자치구', '주소', '위도', '경도', '기본요금', '무료여부', '주말운영']
for col in required_cols:
    if col not in df.columns:
        if col == '주차장명':
            df[col] = "이름 없음 공영주차장"
        elif col == '자치구':
            df[col] = "기타 자치구"
        elif col == '주소':
            df[col] = "주소 정보 없음"
        elif col == '위도':
            df[col] = 37.5665  # 서울 중심부 위도 기본값
        elif col == '경도':
            df[col] = 126.9780 # 서울 중심부 경도 기본값
        elif col == '기본요금':
            df[col] = 0        # 요금 정보를 모르면 무료(0원) 취급
        elif col == '무료여부':
            df[col] = "유료"
        elif col == '주말운영':
            df[col] = "운영"

# 데이터 정제(Data Cleaning): 데이터 타입 맞춤 및 결측치 제거
df['위도'] = pd.to_numeric(df['위도'], errors='coerce').fillna(37.5665)
df['경도'] = pd.to_numeric(df['경도'], errors='coerce').fillna(126.9780)

# 요금 정보에 콤마(,)가 찍혀있거나 '무료' 등의 텍스트가 섞여 있어도 숫자로 파싱 처리
if df['기본요금'].dtype == object:
    df['기본요금'] = df['기본요금'].astype(str).str.replace(r'[^\d]', '', regex=True)
    df['기본요금'] = pd.to_numeric(df['기본요금'], errors='coerce').fillna(0).astype(int)
else:
    df['기본요금'] = df['기본요금'].fillna(0).astype(int)

# 텍스트 형태 통일화 (무료/유료, 주말 운영 등 빈칸 채우기)
df['무료여부'] = df['무료여부'].fillna('유료').astype(str).apply(lambda x: '무료' if '무료' in x or 'Free' in x or 'free' in x else '유료')
df['주말운영'] = df['주말운영'].fillna('운영').astype(str).apply(lambda x: '미운영' if '미운영' in x or '쉬는' in x or 'off' in x else '운영')

# ----------------------------------------------------
# 3. 사이드바 검색 및 필터링 기능
# ----------------------------------------------------
st.sidebar.header("🔍 검색 및 필터링")

# 1) 자치구 선택 (데이터 내 모든 고유 자치구 목록 추출)
borough_list = sorted(df['자치구'].astype(str).unique())
selected_borough = st.sidebar.selectbox("자치구를 선택하세요", borough_list)

# 2) 주차장명 직접 검색
search_query = st.sidebar.text_input("주차장 이름 검색")

# 3) 편의 필터링 옵션
filter_free = st.sidebar.checkbox("무료 주차장만 보기")
filter_weekend = st.sidebar.checkbox("주말에도 운영하는 곳만 보기")

# 필터링 적용 단계
filtered_df = df[df['자치구'] == selected_borough]

if search_query:
    filtered_df = filtered_df[filtered_df['주차장명'].str.contains(search_query, case=False, na=False)]

if filter_free:
    filtered_df = filtered_df[filtered_df['무료여부'] == '무료']

if filter_weekend:
    filtered_df = filtered_df[filtered_df['주말운영'] == '운영']

# ----------------------------------------------------
# 4. 자치구별 통계 및 최저가 주차장 자동 판별
# ----------------------------------------------------
st.subheader(f"📍 {selected_borough} 내 공영주차장 분석 및 추천")

if not filtered_df.empty:
    # 해당 자치구 내 요금이 가장 싼 곳 검색 (동일 최저가가 있을 시 첫 번째 우선 선택)
    cheapest_idx = filtered_df['기본요금'].idxmin()
    cheapest_parking = filtered_df.loc[cheapest_idx]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="🏆 자치구 내 최저가 주차장", 
            value=cheapest_parking['주차장명'], 
            delta=f"{cheapest_parking['기본요금']:,} 원"
        )
    with col2:
        st.metric(
            label="💰 평균 기본 요금", 
            value=f"{int(filtered_df['기본요금'].mean()):,} 원"
        )
    with col3:
        st.metric(
            label="🚗 검색된 주차장 수", 
            value=f"{len(filtered_df)} 개"
        )
        
    # 최저가 추천 주차장 안내 박스
    st.info(
        f"**💡 {selected_borough}에서 가장 저렴한 주차장은 [{cheapest_parking['주차장명']}] 입니다!** \n"
        f"* **주소:** {cheapest_parking['주소']} \n"
        f"* **요금 정보:** {cheapest_parking['기본요금']:,}원 (무료 여부: {cheapest_parking['무료여부']}) \n"
        f"* **주말 운영:** {cheapest_parking['주말운영']} \n"
        f"* **기타 정보:** {cheapest_parking.get('상세설명', '제공된 설명이 없습니다.')}"
    )
else:
    st.error("현재 필터링 조건에 일치하는 주차장이 존재하지 않습니다. 검색어나 필터를 조정해 주세요.")

# ----------------------------------------------------
# 5. 지도 위치 시각화 (Folium Map)
# ----------------------------------------------------
st.subheader("🗺️ 지도 위치 시각화")
st.caption("마커에 마우스를 대면 주소와 요금이 보이고, 마커를 클릭하면 더 상세한 운영 안내 정보가 표시됩니다.")

if not filtered_df.empty:
    # 지도의 중심점을 필터링된 주차장들의 평균 위도/경도로 설정
    start_lat = filtered_df['위도'].mean()
    start_lng = filtered_df['경도'].mean()
    
    # 지도 객체 생성 (기본 줌 레벨: 13)
    m = folium.Map(location=[start_lat, start_lng], zoom_start=13)
    
    # 각 주차장 위치에 마커 추가
    for idx, row in filtered_df.iterrows():
        # 마우스를 가져다 댔을 때 보여줄 간단 툴팁 (Hover)
        tooltip_content = f"""
        <strong>{row['주차장명']}</strong><br>
        📍 주소: {row['주소']}<br>
        💵 요금: {row['기본요금']:,}원
        """
        
        # 마커 클릭 시 나타날 세부 정보 팝업 (Popup)
        popup_content = f"""
        <div style="font-family: 'Malgun Gothic', sans-serif; width: 240px; line-height:1.5;">
            <h4 style="margin:0 0 5px 0; color:#1f77b4;">{row['주차장명']}</h4>
            <hr style="margin:5px 0;">
            <b>📍 주소:</b> {row['주소']}<br>
            <b>💵 기본요금:</b> {row['기본요금']:,}원 ({row['무료여부']})<br>
            <b>📅 주말운영:</b> {row['주말운영']}<br>
            <b>📝 비고:</b> {row.get('상세설명', '내용 없음')}<br>
        </div>
        """
        
        # 필터링 대상 중 최저가 주차장인 경우 초록색 스타 마커로 강조 표현
        is_cheapest = (row['주차장명'] == cheapest_parking['주차장명'])
        marker_color = 'green' if is_cheapest else 'blue'
        icon_type = 'star' if is_cheapest else 'info-sign'
        
        folium.Marker(
            location=[row['위도'], row['경도']],
            tooltip=tooltip_content,
            popup=folium.Popup(popup_content, max_width=350),
            icon=folium.Icon(color=marker_color, icon=icon_type)
        ).add_to(m)
        
    # Streamlit 화면에 지도 렌더링
    st_folium(m, width=1200, height=500, returned_objects=[])
else:
    st.warning("지도상에 표기할 주차장 정보가 존재하지 않습니다.")

# ----------------------------------------------------
# 6. 원본 데이터 테이블 및 파일 다운로드 제공
# ----------------------------------------------------
st.markdown("---")
st.subheader("📊 필터링된 주차장 전체 데이터 현황")

# 스트리밋 인터랙티브 데이터프레임으로 표현
st.dataframe(filtered_df, use_container_width=True)

# 다운로드 기능 연동
if not filtered_df.empty:
    csv_data = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 필터링된 주차장 명단 CSV로 저장하기",
        data=csv_data,
        file_name=f"{selected_borough}_공영주차장_검색결과.csv",
        mime="text/csv"
    )
