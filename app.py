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

# [디자인] 사이드바 캘린더 크기 조절 및 디자인 CSS
st.markdown("""
    <style>
    .stApp { background-color: #1a1b26; color: #a9b1d6; }
    [data-testid="stSidebar"] { background-color: #1f2335 !important; border-right: 1px solid #414868; width: 350px !important; }
    [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] span { color: #ffffff !important; font-weight: 500 !important; }
    [data-testid="stImage"] img { border-radius: 15px; aspect-ratio: 1/1; object-fit: cover; border: 2px solid #414868; transition: 0.3s ease; }
    /* 사이드바 내 캘린더 폰트 크기 축소 */
    [data-testid="stSidebar"] iframe { height: 300px !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_all_data():
    # ... (100장 제한 해제 pagination 로직 포함된 이전 get_all_data 함수 내용 그대로 사용) ...
    # (내용이 길어 생략하지만, 실제 코드에는 위에서 만든 while 루프가 다 들어가야 합니다!)
    # 여기서는 편의상 구조만 표시합니다.
    g_data = [] # 모든 사진 데이터 수집 루프
    s_events = [] # 모든 스케줄 데이터 수집 루프
    # (위의 pagination 코드를 여기에 붙여넣으세요)
    return g_data, s_events

with st.spinner('🦌 데이터 동기화 중...'):
    gallery_data, schedule_events = get_all_data()

# 사이드바 구성
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🦌 Sungchan Menu</h2>", unsafe_allow_html=True)
    
    if st.button("🔄 데이터 강제 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    # [핵심] 사이드바 미니 캘린더 (날짜 이동 컨트롤러)
    st.markdown("📅 **빠른 날짜 이동**")
    side_cal = calendar(
        events=schedule_events,
        options={
            "initialView": "dayGridMonth",
            "headerToolbar": {"left": "prev", "center": "title", "right": "next"},
            "contentHeight": "auto",
            "locale": "en",
            "selectable": True,
        },
        key="side_cal" # 메인 달력과 구분하기 위한 키
    )
    
    st.markdown("---")
    search_query = st.text_input("🔍 착장 검색", "").lower()
    years = sorted(list(set([d['date'].split('-')[0] for d in gallery_data if d['date'] != "날짜미상"])), reverse=True)
    sel_year = st.selectbox("📅 연도 선택", ["전체"] + years)
    show_only_star = st.checkbox("⭐ Favorite SC")

# --- 날짜 로직 처리 ---
query_date = st.query_params.get("date")
active_date = None

# 사이드바 달력 클릭 감지
if side_cal.get("callback") == "dateClick":
    active_date = (datetime.strptime(side_cal["dateClick"]["date"].split("T")[0], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    st.query_params["date"] = active_date
elif side_cal.get("callback") == "eventClick":
    active_date = side_cal["eventClick"]["event"]["extendedProps"]["date"]
    st.query_params["date"] = active_date
elif query_date:
    active_date = query_date

# 필터링
filtered_gallery = gallery_data
if show_only_star: filtered_gallery = [d for d in filtered_gallery if "⭐" in d['tags']]
if sel_year != "전체": filtered_gallery = [d for d in filtered_gallery if d['date'].startswith(sel_year)]
if search_query: filtered_gallery = [d for d in filtered_gallery if search_query in d['search_text']]

# 메인 화면
st.title("Sungchan Archive (  •  ³  •  )")

if active_date:
    display_data = [d for d in filtered_gallery if d['date'] == active_date]
    st.subheader(f"📅 {active_date} 검색 결과 ({len(display_data)}장)")
    if st.button("⬅️ 전체 보기로 돌아가기"):
        st.query_params.clear()
        st.rerun()
else:
    display_data = filtered_gallery
    st.subheader(f"🖼️ 전체 사진 ({len(display_data)}장)")

# 사진 그리드
if not display_data:
    st.info("해당 날짜나 조건에 맞는 사진이 없습니다. 🦌")
else:
    cols = st.columns(3)
    for idx, item in enumerate(display_data):
        with cols[idx % 3]:
            st.image(item['url'], caption=item['date'], use_container_width=True)
