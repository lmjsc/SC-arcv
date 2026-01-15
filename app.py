import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta
import base64 # 로딩 아이콘용

# 1. 설정 및 노션 연결
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
GALLERY_DB_ID = st.secrets["DATABASE_ID"]
SCHEDULE_DB_ID = st.secrets["SCHEDULE_DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Sungchan Archive 🦌", page_icon="🦌", layout="wide")

# [디자인] 통합 다크 모드 CSS + 로딩 아이콘 CSS
st.markdown("""
    <style>
    .stApp { background-color: #1a1b26; color: #a9b1d6; }
    h1, h2, h3 { color: #7aa2f7 !important; }
    iframe { background-color: #24283b !important; border-radius: 15px !important; border: 1px solid #414868 !important; }
    [data-testid="stImage"] img { border-radius: 12px; aspect-ratio: 1/1; object-fit: cover; border: 2px solid #414868; transition: 0.2s; }
    [data-testid="stImage"] img:hover { transform: scale(1.03); border-color: #7aa2f7; }
    
    /* 로딩 애니메이션 스타일 */
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 300px; /* 로딩 스피너가 보이는 최소 높이 */
        color: #7aa2f7;
        font-size: 1.2em;
    }
    .loading-spinner {
        animation: spin 1.5s linear infinite;
        width: 60px;
        height: 60px;
        margin-bottom: 20px;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)

# [로딩 아이콘] 사슴 SVG (Base64 인코딩)
# 좀 더 최적화된 방법은 외부에 SVG 파일로 두는 것이나, 편의상 여기에 포함
DEER_SVG = """
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M12 2C9.5 2 7 3.5 7 6C7 8.5 9.5 10 12 10C14.5 10 17 8.5 17 6C17 3.5 14.5 2 12 2Z" fill="#7aa2f7"/>
<path d="M12 11C8.5 11 5 13 5 17V22H19V17C19 13 15.5 11 12 11Z" fill="#7aa2f7"/>
<path d="M16 1C17.6569 1 19 2.34315 19 4C19 5.65685 17.6569 7 16 7C14.3431 7 13 5.65685 13 4C13 2.34315 14.3431 1 16 1Z" fill="#7aa2f7"/>
<path d="M8 1C6.34315 1 5 2.34315 5 4C5 5.65685 6.34315 7 8 7C9.65685 7 11 5.65685 11 4C11 2.34315 9.65685 1 8 1Z" fill="#7aa2f7"/>
</svg>
"""
DEER_SVG_B64 = base64.b64encode(DEER_SVG.encode()).decode()

@st.cache_data(ttl=600)
def get_all_data():
    with st.spinner('🦌 성찬이 데이터 동기화 중...'): # 데이터 로딩 시 스피너 표시
        # 갤러리 데이터
        res_g = notion.databases.query(database_id=GALLERY_DB_ID).get("results")
        g_data = []
        for page in res_g:
            props = page.get('properties', {})
            date = props.get('날짜', {}).get('date', {}).get('start') or "날짜미상"
            s_tags = props.get('스케줄', {}).get('multi_select', [])
            t_tags = props.get('tag', {}).get('multi_select', [])
            
            # [수정] 검색을 위해 모든 태그를 하나의 리스트(문자열)로 저장
            combined_tags_list = [s['name'] for s in s_tags] + [t['name'] for t in t_tags]
            combined_tags_str = " ".join(combined_tags_list).lower() # 검색 용이하게 소문자 문자열로
            
            blocks = notion.blocks.children.list(block_id=page['id']).get("results")
            for block in blocks:
                if block["type"] == "image":
                    url = block["image"].get('file', {}).get('url') or block["image"].get('external', {}).get('url')
                    if url: g_data.append({"url": url, "date": date, "tags": combined_tags_list, "search_text": combined_tags_str})
        
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

with st.sidebar:
    st.title("🦌 Sungchan Menu")
    menu = st.radio("이동할 페이지", ["📅 스케줄 달력", "🖼️ 사진 갤러리"])
    st.markdown("---")
    
    # [새로운 기능] 검색창
    search_query = st.text_input("🔍 태그/스케줄 검색", "").lower() # 소문자로 변환하여 검색

    # 공통 필터
    all_dates = [d['date'] for d in gallery_data if d['date'] != "날짜미상"]
    years = sorted(list(set([d.split('-')[0] for d in all_dates])), reverse=True)
    sel_year = st.selectbox("📅 연도 선택", ["전체"] + years)
    show_only_star = st.checkbox("⭐ 레전드만 보기")

# 필터 적용
filtered_gallery = gallery_data
if show_only_star: filtered_gallery = [d for d in filtered_gallery if "⭐" in d['tags']]
if sel_year != "전체": filtered_gallery = [d for d in filtered_gallery if d['date'].startswith(sel_year)]

# [새로운 기능] 검색 쿼리 필터 적용
if search_query:
    filtered_gallery = [d for d in filtered_gallery if search_query in d['search_text']]


if menu == "📅 스케줄 달력":
    st.title("Sungchan Schedule 🗓️")
    with st.spinner('스케줄 불러오는 중...'):
        sched_state = calendar(events=schedule_events, options={"contentHeight": 650, "initialView": "dayGridMonth", "locale": "en"})
        if sched_state.get("callback") == "eventClick":
            st.query_params["date"] = sched_state["eventClick"]["event"]["extendedProps"]["date"]
            st.rerun()
else:
    st.title("Archive (  •  ³  •  )")
    
    # 드롭다운 태그 필터 (검색창과 별개로 작동)
    all_tags_for_dropdown = sorted(list(set([t for item in filtered_gallery for t in item['tags']])))
    selected_tag_dropdown = st.sidebar.selectbox("드롭다운 태그 선택", ["전체 보기"] + all_tags_for_dropdown)

    query_date = st.query_params.get("date")
    cal_state = calendar(options={"contentHeight": 350, "selectable": True, "locale": "en"})
    
    display_data = filtered_gallery
    
    # 드롭다운 필터 적용
    if selected_tag_dropdown != "전체 보기":
        display_data = [d for d in display_data if selected_tag_dropdown in d['tags']]
        
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
        st.subheader(f"🖼️ {selected_tag_dropdown if selected_tag_dropdown != '전체 보기' else '전체'} ({len(display_data)}장)")

    cols = st.columns(3)
    # [로딩 애니메이션] 사진이 로딩될 때 스피너 대신 사슴 아이콘
    with st.spinner("사진 불러오는 중..."):
        for idx, item in enumerate(display_data):
            with cols[idx % 3]:
                st.image(item['url'], caption=item['date'], use_container_width=True)
