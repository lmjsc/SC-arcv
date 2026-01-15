import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# 1. 설정 및 노션 연결
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
GALLERY_DB_ID = st.secrets["DATABASE_ID"]
SCHEDULE_DB_ID = st.secrets["SCHEDULE_DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

# [디자인] 파비콘 설정 (사슴 아이콘) 및 페이지 레이아웃
st.set_page_config(
    page_title="Sungchan Archive 🦌",
    page_icon="🦌",
    layout="wide"
)

# 통합 다크 모드 및 달력 내 이미지 스타일 CSS
st.markdown("""
    <style>
    .stApp { background-color: #1a1b26; color: #a9b1d6; }
    h1, h2, h3 { color: #7aa2f7 !important; }
    iframe { background-color: #24283b !important; border-radius: 15px !important; border: 1px solid #414868 !important; }
    
    /* 갤러리 이미지 스타일 */
    [data-testid="stImage"] img { border-radius: 12px; aspect-ratio: 1/1; object-fit: cover; border: 2px solid #414868; transition: 0.2s; }
    [data-testid="stImage"] img:hover { transform: scale(1.03); border-color: #7aa2f7; }
    
    /* 달력 내부 사진 스타일 (월말정산용) */
    .fc-event-main { background: none !important; border: none !important; }
    .cal-img { width: 100%; border-radius: 4px; aspect-ratio: 1/1; object-fit: cover; }
    </style>
    """, unsafe_allow_html=True)

# 데이터 로딩 함수 (캐시 적용)
@st.cache_data(ttl=600)
def get_all_data():
    # 갤러리 데이터
    res_g = notion.databases.query(database_id=GALLERY_DB_ID).get("results")
    g_data = []
    for page in res_g:
        props = page.get('properties', {})
        date = props.get('날짜', {}).get('date', {}).get('start') or "날짜미상"
        s_tags = props.get('스케줄', {}).get('multi_select', [])
        t_tags = props.get('tag', {}).get('multi_select', [])
        tags = list(set([s['name'] for s in s_tags] + [t['name'] for t in t_tags]))
        
        blocks = notion.blocks.children.list(block_id=page['id']).get("results")
        for block in blocks:
            if block["type"] == "image":
                url = block["image"].get('file', {}).get('url') or block["image"].get('external', {}).get('url')
                if url: g_data.append({"url": url, "date": date, "tags": tags})
    
    # 스케줄 데이터
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

gallery_data, schedule_events = get_all_data()

# 사이드바 메뉴
with st.sidebar:
    st.title("🦌 Sungchan Menu")
    menu = st.radio("이동할 페이지", ["🖼️ 사진 갤러리", "📊 월말 정산 달력", "📅 스케줄 달력"])
    st.markdown("---")
    
    # [1번 기능] 타임라인 필터 (연도/월)
    all_dates = [d['date'] for d in gallery_data if d['date'] != "날짜미상"]
    years = sorted(list(set([d.split('-')[0] for d in all_dates])), reverse=True)
    sel_year = st.selectbox("📅 연도 선택", ["전체"] + years)
    
    # [2번 기능] ⭐ 레전드 필터 (이미 노션에 정리 중인 ⭐ 태그 활용)
    show_only_star = st.checkbox("⭐ 레전드만 보기")

# --- 공통 필터링 로직 ---
filtered_gallery = gallery_data
if show_only_star:
    filtered_gallery = [d for d in filtered_gallery if "⭐" in d['tags']]
if sel_year != "전체":
    filtered_gallery = [d for d in filtered_gallery if d['date'].startswith(sel_year)]

# --- 페이지 1: 사진 갤러리 ---
if menu == "🖼️ 사진 갤러리":
    st.title("Sungchan Archive")
    all_tags = sorted(list(set([t for item in filtered_gallery for t in item['tags']])))
    selected_tag = st.sidebar.selectbox("🏷️ 태그 검색", ["전체 보기"] + all_tags)
    
    # URL 파라미터 날짜 확인
    query_date = st.query_params.get("date")
    cal_state = calendar(options={"contentHeight": 350, "selectable": True, "locale": "en"})
    
    display_data = filtered_gallery
    if selected_tag != "전체 보기":
        display_data = [d for d in display_data if selected_tag in d['tags']]
        
    active_date = None
    if cal_state.get("callback") == "dateClick":
        active_date = (datetime.strptime(cal_state["dateClick"]["date"].split("T")[0], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        st.query_params.clear()
    elif query_date:
        active_date = query_date

    if active_date:
        display_data = [d for d in display_data if d['date'] == active_date]
        st.subheader(f"📅 {active_date} 결과 ({len(display_data)}장)")
    else:
        st.subheader(f"🖼️ {selected_tag} ({len(display_data)}장)")

    cols = st.columns(3)
    for idx, item in enumerate(display_data):
        with cols[idx % 3]:
            st.image(item['url'], caption=item['date'], use_container_width=True)

# --- 페이지 2: 월말 정산 달력 (사진 달력) ---
elif menu == "📊 월말 정산 달력":
    st.title("Monthly Photo Summary 🎞️")
    st.info("달력 안에 그날의 대표 사진이 표시됩니다. 월말 정산용으로 확인하세요!")
    
    # 달력용 이벤트 데이터 생성 (날짜별 첫 번째 사진만 추출)
    photo_events = []
    seen_dates = set()
    for item in filtered_gallery:
        if item['date'] not in seen_dates and item['date'] != "날짜미상":
            photo_events.append({
                "start": item['date'],
                "display": "background", # 배경처럼 깔기
                "backgroundColor": "transparent",
                "html": f'<img src="{item["url"]}" class="cal-img">' # 커스텀 HTML 주입
            })
            seen_dates.add(item['date'])
            
    calendar(events=photo_events, options={"contentHeight": 700, "initialView": "dayGridMonth", "locale": "en"})

# --- 페이지 3: 스케줄 달력 ---
else:
    st.title("Sungchan Schedule 🗓️")
    sched_state = calendar(events=schedule_events, options={"contentHeight": 650, "initialView": "dayGridMonth", "locale": "en"})
    if sched_state.get("callback") == "eventClick":
        st.query_params["date"] = sched_state["eventClick"]["event"]["extendedProps"]["date"]
        st.rerun()
