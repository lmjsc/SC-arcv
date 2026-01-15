import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Archive", layout="centered")

# [핵심] 모바일에서도 절대 깨지지 않는 테이블 레이아웃 CSS
st.markdown("""
    <style>
    /* 컬럼 컨테이너 자체를 무조건 가로 정렬(Flex)로 고정 */
    [data-testid="column"] {
        width: calc(33% - 1rem) !important;
        flex: 1 1 calc(33% - 1rem) !important;
        min-width: 33% !important;
    }
    
    /* 버튼 크기 및 중앙 정렬 */
    .stButton button {
        width: 100% !important;
        padding: 5px 0 !important;
        border-radius: 10px !important;
    }
    
    /* 숫자 텍스트 수직 중앙 정렬 */
    .num-text {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 40px;
        font-weight: bold;
        font-size: 16px;
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
    # 날짜 보정 (KST 대응)
    selected_date = (datetime.strptime(selected_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    
    st.markdown("---")
    filtered_imgs = [item['url'] for item in data if item['date'] == selected_date]
    
    if filtered_imgs:
        if f"idx_{selected_date}" not in st.session_state:
            st.session_state[f"idx_{selected_date}"] = 0
            
        curr = st.session_state[f"idx_{selected_date}"]
        total = len(filtered_imgs)

        # 3칸을 나누어 강제 가로 배치
        c1, c2, c3 = st.columns(3)
        
        with c1:
            if st.button("⬅️", key="p"):
                st.session_state[f"idx_{selected_date}"] = (curr - 1) % total
                st.rerun()
        with c2:
            # 칸 안에서 텍스트를 수직/수평 중앙 정렬
            st.markdown(f"<div class='num-text'>{curr + 1} / {total}</div>", unsafe_allow_html=True)
        with c3:
            if st.button("➡️", key="n"):
                st.session_state[f"idx_{selected_date}"] = (curr + 1) % total
                st.rerun()

        st.image(filtered_imgs[st.session_state[f"idx_{selected_date}"]], use_container_width=True)
    else:
        st.info(f"{selected_date} 사진이 없습니다.")
