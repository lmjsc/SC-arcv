import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# 1. 설정 및 노션 연결
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Archive", layout="centered")

# [핵심] 중앙 집중형 레이아웃 CSS
st.markdown("""
    <style>
    /* 버튼과 숫자를 감싸는 상자를 중앙으로 모음 */
    .nav-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 20px;
        margin: 20px 0;
    }
    /* 버튼 크기 고정 및 텍스트 제거 대응 */
    .stButton button {
        width: 60px !important;
        height: 45px !important;
        border-radius: 12px !important;
        padding: 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    /* 숫자 텍스트 스타일 */
    .nav-text {
        font-size: 18px;
        font-weight: bold;
        min-width: 60px;
        text-align: center;
    }
    /* Streamlit 기본 컬럼 간격 무시 */
    [data-testid="stHorizontalBlock"] {
        justify-content: center !important;
        gap: 10px !important;
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
            date_str = date_info.get('start') if date_info else None
            blocks = notion.blocks.children.list(block_id=page_id).get("results")
            for block in blocks:
                if block["type"] == "image":
                    img_block = block["image"]
                    url = img_block.get('file', {}).get('url') or img_block.get('external', {}).get('url')
                    if url: img_data.append({"url": url, "date": date_str})
    except Exception as e:
        st.error(f"로드 실패: {e}")
    return img_data

st.title("Archive")
data = get_data()

state = calendar(options={"contentHeight": 350, "selectable": True})

if state.get("callback") == "dateClick":
    selected_date = state["dateClick"]["date"].split("T")[0]
    selected_date = (datetime.strptime(selected_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    
    st.markdown("---")
    filtered_imgs = [item['url'] for item in data if item['date'] == selected_date]
    
    if filtered_imgs:
        if f"idx_{selected_date}" not in st.session_state:
            st.session_state[f"idx_{selected_date}"] = 0
            
        curr = st.session_state[f"idx_{selected_date}"]
        total = len(filtered_imgs)

        # ⭐️ 레이아웃: [ ⬅️ ]  1 / 30  [ ➡️ ] 형태로 중앙 정렬
        # columns 비율을 조절하여 버튼들이 중앙으로 모이게 설정
        c1, c2, c3, c4, c5 = st.columns([2, 1, 2, 1, 2])
        
        with c2:
            if st.button("⬅️", key="p_btn"):
                st.session_state[f"idx_{selected_date}"] = (curr - 1) % total
                st.rerun()
        with c3:
            st.markdown(f"<div class='nav-text' style='line-height:45px;'>{curr + 1} / {total}</div>", unsafe_allow_html=True)
        with c4:
            if st.button("➡️", key="n_btn"):
                st.session_state[f"idx_{selected_date}"] = (curr + 1) % total
                st.rerun()

        st.image(filtered_imgs[st.session_state[f"idx_{selected_date}"]], use_container_width=True)
    else:
        st.info(f"{selected_date} 사진이 없습니다.")
