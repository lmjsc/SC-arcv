import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime

# 1. 설정값 가져오기
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Sungchan-Archive", layout="wide")

# 2. 데이터 가져오기 (날짜 정보 포함)
def get_data():
    img_data = []
    results = notion.databases.query(database_id=DATABASE_ID).get("results")
    
    for page in results:
        props = page.get('properties', {})
        # '날짜' 속성 가져오기 (노션의 열 이름이 '날짜'여야 합니다)
        date_info = props.get('날짜', {}).get('date')
        date_str = date_info.get('start') if date_info else None
        
        # 'img' 속성에서 사진 가져오기
        files = props.get('img', {}).get('files', [])
        for f in files:
            url = f.get('file', {}).get('url') or f.get('external', {}).get('url')
            if url:
                img_data.append({"url": url, "date": date_str})
    return img_data

st.title("성찬 갤러리 달력 (  •  ³  •  )")

data = get_data()

# 3. 달력 표시 설정
calendar_options = {
    "editable": False,
    "selectable": True,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth",
    },
}

# 달력 생성 및 클릭 이벤트 감지
state = calendar(options=calendar_options)

# 4. 날짜 클릭 시 사진 필터링
if state.get("callback") == "dateClick":
    selected_date = state["dateClick"]["date"].split("T")[0] # 클릭한 날짜 (YYYY-MM-DD)
    st.subheader(f"📅 {selected_date} 사진")
    
    # 해당 날짜의 사진만 필터링
    filtered_imgs = [item['url'] for item in data if item['date'] == selected_date]
    
    if filtered_imgs:
        # 사진이 여러 장일 수 있으므로 슬라이더로 표시
        idx = st.select_slider("사진 선택", options=range(len(filtered_imgs)), key="filter_slider")
        st.image(filtered_imgs[idx], use_container_width=True)
    else:
        st.info("이 날짜에는 등록된 사진이 없어요.")
else:
    st.info("달력에서 날짜를 클릭하면 그날의 사진이 나옵니다!")
