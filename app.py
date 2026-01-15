import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# 1. 설정 및 노션 연결
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Archive", layout="wide")

# [디자인] 달력 및 전체 톤앤매너 통합 CSS
st.markdown("""
    <style>
    .stApp { background-color: #1a1b26; color: #a9b1d6; }
    h1, h2, h3 { color: #7aa2f7 !important; }
    iframe { background-color: #24283b !important; border-radius: 15px !important; border: 1px solid #414868 !important; }
    
    /* 이미지 카드 스타일 */
    [data-testid="stImage"] img {
        border-radius: 12px;
        aspect-ratio: 1/1;
        object-fit: cover;
        border: 2px solid #414868;
        transition: transform 0.2s;
    }
    [data-testid="stImage"] img:hover { transform: scale(1.03); border-color: #7aa2f7; }
    [data-testid="stImageCaption"] { color: #9ece6a !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=600)
def get_data():
    img_data = []
    try:
        results = notion.databases.query(database_id=DATABASE_ID).get("results")
        for page in results:
            page_id = page["id"]
            props = page.get('properties', {})
            date_str = props.get('날짜', {}).get('date', {}).get('start') or "날짜미상"
            
            # [수정] '스케줄'과 'tag' 두 곳에서 태그 데이터 수집
            sched_info = props.get('스케줄', {}).get('multi_select', [])
            tag_info = props.get('tag', {}).get('multi_select', [])
            
            # 두 속성의 이름을 합치고 중복 제거
            combined_tags = list(set([s['name'] for s in sched_info] + [t['name'] for t in tag_info]))
            
            blocks = notion.blocks.children.list(block_id=page_id).get("results")
            for block in blocks:
                if block["type"] == "image":
                    img_block = block["image"]
                    url = img_block.get('file', {}).get('url') or img_block.get('external', {}).get('url')
                    if url: 
                        img_data.append({
                            "url": url, 
                            "date": date_str, 
                            "all_tags": combined_tags
                        })
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
    return img_data

st.title("Archive (  •  ³  •  )")

with st.spinner('데이터 동기화 중...'):
    data = get_data()

# 사이드바 필터 (스케줄 + tag 통합 목록)
with st.sidebar:
    st.header("🔍 Search Sungchan")
    # 모든 사진에 붙은 태그들을 모아서 정렬
    unique_tags = sorted(list(set([tag for item in data for tag in item['all_tags']])))
    selected_tag = st.selectbox("🏷️ 태그/스케줄 선택", ["전체 보기"] + unique_tags)

# 2. 달력 표시
calendar_options = {
    "contentHeight": 350,
    "selectable": True,
    "headerToolbar": {"left": "prev,next", "center": "title", "right": "today"},
}
state = calendar(options=calendar_options)

# 3. 사진 필터링 로직
display_data = data

# 태그 필터링 (스케줄이나 tag 중 어디에든 포함되어 있으면 출력)
if selected_tag != "전체 보기":
    display_data = [d for d in display_data if selected_tag in d['all_tags']]

# 날짜 필터링
title_text = f"🖼️ {selected_tag}"
if state.get("callback") == "dateClick":
    click_date = (datetime.strptime(state["dateClick"]["date"].split("T")[0], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    display_data = [d for d in display_data if d['date'] == click_date]
    title_text = f"📅 {click_date} 결과"

st.markdown(f"### {title_text} ({len(display_data)}장)")

# 4. 바둑판 출력
if display_data:
    cols = st.columns(3)
    for idx, item in enumerate(display_data):
        with cols[idx % 3]:
            st.image(item['url'], caption=item['date'], use_container_width=True)
else:
    st.warning("Unknown Sungchan..")


