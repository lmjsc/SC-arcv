import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Archive", layout="centered")

# [핵심] 버튼을 양사이드로 밀어내는 커스텀 CSS
st.markdown("""
    <style>
    /* 버튼 컨테이너를 한 줄로 고정하고 양 끝으로 배치 */
    .button-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        width: 100%;
    }
    /* 버튼 스타일 조정 */
    .stButton button {
        width: 60px !important;
        height: 40px !important;
        padding: 0px !important;
        border-radius: 8px;
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

with st.spinner('사진 불러오는 중...'):
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

        # HTML과 Streamlit 버튼을 조합하여 양사이드 배치 구현
        col_l, col_m, col_r = st.columns([1, 2, 1])
        
        with col_l:
            if st.button("⬅️", key="prev"):
                st.session_state[f"idx_{selected_date}"] = (current_idx - 1) % total_count
                st.rerun()
        
        with col_m:
            st.markdown(f"<p style='text-align: center; font-size: 18px; margin-top: 5px;'><b>{current_idx + 1} / {total_count}</b></p>", unsafe_allow_html=True)
            
        with col_r:
            # 버튼이 오른쪽 끝으로 붙도록 배치
            st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
            if st.button("➡️", key="next"):
                st.session_state[f"idx_{selected_date}"] = (current_idx + 1) % total_count
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.image(filtered_imgs[st.session_state[f"idx_{selected_date}"]], use_container_width=True)
    else:
        st.info(f"{selected_date} 사진이 없습니다.")
