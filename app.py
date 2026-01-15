import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta
import random

# 1. 설정 및 노션 연결
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

# 페이지 설정 (다크모드 지향 디자인)
st.set_page_config(page_title="Sungchan Archive", layout="wide")

# [디자인] 파스텔 다크 모드 스타일 CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto+Sans+KR', sans-serif; background-color: #1e1e2e; color: #cdd6f4; }
    .stApp { background: linear-gradient(135deg, #1e1e2e 0%, #181825 100%); }
    [data-testid="stImage"] img { border-radius: 15px; transition: transform 0.3s ease; cursor: pointer; aspect-ratio: 1/1; object-fit: cover; border: 2px solid #313244; }
    [data-testid="stImage"] img:hover { transform: scale(1.05); border-color: #89b4fa; }
    .main-title { font-size: 3rem; font-weight: 700; text-align: center; color: #89b4fa; margin-bottom: 0px; }
    .sub-title { text-align: center; color: #9399b2; margin-bottom: 30px; }
    div.stButton > button { width: 100%; border-radius: 12px; background-color: #313244; color: white; border: none; height: 50px; font-weight: bold; }
    div.stButton > button:hover { background-color: #45475a; border: 1px solid #89b4fa; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=600)
def get_data():
    img_data = []
    try:
        results = notion.databases.query(database_id=DATABASE_ID).get("results")
        for page in results:
            page_id = page["id"]
            props = page.get('properties', {})
            date_str = props.get('날짜', {}).get('date', {}).get('start') or "날짜미상"
            # 태그 가져오기
            tag_info = props.get('태그', {}).get('multi_select', [])
            tags = [t['name'] for t in tag_info]
            
            blocks = notion.blocks.children.list(block_id=page_id).get("results")
            for block in blocks:
                if block["type"] == "image":
                    img_block = block["image"]
                    url = img_block.get('file', {}).get('url') or img_block.get('external', {}).get('url')
                    if url: img_data.append({"url": url, "date": date_str, "tags": tags})
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
    return img_data

st.markdown("<h1 class='main-title'>Archive</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>(  •  ³  •  ) 성찬이의 모든 순간을 기록합니다</p>", unsafe_allow_html=True)

data = get_data()

# 사이드바: 필터 및 랜덤 기능
with st.sidebar:
    st.header("⚙️ Filter & Menu")
    if st.button("🎲 오늘의 성찬 (Random)"):
        st.session_state.random_img = random.choice(data)['url'] if data else None
    
    all_tags = sorted(list(set([tag for item in data for tag in item['tags']])))
    selected_tag = st.selectbox("🏷️ 카테고리 필터", ["전체"] + all_tags)

# 1. 랜덤 이미지 팝업 (가장 상단)
if "random_img" in st.session_state and st.session_state.random_img:
    st.info("🎲 오늘의 랜덤 성찬!")
    st.image(st.session_state.random_img, use_container_width=True)
    if st.button("닫기"):
        st.session_state.random_img = None
        st.rerun()

# 2. 달력 필터
state = calendar(options={"contentHeight": 350, "selectable": True})

# 3. 사진 표시 로직
display_data = data

# 태그 필터 적용
if selected_tag != "전체":
    display_data = [d for d in display_data if selected_tag in d['tags']]

# 날짜 필터 적용
title_text = f"🖼️ {selected_tag} 사진"
if state.get("callback") == "dateClick":
    click_date = (datetime.strptime(state["dateClick"]["date"].split("T")[0], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    display_data = [d for d in display_data if d['date'] == click_date]
    title_text = f"📅 {click_date} 사진"

st.markdown(f"### {title_text} ({len(display_data)}장)")

# 4. 바둑판 그리드 (라이트박스 효과 포함)
if display_data:
    cols = st.columns(3)
    for idx, item in enumerate(display_data):
        with cols[idx % 3]:
            # 캡션에 날짜 표시
            st.image(item['url'], caption=item['date'] if selected_tag != "전체" else "", use_container_width=True)
else:
    st.warning("일치하는 사진이 없습니다.")
