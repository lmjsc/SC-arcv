import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# 1. 설정값 가져오기
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Sungchan-Archive", layout="centered")

def get_data():
    img_data = []
    response = notion.databases.query(database_id=DATABASE_ID)
    results = response.get("results", [])
    
    for page in results:
        props = page.get('properties', {})
        date_info = props.get('날짜', {}).get('date')
        date_str = date_info.get('start') if date_info else None
        
        files = props.get('img', {}).get('files', [])
        for f in files:
            url = f.get('file', {}).get('url') or f.get('external', {}).get('url')
            if url:
                img_data.append({"url": url, "date": date_str})
    return img_data

st.title("성찬 갤러리 (  •  ³  •  )")

data = get_data()

# 달력 설정
calendar_options = {
    "contentHeight": 400,
    "selectable": True,
    "headerToolbar": {
        "left": "prev,next",
        "center": "title",
        "right": "today",
    },
}

state = calendar(options=calendar_options)

# 2. 날짜 클릭 이벤트 처리 (강력한 보정 로직)
if state.get("callback") == "dateClick":
    # 1. 클릭한 시각 문자열 가져오기 (예: "2026-01-03T15:00:00.000Z")
    click_raw = state["dateClick"]["date"]
    
    # 2. 날짜 객체로 변환
    # T 이후를 떼고 변환하거나, 아예 시각 정보를 포함해 변환
    click_dt = datetime.fromisoformat(click_raw.replace("Z", "+00:00"))
    
    # 3. [핵심] 12시간을 더해서 한국 시간대 기준으로 날짜가 넘어가게 보정
    # 4일을 눌렀는데 3일 밤으로 인식된다면, 12시간을 더하면 안전하게 4일이 됩니다.
    corrected_dt = click_dt + timedelta(hours=12)
    selected_date = corrected_dt.strftime("%Y-%m-%d")
    
    st.markdown(f"### 📅 선택한 날짜: {selected_date}")
    
    # 노션 데이터와 비교
    filtered_imgs = [item['url'] for item in data if item['date'] == selected_date]
    
    if filtered_imgs:
        if len(filtered_imgs) > 1:
            idx = st.select_slider(f"총 {len(filtered_imgs)}장", options=range(len(filtered_imgs)))
            st.image(filtered_imgs[idx], use_container_width=True)
        else:
            st.image(filtered_imgs[0], use_container_width=True)
    else:
        # 디버깅용: 노션에 있는 날짜 목록 출력
        available_dates = list(set([item['date'] for item in data if item['date']]))
        st.info(f"{selected_date}에 사진이 없어요. (현재 등록된 날짜: {available_dates})")
else:
    st.info("달력에서 날짜를 누르면 사진이 나옵니다!")
