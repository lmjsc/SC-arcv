import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Archive", layout="centered")

# CSS: 버튼이 표 칸안에 꽉 차게 설정
st.markdown("""
    <style>
    .stButton button {
        width: 100% !important;
        height: 40px !important;
        border-radius: 8px !important;
    }
    table {
        width: 100%;
        border-collapse: collapse;display:inline;
    }
    td {
        vertical-align: middle;
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

with st.spinner('사진첩 여는 중...'):
    data = get_data()

state = calendar(options={"contentHeight": 350, "selectable": True})

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

        # [핵심] Table 구조로 버튼과 텍스트 배치
        # 각 칸의 너비를 25% | 50% | 25%로 고정
        col1, col2, col3 = st.columns([1, 2, 1])
        
        # 실제 클릭 로직은 Streamlit 버튼으로 처리하되, CSS로 위치를 잡습니다.
        with col1:
            if st.button("⬅️", key="prev"):
                st.session_state[f"idx_{selected_date}"] = (current_idx - 1) % total_count
                st.rerun()
        
        with col2:
            st.markdown(f"<div style='text-align: center; font-size: 18px; font-weight: bold; line-height: 40px;'>{current_idx + 1} / {total_count}</div>", unsafe_allow_html=True)
            
        with col3:
            if st.button("➡️", key="next"):
                st.session_state[f"idx_{selected_date}"] = (current_idx + 1) % total_count
                st.rerun()

        st.image(filtered_imgs[st.session_state[f"idx_{selected_date}"]], use_container_width=True)
    else:
        st.info(f"{selected_date} 사진이 없습니다.")

