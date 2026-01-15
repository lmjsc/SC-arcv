import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# 1. 설정 및 노션 연결
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
GALLERY_DB_ID = st.secrets["DATABASE_ID"]
SCHEDULE_DB_ID = st.secrets["SCHEDULE_DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Sungchan Archive 🦌", page_icon="🦌", layout="wide")

# [디자인] 기존 디자인 유지
st.markdown("""
    <style>
    .stApp { background-color: #1a1b26; color: #a9b1d6; }
    [data-testid="stSidebar"] { background-color: #1f2335 !important; border-right: 1px solid #414868; }
    [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] span { color: #ffffff !important; }
    [data-testid="stImage"] img { border-radius: 15px; aspect-ratio: 1/1; object-fit: cover; border: 2px solid #414868; }
    </style>
    """, unsafe_allow_html=True)

# [수정] 캐시 시간을 60초로 단축하여 더 자주 업데이트 확인
@st.cache_data(ttl=60)
def get_all_data():
    res_g = notion.databases.query(database_id=GALLERY_DB_ID).get("results")
    g_data = []
    for page in res_g:
        props = page.get('properties', {})
        date = props.get('날짜', {}).get('date', {}).get('start') or "날짜미상"
        s_tags = props.get('스케줄', {}).get('multi_select', [])
        t_tags = props.get('tag', {}).get('multi_select', [])
        tags_list = [s['name'] for s in s_tags] + [t['name'] for t in t_tags]
        search_text = " ".join(tags_list).lower()
        
        blocks = notion.blocks.children.list(block_id=page['id']).get("results")
        for block in blocks:
            if block["type"] == "image":
                url = block["image"].get('file', {}).get('url') or block["image"].get('external', {}).get('url')
                if url: g_data.append({"url": url, "date": date, "tags": tags_list, "search_text": search_text})
    
    res_s = notion.databases.query(database_id=SCHEDULE_DB_ID).get("results")
    s_events = []
    for page in res_s:
        props = page.get('properties', {})
        title = props.get('스케줄명', {}).get('title', [{}])[0].get('plain_text', '제목없음')
        is_off = props.get('오프라인', {}).get('formula', {}).get('boolean', False)
        date_info = props.get('날짜', {}).get('date', {})
        if is_off and date_info:
            s_events.append({"title": title, "start": date_info.get('start'), "end": date_info.get('end'), "color": "#7aa2f7", "extendedProps": {"date": date_info.get('start')}})
    return g_data, s_events

# 데이터 불러오기
gallery_data, schedule_events = get_all_data()

with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🦌 Sungchan Menu</h2>", unsafe_allow_html=True)
    
    # [새로운 기능] 데이터 강제 새로고침 버튼
    if st.button("🔄 데이터 새로고침"):
        st.cache_data.clear() # 모든 캐시 삭제
        st.rerun() # 앱 재실행
        
    st.markdown("---")
    menu = st.radio("이동할 페이지", ["📅 스케줄 달력", "🖼️ 사진 갤러리"])
    search_query = st.text_input("🔍 착장 검색", "").lower()
    
    years = sorted(list(set([d['date'].split('-')[0] for d in gallery_data if d['date'] != "날짜미상"])), reverse=True)
    sel_year = st.selectbox("📅 연도 선택", ["전체"] + years)
    show_only_star = st.checkbox("⭐ 레전드만 보기")

# 나머지 갤러리/스케줄 출력 로직 동일...
# (생략된 부분은 기존 코드와 동일하게 유지하시면 됩니다.)
