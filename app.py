import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# 1. 설정 및 노션 연결
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
GALLERY_DB_ID = st.secrets["DATABASE_ID"]
SCHEDULE_DB_ID = st.secrets["SCHEDULE_DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Sungchan Archive", layout="wide")

# [디자인] 통합 다크 모드 CSS
st.markdown("""
    <style>
    .stApp { background-color: #1a1b26; color: #a9b1d6; }
    h1, h2, h3 { color: #7aa2f7 !important; }
    iframe { background-color: #24283b !important; border-radius: 15px !important; border: 1px solid #414868 !important; }
    [data-testid="stImage"] img { border-radius: 12px; aspect-ratio: 1/1; object-fit: cover; border: 2px solid #414868; transition: 0.2s; }
    [data-testid="stImage"] img:hover { transform: scale(1.03); border-color: #7aa2f7; }
    </style>
    """, unsafe_allow_html=True)

# 데이터 로딩 함수
@st.cache_data(ttl=600)
def get_gallery_data():
    results = notion.databases.query(database_id=GALLERY_DB_ID).get("results")
    data = []
    for page in results:
        props = page.get('properties', {})
        date_str = props.get('날짜', {}).get('date', {}).get('start') or "날짜미상"
        sched_info = props.get('스케줄', {}).get('multi_select', [])
        tag_info = props.get('tag', {}).get('multi_select', [])
        combined_tags = list(set([s['name'] for s in sched_info] + [t['name'] for t in tag_info]))
        
        blocks = notion.blocks.children.list(block_id=page['id']).get("results")
        for block in blocks:
            if block["type"] == "image":
                url = block["image"].get('file', {}).get('url') or block["image"].get('external', {}).get('url')
                if url: data.append({"url": url, "date": date_str, "tags": combined_tags})
    return data

@st.cache_data(ttl=600)
def get_schedule_data():
    results = notion.databases.query(database_id=SCHEDULE_DB_ID).get("results")
    events = []
    for page in results:
        props = page.get('properties', {})
        # 스케줄명 가져오기
        title_list = props.get('스케줄명', {}).get('title', [])
        title = title_list[0].get('plain_text', '제목없음') if title_list else '제목없음'
        
        # 오프라인 수식 체크박스 확인
        offline_prop = props.get('오프라인', {})
        is_offline = False
        if offline_prop.get('type') == 'formula':
            is_offline = offline_prop.get('formula', {}).get('boolean', False)
        
        if is_offline:
            date_info = props.get('날짜', {}).get('date', {})
            if date_info:
                events.append({
                    "title": title,
                    "start": date_info.get('start'),
                    "end": date_info.get('end'),
                    "color": "#7aa2f7",
                    # 클릭 시 이동할 날짜 정보를 저장
                    "extendedProps": {"date": date_info.get('start')}
                })
    return events

# 사이드바 메뉴
with st.sidebar:
    st.title("📂 Menu")
    # URL 파라미터에 'date'가 있으면 갤러리를 기본값으로 설정
    default_index = 0 if "date" in st.query_params else 0
    menu = st.radio("이동할 페이지", ["🖼️ 사진 갤러리", "📅 스케줄 달력"], index=default_index)
    st.markdown("---")

# --- 페이지 1: 사진 갤러리 ---
if menu == "🖼️ 사진 갤러리":
    st.title("Archive (  •  ³  •  )")
    gallery_data = get_gallery_data()
    
    # 태그 필터
    all_tags = sorted(list(set([t for item in gallery_data for t in item['tags']])))
    selected_tag = st.sidebar.selectbox("🏷️ 태그 검색", ["전체 보기"] + all_tags)
    
    # URL 파라미터로 날짜가 넘어왔는지 확인
    query_date = st.query_params.get("date")
    
    # 달력 옵션
    calendar_options = {"contentHeight": 350, "selectable": True, "locale": "en"}
    state = calendar(options=calendar_options)
    
    display_data = gallery_data
    
    # 1. 태그 필터 적용
    if selected_tag != "전체 보기":
        display_data = [d for d in display_data if selected_tag in d['tags']]
    
    # 2. 날짜 필터 적용 (클릭 우선 -> URL 파라미터 순)
    active_date = None
    if state.get("callback") == "dateClick":
        active_date = (datetime.strptime(state["dateClick"]["date"].split("T")[0], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        st.query_params.clear() # 클릭 시 기존 쿼리 삭제
    elif query_date:
        active_date = query_date
        st.info(f"📅 스케줄에서 선택한 날짜: {active_date}")

    if active_date:
        display_data = [d for d in display_data if d['date'] == active_date]
        title_text = f"📅 {active_date} 결과"
    else:
        title_text = f"🖼️ {selected_tag}"

    st.subheader(f"{title_text} ({len(display_data)}장)")
    
    if display_data:
        cols = st.columns(3)
        for idx, item in enumerate(display_data):
            with cols[idx % 3]:
                st.image(item['url'], caption=item['date'], use_container_width=True)
    else:
        st.warning("사진이 없습니다.")

# --- 페이지 2: 스케줄 달력 ---
else:
    st.title("Sungchan Schedule 🗓️")
    schedule_events = get_schedule_data()
    
    calendar_options = {
        "contentHeight": 650,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,dayGridWeek"},
        "initialView": "dayGridMonth",
    }
    
    # 달력 표시 및 클릭 이벤트 감지
    sched_state = calendar(events=schedule_events, options=calendar_options)
    
    # 스케줄 클릭 시 해당 날짜를 들고 갤러리로 이동
    if sched_state.get("callback") == "eventClick":
        clicked_date = sched_state["eventClick"]["event"]["extendedProps"]["date"]
        st.query_params["date"] = clicked_date
        st.rerun()

    st.info("💡 스케줄을 클릭하면 해당 날짜의 사진 갤러리로 이동합니다.")
