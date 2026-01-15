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

# [디자인] 사이드바 시인성 강화
st.markdown("""
    <style>
    .stApp { background-color: #1a1b26; color: #a9b1d6; }
    [data-testid="stSidebar"] { background-color: #1f2335 !important; border-right: 1px solid #414868; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { color: #ffffff !important; }
    [data-testid="stImage"] img { border-radius: 15px; aspect-ratio: 1/1; object-fit: cover; border: 2px solid #414868; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60) # 1분마다 자동 새로고침 체크
def get_all_data():
    # 갤러리 데이터
    res_g = notion.databases.query(database_id=GALLERY_DB_ID).get("results")
    g_data = []
    for page in res_g:
        props = page.get('properties', {})
        date = props.get('날짜', {}).get('date', {}).get('start') or "날짜미상"
        s_tags = props.get('스케줄', {}).get('multi_select', [])
        t_tags = props.get('tag', {}).get('multi_select', [])
        tags_list = [s['name'] for s in s_tags] + [t['name'] for t in t_tags]
        search_text = " ".join(tags_list).lower()
        
        # --- 이미지 추출 로직 (본문 + 파일 열 둘다 체크) ---
        img_urls = []
        
        # 1. '파일과 미디어' 타입의 모든 열을 뒤져서 이미지 찾기
        for p_val in props.values():
            if p_val.get('type') == 'files':
                for f in p_val.get('files', []):
                    url = f.get('file', {}).get('url') or f.get('external', {}).get('url')
                    if url: img_urls.append(url)
        
        # 2. 본문에 있는 이미지 찾기 (이미 위에서 찾았으면 생략 가능하지만 안전하게 추가)
        blocks = notion.blocks.children.list(block_id=page['id']).get("results")
        for block in blocks:
            if block["type"] == "image":
                url = block["image"].get('file', {}).get('url') or block["image"].get('external', {}).get('url')
                if url: img_urls.append(url)
        
        # 중복 제거 후 데이터 추가
        for final_url in list(set(img_urls)):
            g_data.append({"url": final_url, "date": date, "tags": tags_list, "search_text": search_text})
    
    # 스케줄 데이터
    res_s = notion.databases.query(database_id=SCHEDULE_DB_ID).get("results")
    s_events = []
    for page in res_s:
        props = page.get('properties', {})
        title_list = props.get('스케줄명', {}).get('title', [])
        title = title_list[0].get('plain_text', '제목없음') if title_list else '제목없음'
        is_off = props.get('오프라인', {}).get('formula', {}).get('boolean', False)
        date_info = props.get('날짜', {}).get('date', {})
        if is_off and date_info:
            s_events.append({"title": title, "start": date_info.get('start'), "end": date_info.get('end'), "color": "#7aa2f7", "extendedProps": {"date": date_info.get('start')}})
            
    return g_data, s_events

with st.spinner('🦌 성찬이 데이터 불러오는 중...'):
    gallery_data, schedule_events = get_all_data()

with st.sidebar:
    st.markdown("## 🦌 Sungchan Menu")
    if st.button("🔄 데이터 강제 새로고침"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    menu = st.radio("이동할 페이지", ["📅 스케줄 달력", "🖼️ 사진 갤러리"])
    search_query = st.text_input("🔍 착장 검색", "").lower()
    years = sorted(list(set([d['date'].split('-')[0] for d in gallery_data if d['date'] != "날짜미상"])), reverse=True)
    sel_year = st.selectbox("📅 연도 선택", ["전체"] + years)
    show_only_star = st.checkbox("⭐ 레전드만 보기")

# 필터링 및 출력 (기존과 동일)
filtered_gallery = gallery_data
if show_only_star: filtered_gallery = [d for d in filtered_gallery if "⭐" in d['tags']]
if sel_year != "전체": filtered_gallery = [d for d in filtered_gallery if d['date'].startswith(sel_year)]
if search_query: filtered_gallery = [d for d in filtered_gallery if search_query in d['search_text']]

if menu == "📅 스케줄 달력":
    st.title("Sungchan Schedule 🗓️")
    calendar(events=schedule_events, options={"contentHeight": 650, "initialView": "dayGridMonth", "locale": "en"})
else:
    st.title("Archive (  •  ³  •  )")
    cols = st.columns(3)
    for idx, item in enumerate(filtered_gallery):
        with cols[idx % 3]:
            st.image(item['url'], caption=item['date'], use_container_width=True)
