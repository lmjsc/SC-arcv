import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# 1. 설정 및 노션 연결
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
GALLERY_DB_ID = st.secrets["DATABASE_ID"] # 기존 사진 DB
SCHEDULE_DB_ID = st.secrets["SCHEDULE_DATABASE_ID"] # 신규 스케줄 DB
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Sungchan Archive", layout="wide")

# CSS 스타일 (기존 스타일 유지 + 사이드바 커스텀)
st.markdown("""
    <style>
    .stApp { background-color: #1a1b26; color: #a9b1d6; }
    h1, h2, h3 { color: #7aa2f7 !important; }
    iframe { background-color: #24283b !important; border-radius: 15px !important; border: 1px solid #414868 !important; }
    [data-testid="stImage"] img { border-radius: 12px; aspect-ratio: 1/1; object-fit: cover; border: 2px solid #414868; }
    </style>
    """, unsafe_allow_html=True)

# 데이터 가져오기 함수 (캐싱 적용)
@st.cache_data(ttl=600)
def get_notion_data(database_id, is_gallery=True):
    results = notion.databases.query(database_id=database_id).get("results")
    data = []
    for page in results:
        props = page.get('properties', {})
        
        if is_gallery:
            # 사진 갤러리 로직
            date_str = props.get('날짜', {}).get('date', {}).get('start') or "날짜미상"
            sched_info = props.get('스케줄', {}).get('multi_select', [])
            tag_info = props.get('tag', {}).get('multi_select', [])
            combined_tags = list(set([s['name'] for s in sched_info] + [t['name'] for t in tag_info]))
            
            blocks = notion.blocks.children.list(block_id=page['id']).get("results")
            for block in blocks:
                if block["type"] == "image":
                    img_block = block["image"]
                    url = img_block.get('file', {}).get('url') or img_block.get('external', {}).get('url')
                    if url: data.append({"url": url, "date": date_str, "tags": combined_tags})
        else:
            # 스케줄 달력 로직 (제목과 날짜만 가져옴)
            title = props.get('이름', {}).get('title', [{}])[0].get('plain_text', '제목없음')
            date_info = props.get('날짜', {}).get('date', {})
            if date_info:
                data.append({
                    "title": title,
                    "start": date_info.get('start'),
                    "end": date_info.get('end'),
                    "color": "#7aa2f7"
                })
    return data

# 사이드바 메뉴 구성
with st.sidebar:
    st.title("📂 Menu")
    menu = st.radio("이동할 페이지", ["🖼️ 사진 갤러리", "📅 스케줄 달력"])
    st.markdown("---")

# --- 페이지 1: 사진 갤러리 ---
if menu == "🖼️ 사진 갤러리":
    st.title("Archive (  •  ³  •  )")
    gallery_raw = get_notion_data(GALLERY_DB_ID, is_gallery=True)
    
    # 통합 검색 필터
    all_tags = sorted(list(set([t for item in gallery_raw for t in item['tags']])))
    selected_tag = st.sidebar.selectbox("🏷️ 태그 검색", ["전체 보기"] + all_tags)
    
    # 달력
    cal_state = calendar(options={"contentHeight": 350, "selectable": True, "locale": "en"})
    
    # 필터링 및 출력
    display_data = gallery_raw
    if selected_tag != "전체 보기":
        display_data = [d for d in display_data if selected_tag in d['tags']]
    
    if cal_state.get("callback") == "dateClick":
        target_date = (datetime.strptime(cal_state["dateClick"]["date"].split("T")[0], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        display_data = [d for d in display_data if d['date'] == target_date]

    st.subheader(f"결과: {len(display_data)}장")
    cols = st.columns(3)
    for idx, item in enumerate(display_data):
        with cols[idx % 3]:
            st.image(item['url'], caption=item['date'], use_container_width=True)

# --- 페이지 2: 스케줄 달력 ---
else:
    st.title("Sungchan Schedule 🗓️")
    schedule_events = get_notion_data(SCHEDULE_DB_ID, is_gallery=False)
    
    calendar_options = {
        "contentHeight": 600,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,dayGridWeek"},
        "initialView": "dayGridMonth",
        "locale": "en",
        "editable": False,
        "selectable": True,
    }
    
    # 스케줄 전용 달력 (가져온 이벤트를 넣어줍니다)
    calendar(events=schedule_events, options=calendar_options)
    st.info("노션 스케줄 데이터베이스와 실시간 연동 중입니다.")
