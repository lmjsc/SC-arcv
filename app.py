import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# 1. 설정 및 노션 연결
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Archive", layout="centered")

# [핵심] 모바일에서 절대 줄바꿈 되지 않는 강제 가로 테이블 CSS
st.markdown("""
    <style>
    /* 기본 컬럼 디자인 무력화 */
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }
    /* 버튼 내부 텍스트 및 레이아웃 강제 고정 */
    .stButton button {
        width: 100% !important;
        padding: 0px !important;
        height: 45px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    /* 버튼 사이의 간격 최소화 */
    [data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
        flex-wrap: nowrap !important; /* 줄바꿈 방지 핵심 */
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
    # KST 보정 (선택한 날짜 다음날로 인식되는 문제 해결)
    selected_date = (datetime.strptime(selected_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    
    st.markdown("---")
    filtered_imgs = [item['url'] for item in data if item['date'] == selected_date]
    
    if filtered_imgs:
        if f"idx_{selected_date}" not in st.session_state:
            st.session_state[f"idx_{selected_date}"] = 0
            
        curr = st.session_state[f"idx_{selected_date}"]
        total = len(filtered_imgs)

        # ⭐️ flex-wrap: nowrap 을 적용한 강제 한 줄 레이아웃 ⭐️
        c1, c2, c3 = st.columns([1, 2, 1])
        
        with c1:
            if st.button("⬅️", key="p_btn"):
                st.session_state[f"idx_{selected_date}"] = (curr - 1) % total
                st.rerun()
        with c2:
            # 중앙 숫자를 버튼 높이와 맞추기 위해 45px 높이 고정
            st.markdown(f"<div style='height:45px; display:flex; justify-content:center; align-items:center; font-weight:bold;'>{curr + 1} / {total}</div>", unsafe_allow_html=True)
        with c3:
            if st.button("➡️", key="n_btn"):
                st.session_state[f"idx_{selected_date}"] = (curr + 1) % total
                st.rerun()

        st.image(filtered_imgs[st.session_state[f"idx_{selected_date}"]], use_container_width=True)
    else:
        st.info(f"{selected_date} 사진이 없습니다.")
