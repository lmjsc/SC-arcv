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

# [보안] 검색 엔진(구글, 네이버 등) 수집 차단 메타 태그
st.markdown('<head><meta name="robots" content="noindex, nofollow"></head>', unsafe_allow_html=True)

# [디자인] 사용자님 취향 다크 테마 CSS
st.markdown("""
    <style>
    .stApp { background-color: #1a1b26; color: #a9b1d6; }
    [data-testid="stSidebar"] { background-color: #1f2335 !important; border-right: 1px solid #414868; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { color: #ffffff !important; }
    [data-testid="stSidebar"] .stButton button { width: 100%; background-color: #24283b; border: 1px solid #414868; color: #7aa2f7; }
    [data-testid="stSidebar"] .stButton button:hover { border-color: #7aa2f7; background-color: #414868; }
    [data-testid="stImage"] img { border-radius: 15px; aspect-ratio: 1/1; object-fit: cover; border: 2px solid #414868; transition: 0.3s; }
    [data-testid="stImage"] img:hover { transform: scale(1.02); border-color: #7aa2f7; }
    iframe { background-color: #24283b !important; border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# [데이터 로드] 100장 제한 해제 Pagination
@st.cache_data(ttl=60)
def get_all_data():
    g_data = []
    has_more = True
    next_cursor = None
    while has_more:
        res_g = notion.databases.query(database_id=GALLERY_DB_ID, start_cursor=next_cursor)
        for page in res_g.get("results"):
            props = page.get('properties', {})
            date = props.get('날짜', {}).get('date', {}).get('start') or "날짜미상"
            tags_list = [s['name'] for s in props.get('스케줄', {}).get('multi_select', [])] + \
                        [t['name'] for t in props.get('tag', {}).get('multi_select', [])]
            search_text = " ".join(tags_list).lower()
            img_urls = set()
            for p_val in props.values():
                if p_val.get('type') == 'files':
                    for f in p_val.get('files', []):
                        u = f.get('file', {}).get('url') or f.get('external', {}).get('url')
                        if u: img_urls.add(u)
            for block in notion.blocks.children.list(block_id=page['id']).get("results"):
                if block["type"] == "image":
                    u = block["image"].get('file', {}).get('url') or block["image"].get('external', {}).get('url')
                    if u: img_urls.add(u)
            for final_url in img_urls:
                g_data.append({"url": final_url, "date": date, "tags": tags_list, "search_text": search_text})
        has_more = res_g.get("has_more")
        next_cursor = res_g.get("next_cursor")

    s_events = []
    has_more_s = True
    next_cursor_s = None
    while has_more_s:
        res_s = notion.databases.query(database_id=SCHEDULE_DB_ID, start_cursor=next_cursor_s)
        for page in res_s.get("results"):
            props = page.get('properties', {})
            title = props.get('스케줄명', {}).get('title', [{}])[0].get('plain_text', '제목없음')
            is_off = props.get('오프라인', {}).get('formula', {}).get('boolean', False)
            date_info = props.get('날짜', {}).get('date', {})
            if is_off and date_info:
                s_events.append({"title": title, "start": date_info.get('start'), "color": "#7aa2f7", "extendedProps": {"date": date_info.get('start')}})
        has_more_s = res_s.get("has_more")
        next_cursor_s = res_s.get("next_cursor")
    return g_data, s_events

with st.spinner('🦌 성찬이 불러오는 중...'):
    gallery_data, schedule_events = get_all_data()

# 사이드바 구성
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🦌 Sungchan Menu</h2>", unsafe_allow_html=True)
    if st.button("🔄 데이터 강제 새로고침"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("🔍 **빠른 착장 찾기**")
    # 자주 쓰는 태그 버튼들 (사용자님 노션 태그에 맞춰 수정 가능)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("#안경"): st.query_params["search"] = "안경"
        if st.button("#공항"): st.query_params["search"] = "공항"
    with col2:
        if st.button("#셀카"): st.query_params["search"] = "셀카"
        if st.button("#무대"): st.query_params["search"] = "무대"
    
    st.markdown("---")
    search_query = st.text_input("직접 검색 (단어 입력)", value=st.query_params.get("search", "")).lower()
    show_only_star = st.checkbox("⭐ Favorite SC")

# 필터링 로직
filtered_gallery = gallery_data
if show_only_star: filtered_gallery = [d for d in filtered_gallery if "⭐" in d['tags']]
if search_query: filtered_gallery = [d for d in filtered_gallery if search_query in d['search_text']]

# 메인 화면
st.title("Archive (  •  ³  •  )")

# 갤러리 상단 달력
cal_state = calendar(events=schedule_events, options={"contentHeight": 350, "selectable": True, "locale": "en"})

active_date = st.query_params.get("date")
if cal_state.get("callback") == "dateClick":
    active_date = (datetime.strptime(cal_state["dateClick"]["date"].split("T")[0], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
elif cal_state.get("callback") == "eventClick":
    active_date = cal_state["eventClick"]["event"]["extendedProps"]["date"]

if active_date:
    display_data = [d for d in filtered_gallery if d['date'] == active_date]
    st.subheader(f"📅 {active_date} 검색 결과")
    if st.button("⬅️ 전체 보기"): 
        st.query_params.clear()
        st.rerun()
else:
    display_data = filtered_gallery
    st.subheader(f"🖼️ 결과 ({len(display_data)}장)")

# 사진 그리드
if not display_data:
    st.info("해당 조건에 맞는 사진이 없습니다. 🦌")
else:
    cols = st.columns(3)
    for idx, item in enumerate(display_data):
        with cols[idx % 3]:
            st.image(item['url'], caption=item['date'], use_container_width=True)
