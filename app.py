import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# 1. 설정 및 노션 연결
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

# 페이지 설정
st.set_page_config(page_title="Archive", layout="wide")

# [디자인] 글자색과 배경색 대비를 명확하게 수정
st.markdown("""
    <style>
    /* 기본 배경: 어두운 네이비 / 글자: 연한 회색(밝음) */
    .stApp {
        background-color: #1a1b26;
        color: #a9b1d6;
    }
    /* 제목: 하늘색 */
    h1, h2, h3 {
        color: #7aa2f7 !important;
    }
    /* 사이드바 글자색 고정 */
    [data-testid="stSidebar"] {
        background-color: #24283b;
    }
    [data-testid="stSidebar"] .css-17l2qt2 {
        color: #cfc9c2;
    }
    /* 이미지 카드 스타일 */
    [data-testid="stImage"] img {
        border-radius: 12px;
        aspect-ratio: 1/1;
        object-fit: cover;
        border: 2px solid #414868;
    }
    /* 캡션 글자 잘 보이게 설정 */
    [data-testid="stImageCaption"] {
        color: #9ece6a !important;
        font-weight: bold;
    }
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
            
            # [수정] 노션 속성명을 '스케줄'로 변경
            schedule_info = props.get('스케줄', {}).get('multi_select', [])
            schedules = [s['name'] for s in schedule_info]
            
            blocks = notion.blocks.children.list(block_id=page_id).get("results")
            for block in blocks:
                if block["type"] == "image":
                    img_block = block["image"]
                    url = img_block.get('file', {}).get('url') or img_block.get('external', {}).get('url')
                    if url: img_data.append({"url": url, "date": date_str, "schedules": schedules})
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
    return img_data

st.title("Archive (  •  ³  •  )")

with st.spinner('로딩 중...'):
    data = get_data()

# 사이드바: 필터 기능
with st.sidebar:
    st.header("🔍 Filter")
    all_schedules = sorted(list(set([s for item in data for s in item['schedules']])))
    selected_schedule = st.selectbox("📅 스케줄별 보기", ["전체"] + all_schedules)

# 1. 달력 필터
state = calendar(options={"contentHeight": 350, "selectable": True})

# 2. 사진 표시 로직
display_data = data

# 스케줄 필터 적용
if selected_schedule != "전체":
    display_data = [d for d in display_data if selected_schedule in d['schedules']]

# 날짜 필터 적용
title_text = f"🖼️ {selected_schedule} 사진"
if state.get("callback") == "dateClick":
    click_date = (datetime.strptime(state["dateClick"]["date"].split("T")[0], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    display_data = [d for d in display_data if d['date'] == click_date]
    title_text = f"📅 {click_date} 사진"

st.markdown(f"### {title_text} ({len(display_data)}장)")

# 3. 바둑판 그리드
if display_data:
    cols = st.columns(3)
    for idx, item in enumerate(display_data):
        with cols[idx % 3]:
            # 사진 아래 날짜를 캡션으로 표시
            st.image(item['url'], caption=item['date'], use_container_width=True)
else:
    st.warning("해당 조건의 사진이 없습니다.")
