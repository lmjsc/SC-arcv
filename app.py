import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# 1. 설정 및 노션 연결
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Archive", layout="wide") # 넓게 보기 설정

# CSS: 바둑판 이미지 스타일 및 모바일 대응
st.markdown("""
    <style>
    [data-testid="stImage"] img {
        border-radius: 10px;
        aspect-ratio: 1 / 1;
        object-fit: cover;
    }
    .date-title {
        font-size: 24px;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 10px;
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
            date_info = props.get('날짜', {}).get('date')
            date_str = date_info.get('start') if date_info else "날짜없음"
            
            blocks = notion.blocks.children.list(block_id=page_id).get("results")
            for block in blocks:
                if block["type"] == "image":
                    img_block = block["image"]
                    url = img_block.get('file', {}).get('url') or img_block.get('external', {}).get('url')
                    if url: img_data.append({"url": url, "date": date_str})
    except Exception as e:
        st.error(f"로드 실패: {e}")
    return img_data

st.title("Archive (  •  ³  •  )")

with st.spinner('사진첩 정리 중...'):
    data = get_data()

# 달력 표시 (상단)
state = calendar(options={"contentHeight": 350, "selectable": True})

# 사진을 그리드로 보여주는 함수
def display_gallery(photos, title):
    st.markdown(f"<div class='date-title'>{title}</div>", unsafe_allow_html=True)
    if not photos:
        st.info("표시할 사진이 없습니다.")
        return

    # 한 줄에 3장씩 배치 (모바일/PC 공통)
    cols = st.columns(3)
    for idx, photo_url in enumerate(photos):
        with cols[idx % 3]:
            st.image(photo_url, use_container_width=True)

# 메인 로직
if state.get("callback") == "dateClick":
    # 1. 특정 날짜 클릭 시
    click_raw = state["dateClick"]["date"].split("T")[0]
    selected_date = (datetime.strptime(click_raw, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    
    filtered_imgs = [item['url'] for item in data if item['date'] == selected_date]
    display_gallery(filtered_imgs, f"📅 {selected_date} 사진 ({len(filtered_imgs)}장)")
    
    if st.button("전체 보기로 돌아가기"):
        st.rerun()
else:
    # 2. 아무것도 안 눌렀을 때 (전체 사진 바둑판)
    all_imgs = [item['url'] for item in data]
    display_gallery(all_imgs, f"🖼️ 전체 사진 ({len(all_imgs)}장)")
