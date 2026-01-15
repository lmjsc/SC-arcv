import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# 1. 설정 및 노션 연결
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Archive", layout="centered")

# [핵심] 두 줄 레이아웃 전용 스타일
st.markdown("""
    <style>
    /* 버튼을 가로로 꽉 차게 */
    .stButton button {
        width: 100% !important;
        height: 50px !important;
        font-size: 20px !important;
        border-radius: 12px !important;
        margin-bottom: 5px !important;
    }
    /* 숫자 텍스트 스타일 */
    .nav-text {
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        margin: 10px 0;
        color: #555;
    }
    /* 간격 조정 */
    [data-testid="column"] {
        padding: 0 5px !important;
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

        # ⭐️ 1층: 이전/다음 버튼 (가로 2칸)
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("⬅️ 이전", key="p_btn"):
                st.session_state[f"idx_{selected_date}"] = (curr - 1) % total
                st.rerun()
        with btn_col2:
            if st.button("다음 ➡️", key="n_btn"):
                st.session_state[f"idx_{selected_date}"] = (curr + 1) % total
                st.rerun()

        # ⭐️ 2층: 숫자 표시 (단독 줄)
        st.markdown(f"<div class='nav-text'>{curr + 1} / {total}</div>", unsafe_allow_html=True)

        # 사진 출력
        st.image(filtered_imgs[st.session_state[f"idx_{selected_date}"]], use_container_width=True)
    else:
        st.info(f"{selected_date} 사진이 없습니다.")
