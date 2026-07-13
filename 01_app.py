import streamlit as st
import random

st.set_page_config(
    page_title="🍴 오늘 뭐 먹지?",
    page_icon="🍙",
    layout="centered"
)

# ---------------- CSS ----------------

st.markdown("""
<style>

.stApp{
    background: linear-gradient(180deg,#FFF7E6,#FFEFD5);
}

h1{
    text-align:center;
    color:#FF6B6B;
}

.card{
    background:white;
    padding:20px;
    border-radius:25px;
    box-shadow:0 8px 20px rgba(0,0,0,0.15);
}

.menu{
    text-align:center;
    font-size:35px;
    color:#FF7F50;
    font-weight:bold;
}

.info{
    font-size:20px;
    color:#444;
}

.footer{
    text-align:center;
    color:gray;
}

</style>
""", unsafe_allow_html=True)

st.title("🍴 오늘 뭐 먹지?")
st.subheader("☁️ 날씨에 따라 메뉴를 추천해드려요!")

# ---------------- 메뉴 데이터 ----------------

foods = {

    "맑음":[
        {
            "name":"비빔밥",
            "image":"https://images.unsplash.com/photo-1604908177522-432b7b0f7e13?w=800",
            "cal":"650 kcal",
            "nut":"탄수화물 80g | 단백질 22g | 지방 18g"
        },
        {
            "name":"샐러드",
            "image":"https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800",
            "cal":"320 kcal",
            "nut":"탄수화물 20g | 단백질 18g | 지방 15g"
        }
    ],

    "비":[
        {
            "name":"김치전",
            "image":"https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800",
            "cal":"540 kcal",
            "nut":"탄수화물 55g | 단백질 12g | 지방 25g"
        },
        {
            "name":"칼국수",
            "image":"https://images.unsplash.com/photo-1617093727343-374698b1b08d?w=800",
            "cal":"620 kcal",
            "nut":"탄수화물 90g | 단백질 18g | 지방 14g"
        }
    ],

    "눈":[
        {
            "name":"떡국",
            "image":"https://images.unsplash.com/photo-1512058564366-18510be2db19?w=800",
            "cal":"570 kcal",
            "nut":"탄수화물 78g | 단백질 20g | 지방 15g"
        }
    ],

    "흐림":[
        {
            "name":"돈까스",
            "image":"https://images.unsplash.com/photo-1544025162-d76694265947?w=800",
            "cal":"810 kcal",
            "nut":"탄수화물 65g | 단백질 35g | 지방 42g"
        }
    ],

    "더움":[
        {
            "name":"냉면",
            "image":"https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
            "cal":"480 kcal",
            "nut":"탄수화물 70g | 단백질 18g | 지방 8g"
        },
        {
            "name":"콩국수",
            "image":"https://images.unsplash.com/photo-1525755662778-989d0524087e?w=800",
            "cal":"560 kcal",
            "nut":"탄수화물 60g | 단백질 25g | 지방 18g"
        }
    ],

    "추움":[
        {
            "name":"부대찌개",
            "image":"https://images.unsplash.com/photo-1547592180-85f173990554?w=800",
            "cal":"720 kcal",
            "nut":"탄수화물 40g | 단백질 35g | 지방 38g"
        },
        {
            "name":"삼계탕",
            "image":"https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?w=800",
            "cal":"760 kcal",
            "nut":"탄수화물 30g | 단백질 45g | 지방 35g"
        }
    ]

}

# ---------------- 선택 ----------------

weather = st.selectbox(
    "🌤️ 오늘의 날씨를 선택하세요",
    list(foods.keys())
)

if st.button("🍽️ 메뉴 추천받기"):

    menu = random.choice(foods[weather])

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown(
        f'<p class="menu">🍜 {menu["name"]}</p>',
        unsafe_allow_html=True
    )

    st.image(menu["image"], use_container_width=True)

    st.markdown(
        f"""
        <div class="info">
        🔥 <b>칼로리</b><br>
        {menu["cal"]}<br><br>

        🥗 <b>영양소</b><br>
        {menu["nut"]}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.balloons()

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    "<p class='footer'>🐻 귀여운 날씨 메뉴 추천 앱</p>",
    unsafe_allow_html=True
)
