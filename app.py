import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# 1. 설정 및 노션 연결
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
GALLERY_DB_ID = st.secrets["DATABASE_ID"]
SCHEDULE_DB_ID = st.secrets["SCHEDULE_DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(
    page_title="Sungchan Archive 🦌",
    page_icon="🦌",
    layout="wide"
)

# [디자인] 다크모드 및 달력 내 사진 표시 CSS
st.markdown("""
    <style>
    .stApp { background-color: #1a1b26; color: #a9b1d6; }
    h1, h2, h3 { color: #7aa2f7 !important; }
    iframe { background-color: #24283b !important; border-radius: 15px !important; border: 1px solid #414868 !important; }
    
    /* 갤러리 이미지 효과 */
    [data-testid="stImage"] img { border-radius: 12px; aspect-ratio: 1/1; object-fit: cover; border: 2px solid #414868; transition: 0.2s; }
    [data-testid="stImage"] img:hover { transform: scale(1.03); border-color: #7aa2f7; }
    
    /* 사진 달력 전용 스타일: 날짜 칸을 사진으로 가득 채움 */
    .fc-event.photo-event {
        background-size: cover !important;
        background-position: center !important;
        height: 80px !important;
        border: 1px solid #414868 !important;
        border-radius: 10px !important;
    }
    .fc-event.photo-event .fc-event-title { display: none; }
    </style>
    """, unsafe_allow_html=True)

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
            s_events.append({
                "title": title, 
                "start": date_info.get('start'), 
                "end": date_info.get('end'), 
                "color": "#7aa2f7", 
                "extendedProps": {"date": date_info.get('start')}
            })
            
    return g_data, s_events

gallery_data, schedule_events = get_all_data()

# [수정] 사이드바 메뉴 3개로 분리 및 순서 조정
with st.sidebar:
    st.title("🦌 Sungchan Menu")
    menu = st.radio("이동할 페이지", ["📅 스케줄 달력", "📊 월말 정산 달력", "🖼️ 사진 갤러리"])
    st.markdown("---")
    
    # 공통 필터
    all_dates = [d['date'] for d in gallery_data if d['date'] != "날짜미상"]
    years = sorted(list(set([d.split('-')[0] for d in all_dates])), reverse=True)
    sel_year = st.selectbox("📅 연도 선택", ["전체"] + years)
    show_only_star = st.checkbox("⭐ 레전드만 보기")

# 필터 적용
filtered_gallery = gallery_data
if show_only_star:
    filtered_gallery = [d for d in filtered_gallery if "⭐" in d['tags']]
if sel_year != "전체":
    filtered_gallery = [d for d in filtered_gallery if d['date'].startswith(sel_year)]

# --- 페이지 1: 스케줄 달력 ---
if menu == "📅 스케줄 달력":
    st.title("Sungchan Schedule 🗓️")
    sched_state = calendar(events=schedule_events, options={"contentHeight": 650, "initialView": "dayGridMonth", "locale": "en"})
    if sched_state.get("callback") == "eventClick":
        st.query_params["date"] = sched_state["eventClick"]["event"]["extendedProps"]["date"]
        st.rerun()

# --- 페이지 2: 월말 정산 달력 ---
elif menu == "📊 월말 정산 달력":
    st.title("Monthly Photo Recap 🎞️")
    st.info("각 날짜의 대표 사진으로 한 달을 정산해보세요!")
    
    photo_events = []
    seen_dates = set()
    for item in filtered_gallery:
        if item['date'] not in seen_dates and item['date'] != "날짜미상":
            photo_events.append({
                "start": item['date'],
                "title": "photo",
                "display": "block",
                "backgroundColor": "transparent",
                "borderColor": "transparent",
                "className": "photo-event",
                "extendedProps": {"imageUrl": item['url']}
            })
            seen_dates.add(item['date'])
    
    # 사진을 달력 이벤트 배경으로 주입하는 커스텀 스크립트 대응 CSS
    custom_css = "<style>"
    for ev in photo_events:
        url = ev['extendedProps']['imageUrl']
        custom_css += f".fc-daygrid-event[style*='{ev['start']}'] {{ background-image: url('{url}') !important; }}"
    custom_css += "</style>"
    st.markdown(custom_css, unsafe_allow_html=True)

    calendar(events=photo_events, options={"contentHeight": 700, "initialView": "dayGridMonth", "locale": "en"})

# --- 페이지 3: 사진 갤러리 ---
else:
    st.title("Archive (  •  ³  •  )")
    all_tags = sorted(list(set([t for item in filtered_gallery for t in item['tags']])))
    selected_tag = st.sidebar.selectbox("🏷️ 태그 검색", ["전체 보기"] + all_tags)
    
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
