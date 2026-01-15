import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# 1. 설정 및 노션 연결
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Archive", layout="centered")

# [핵심] 테이블 레이아웃 및 버튼 스타일 CSS
st.markdown("""
    <style>
    .nav-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
    }
    .nav-td {
        width: 33.33%;
        text-align: center;
        vertical-align: middle;
    }
    /* 버튼처럼 보이게 하는 스타일 */
    .nav-btn {
        display: inline-block;
        padding: 5px 15px;
        background-color: #f0f2f6;
        border-radius: 5px;
        text-decoration: none;
        color: black;
        font-weight: bold;
        border: 1px solid #dcdfe6;
        cursor: pointer;
    }
    /* Streamlit 기본 버튼 간격 제거 */
    [data-testid="column"] {
        display: flex;
        justify-content: center;
        align-items: center;
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

with st.spinner('Loading...'):
    data = get_data()

state = calendar(options={"contentHeight": 350, "selectable": True})

if state.get("callback") == "dateClick":
    selected_date = state["dateClick"]["date"].split("T")[0]
    # KST 보정
    selected_date = (datetime.strptime(selected_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    
    st.markdown("---")
    filtered_imgs = [item['url'] for item in data if item['date'] == selected_date]
    
    if filtered_imgs:
        if f"idx_{selected_date}" not in st.session_state:
            st.session_state[f"idx_{selected_date}"] = 0
            
        curr = st.session_state[f"idx_{selected_date}"]
        total = len(filtered_imgs)

        # ⭐️ 여기서부터 테이블 레이아웃 ⭐️
        # st.columns의 gap을 0으로 만들어 가로 한 줄 강제 유지
        c1, c2, c3 = st.columns([1, 1, 1])
        
        with c1:
            if st.button("⬅️", key="p", use_container_width=True):
                st.session_state[f"idx_{selected_date}"] = (curr - 1) % total
                st.rerun()
        with c2:
            # 숫자를 버튼들과 수평이 맞게 div로 감싸서 출력
            st.markdown(f"<div style='line-height:40px; font-weight:bold; text-align:center;'>{curr + 1} / {total}</div>", unsafe_allow_html=True)
        with c3:
            if st.button("➡️", key="n", use_container_width=True):
                st.session_state[f"idx_{selected_date}"] = (curr + 1) % total
                st.rerun()

        st.image(filtered_imgs[st.session_state[f"idx_{selected_date}"]], use_container_width=True)
    else:
        st.info(f"{selected_date} 사진이 없습니다.")
