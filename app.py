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

# [디자인] 사이드바 글자 시인성 강화 및 다크 테마 CSS
st.markdown("""
    <style>
    /* 전체 배경 및 기본 텍스트 */
    .stApp { background-color: #1a1b26; color: #a9b1d6; }
    
    /* 사이드바 글자색 및 배경색 강제 설정 */
    [data-testid="stSidebar"] {
        background-color: #1f2335 !important;
        border-right: 1px solid #414868;
    }
    /* 사이드바 내 모든 텍스트를 밝은 회색/흰색으로 */
    [data-testid="stSidebar"] .stText, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] h2 {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    
    /* 입력창 내부 텍스트 색상 */
    [data-testid="stSidebar"] input {
        color: #ffffff !important;
        background-color: #24283b !important;
    }

    /* 이미지 카드 디자인 */
    [data-testid="stImage"] img { 
        border-radius: 15px; 
        aspect-ratio: 1/1; 
        object-fit: cover; 
        border: 2px solid #414868; 
        transition: 0.3s ease; 
    }
    [data-testid="stImage"] img:hover { transform: translateY(-5px); border-color: #7aa2f7; }
    
    /* 로딩 스피너 색상 */
    .stSpinner > div > div { border-top-color: #7aa2f7 !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=300)
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

# 로딩 시 사슴 메시지 표시
with st.spinner('🦌 성찬이 데이터 동기화 중...'):
    gallery_data, schedule_events = get_all_data()

with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: white;'>🦌 Sungchan Menu</h2>", unsafe_allow_html=True)
    menu = st.radio("이동할 페이지", ["📅 스케줄 달력", "🖼️ 사진 갤러리"])
    st.markdown("---")
    search_query = st.text_input("🔍 착장 검색 (안경, 공항 등)", "").lower()
    
    years = sorted(list(set([d['date'].split('-')[0] for d in gallery_data if d['date'] != "날짜미상"])), reverse=True)
    sel_year = st.selectbox("📅 연도 선택", ["전체"] + years)
    show_only_star = st.checkbox("⭐ 레전드만 보기")

# 필터링 로직
filtered_gallery = gallery_data
if show_only_star: filtered_gallery = [d for d in filtered_gallery if "⭐" in d['tags']]
if sel_year != "전체": filtered_gallery = [d for d in filtered_gallery if d['date'].startswith(sel_year)]
if search_query: filtered_gallery = [d for d in filtered_gallery if search_query in d['search_text']]

if menu == "📅 스케줄 달력":
    st.title("Sungchan Schedule 🗓️")
    sched_state = calendar(events=schedule_events, options={"contentHeight": 650, "initialView": "dayGridMonth", "locale": "en"})
    if sched_state.get("callback") == "eventClick":
        st.query_params["date"] = sched_state["eventClick"]["event"]["extendedProps"]["date"]
        st.rerun()
else:
    st.title("Archive (  •  ³  •  )")
    query_date = st.query_params.get("date")
    cal_state = calendar(options={"contentHeight": 350, "selectable": True, "locale": "en"})
    
    display_data = filtered_gallery
    active_date = None
    if cal_state.get("callback") == "dateClick":
        active_date = (datetime.strptime(cal_state["dateClick"]["date"].split("T")[0], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        st.query_params.clear()
    elif query_date: active_date = query_date

    if active_date:
        display_data = [d for d in display_data if d['date'] == active_date]
        st.subheader(f"📅 {active_date} 결과 ({len(display_data)}장)")
    else:
        st.subheader(f"🖼️ 전체 결과 ({len(display_data)}장)")

    cols = st.columns(3)
    for idx, item in enumerate(display_data):
        with cols[idx % 3]:
            st.image(item['url'], caption=item['date'], use_container_width=True)
