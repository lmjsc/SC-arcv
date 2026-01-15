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

# [보안] 검색 엔진 수집 차단
st.markdown('<head><meta name="robots" content="noindex, nofollow"></head>', unsafe_allow_html=True)

# [디자인] 버튼 간격 및 시인성 정밀 조정
st.markdown("""
    <style>
    .stApp { background-color: #1a1b26; color: #a9b1d6; }
    [data-testid="stSidebar"] { background-color: #1f2335 !important; border-right: 1px solid #414868; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { color: #ffffff !important; }
    
    /* 사이드바 버튼 촘촘하게 만들기 */
    [data-testid="stSidebar"] .stButton button {
        width: 100%;
        padding: 4px 8px !important;
        min-height: 32px !important;
        height: 32px !important;
        background-color: #24283b !important; 
        color: #7aa2f7 !important; 
        border: 1px solid #7aa2f7 !important;
        font-size: 13px !important;
        margin-bottom: -10px !important; /* 버튼 사이 세로 간격 축소 */
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #7aa2f7 !important;
        color: #1a1b26 !important;
    }
    
    /* 이미지 스타일 */
    [data-testid="stImage"] img { border-radius: 12px; aspect-ratio: 1/1; object-fit: cover; border: 2px solid #414868; transition: 0.3s; }
    [data-testid="stImage"] img:hover { transform: scale(1.02); border-color: #7aa2f7; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=10800)
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
            
            # --- 시작일과 종료일을 모두 가져오도록 수정 ---
            date_info = props.get('날짜', {}).get('date', {})
            if is_off and date_info:
                start_val = date_info.get('start')
                end_val = date_info.get('end') # 노션에서 설정한 종료일 가져오기
                
                s_events.append({
                    "title": title, 
                    "start": start_val, 
                    "end": end_val if end_val else start_val, # 종료일이 없으면 시작일과 같게
                    "color": "#7aa2f7", 
                    "extendedProps": {"date": start_val}
                })
        has_more_s = res_s.get("has_more")
        next_cursor_s = res_s.get("next_cursor")
    return g_data, s_events

gallery_data, schedule_events = get_all_data()

# 사이드바 구성
with st.sidebar:
    st.markdown("### 🦌 Sungchan Archive")
    st.markdown("---")
    
    st.markdown("🔍 **Quick Look**")
    # 버튼 간격을 좁히기 위해 columns의 gap을 제거하거나 조절
    c1, c2 = st.columns(2)
    with c1:
        if st.button("#안경"): st.query_params["search"] = "안경"
        if st.button("#공항"): st.query_params["search"] = "공항"
    with c2:
        if st.button("#셀카"): st.query_params["search"] = "셀카"
        if st.button("#공연"): st.query_params["search"] = "공연" # 무대 -> 공연 수정
    
    st.markdown("---")
    years = sorted(list(set([d['date'].split('-')[0] for d in gallery_data if d['date'] != "날짜미상"])), reverse=True)
    sel_year = st.selectbox("📅 연도 선택", ["전체"] + years)
    
    search_query = st.text_input("직접 검색", value=st.query_params.get("search", "")).lower()
    show_only_star = st.checkbox("⭐ Favorite SC")

    # 새로고침 버튼 하단 배치
    st.markdown("<br>" * 10, unsafe_allow_html=True) 
    if st.button("🔄"):
        st.cache_data.clear()
        st.rerun()

# 필터링 및 메인 화면 출력 (기존 로직 동일)
filtered_gallery = gallery_data
if show_only_star: filtered_gallery = [d for d in filtered_gallery if "⭐" in d['tags']]
if sel_year != "전체": filtered_gallery = [d for d in filtered_gallery if d['date'].startswith(sel_year)]
if search_query: filtered_gallery = [d for d in filtered_gallery if search_query in d['search_text']]

st.title("Archive (  •  ³  •  )")
cal_state = calendar(events=schedule_events, options={"contentHeight": 350, "selectable": True, "locale": "en"})

active_date = st.query_params.get("date")
if cal_state.get("callback") == "dateClick":
    active_date = (datetime.strptime(cal_state["dateClick"]["date"].split("T")[0], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
elif cal_state.get("callback") == "eventClick":
    active_date = cal_state["eventClick"]["event"]["extendedProps"]["date"]

if active_date:
    display_data = [d for d in filtered_gallery if d['date'] == active_date]
    st.subheader(f"📅 {active_date} 결과")
    if st.button("⬅️ 전체 보기"): 
        st.query_params.clear()
        st.rerun()
else:
    display_data = filtered_gallery
    st.subheader(f"🖼️ 결과 ({len(display_data)}장)")

if not display_data:
    st.info("해당 조건에 맞는 사진이 없습니다. 🦌")
else:
    cols = st.columns(3)
    for idx, item in enumerate(display_data):
        with cols[idx % 3]:
            st.image(item['url'], caption=item['date'], use_container_width=True)


