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

# [디자인] 사이드바 시인성 및 다크 테마 CSS
st.markdown("""
    <style>
    .stApp { background-color: #1a1b26; color: #a9b1d6; }
    [data-testid="stSidebar"] { background-color: #1f2335 !important; border-right: 1px solid #414868; }
    [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] span { color: #ffffff !important; font-weight: 500 !important; }
    [data-testid="stSidebar"] .stTextInput input { color: #ffffff !important; background-color: #24283b !important; border: 1px solid #7aa2f7 !important; }
    [data-testid="stImage"] img { border-radius: 15px; aspect-ratio: 1/1; object-fit: cover; border: 2px solid #414868; transition: 0.3s ease; }
    [data-testid="stImage"] img:hover { transform: translateY(-5px); border-color: #7aa2f7; }
    iframe { background-color: #24283b !important; border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# [데이터 로드] 100장 제한 해제(Pagination) 및 중복 제거
@st.cache_data(ttl=60)
def get_all_data():
    # 1. 갤러리 데이터 전체 수집 (Pagination 적용)
    g_data = []
    has_more = True
    next_cursor = None
    
    while has_more:
        res_g = notion.databases.query(
            database_id=GALLERY_DB_ID,
            start_cursor=next_cursor
        )
        
        for page in res_g.get("results"):
            props = page.get('properties', {})
            date = props.get('날짜', {}).get('date', {}).get('start') or "날짜미상"
            s_tags = props.get('스케줄', {}).get('multi_select', [])
            t_tags = props.get('tag', {}).get('multi_select', [])
            tags_list = [s['name'] for s in s_tags] + [t['name'] for t in t_tags]
            search_text = " ".join(tags_list).lower()
            
            img_urls = set() # 한 페이지 내 중복 URL 방지
            
            # 파일 열 확인
            for p_val in props.values():
                if p_val.get('type') == 'files':
                    for f in p_val.get('files', []):
                        u = f.get('file', {}).get('url') or f.get('external', {}).get('url')
                        if u: img_urls.add(u)
            
            # 본문 블록 확인
            blocks = notion.blocks.children.list(block_id=page['id']).get("results")
            for block in blocks:
                if block["type"] == "image":
                    u = block["image"].get('file', {}).get('url') or block["image"].get('external', {}).get('url')
                    if u: img_urls.add(u)
            
            for final_url in img_urls:
                g_data.append({"url": final_url, "date": date, "tags": tags_list, "search_text": search_text})
        
        has_more = res_g.get("has_more")
        next_cursor = res_g.get("next_cursor")

    # 2. 스케줄 데이터 전체 수집 (Pagination 적용)
    s_events = []
    has_more_s = True
    next_cursor_s = None
    
    while has_more_s:
        res_s = notion.databases.query(
            database_id=SCHEDULE_DB_ID,
            start_cursor=next_cursor_s
        )
        for page in res_s.get("results"):
            props = page.get('properties', {})
            title_list = props.get('스케줄명', {}).get('title', [])
            title = title_list[0].get('plain_text', '제목없음') if title_list else '제목없음'
            is_off = props.get('오프라인', {}).get('formula', {}).get('boolean', False)
            date_info = props.get('날짜', {}).get('date', {})
            if is_off and date_info:
                s_events.append({
                    "title": title, 
                    "start": date_info.get('start'), 
                    "end": date_info.get('end'), 
                    "color": "#7aa2f7", 
                    "extendedProps": {"date": date_info.get('start')}
                })
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
    menu = st.radio("이동할 페이지", ["📅 스케줄 달력", "🖼️ 사진 갤러리"])
    search_query = st.text_input("🔍 착장 검색 (안경, 공항 등)", "").lower()
    years = sorted(list(set([d['date'].split('-')[0] for d in gallery_data if d['date'] != "날짜미상"])), reverse=True)
    sel_year = st.selectbox("📅 연도 선택", ["전체"] + years)
    show_only_star = st.checkbox("⭐ Favorite SC")

# 공통 필터링 로직
filtered_gallery = gallery_data
if show_only_star: filtered_gallery = [d for d in filtered_gallery if "⭐" in d['tags']]
if sel_year != "전체": filtered_gallery = [d for d in filtered_gallery if d['date'].startswith(sel_year)]
if search_query: filtered_gallery = [d for d in filtered_gallery if search_query in d['search_text']]

# 페이지 출력부
if menu == "📅 스케줄 달력":
    st.title("Sungchan Schedule 🗓️")
    sched_state = calendar(events=schedule_events, options={"contentHeight": 650, "initialView": "dayGridMonth", "locale": "en"})
    if sched_state.get("callback") == "eventClick":
        st.query_params["date"] = sched_state["eventClick"]["event"]["extendedProps"]["date"]
        st.rerun()
else:
    st.title("Archive (  •  ³  •  )")
    
    # --- 사진 갤러리 상단 날짜 선택용 캘린더 ---
    query_date = st.query_params.get("date")
    cal_state = calendar(options={"contentHeight": 350, "selectable": True, "locale": "en"})
    
    display_data = filtered_gallery
    active_date = None
    
    if cal_state.get("callback") == "dateClick":
        # 클릭한 날짜로 필터링 (보정 포함)
        active_date = (datetime.strptime(cal_state["dateClick"]["date"].split("T")[0], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        st.query_params.clear()
    elif query_date:
        active_date = query_date

    if active_date:
        display_data = [d for d in display_data if d['date'] == active_date]
        st.subheader(f"📅 {active_date} 결과 ({len(display_data)}장)")
        if st.button("⬅️ 전체 보기"):
            st.query_params.clear()
            st.rerun()
    else:
        st.subheader(f"🖼️ 결과 ({len(display_data)}장)")

    # 사진 그리드 출력
    if not display_data:
        st.info("해당 조건에 맞는 사진이 없습니다. 🦌")
    else:
        cols = st.columns(3)
        for idx, item in enumerate(display_data):
            with cols[idx % 3]:
                st.image(item['url'], caption=item['date'], use_container_width=True)
