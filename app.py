import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Archive", layout="centered")

# [핵심] 가로 한 줄 강제 고정 및 버튼 크기 축소 CSS
st.markdown("""
    <style>
    /* 전체 컨트롤 컨테이너 */
    .nav-wrapper {
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-between !important;
        align-items: center !important;
        width: 100% !important;
        margin: 10px 0 !important;
    }
    /* 버튼 크기 대폭 축소 */
    .stButton button {
        width: 50px !important;
        height: 35px !important;
        min-width: 50px !important;
        padding: 0 !important;
        font-size: 14px !important;
        border-radius: 20px !important;
    }
    /* 숫자 텍스트 중앙 정렬 */
    .count-text {
        font-size: 16px;
        font-weight: bold;
        flex-grow: 1;
        text-align: center;
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

with st.spinner('로딩 중...'):
    data = get_data()

calendar_options = {
    "contentHeight": 350,
    "selectable": True,
    "headerToolbar": {"left": "prev,next", "center": "title", "right": "today"},
}

state = calendar(options=calendar_options)

if state.get("callback") == "dateClick":
    click_raw = state["dateClick"]["date"]
    click_dt = datetime.fromisoformat(click_raw.replace("Z", "+00:00"))
    corrected_dt = click_dt + timedelta(hours=12)
    selected_date = corrected_dt.strftime("%Y-%m-%d")
    
    st.markdown("---")
    filtered_imgs = [item['url'] for item in data if item['date'] == selected_date]
    
    if filtered_imgs:
        if f"idx_{selected_date}" not in st.session_state:
            st.session_state[f"idx_{selected_date}"] = 0
            
        current_idx = st.session_state[f"idx_{selected_date}"]
        total_count = len(filtered_imgs)

        # [수정] 컬럼 대신 한 줄에 배치되도록 버튼 구조 변경
        # Streamlit 컬럼은 폰에서 깨지기 쉬워 커스텀 레이아웃 적용
        col_prev, col_text, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if st.button("⬅️", key="prev"):
                st.session_state[f"idx_{selected_date}"] = (current_idx - 1) % total_count
                st.rerun()
        
        with col_text:
            st.markdown(f"<div class='count-text'>{current_idx + 1} / {total_count}</div>", unsafe_allow_html=True)
            
        with col_next:
            # 오른쪽 정렬을 위해 div로 한 번 더 감쌈
            st.markdown("<div style='display: flex; justify-content: flex-end;'>", unsafe_allow_html=True)
            if st.button("➡️", key="next"):
                st.session_state[f"idx_{selected_date}"] = (current_idx + 1) % total_count
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.image(filtered_imgs[st.session_state[f"idx_{selected_date}"]], use_container_width=True)
    else:
        st.info(f"{selected_date} 사진이 없습니다.")
