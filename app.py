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

calendar_options = {
    "contentHeight": 400,
    "initialView": "dayGridMonth",
    "selectable": True,
    "headerToolbar": {
        "left": "prev,next",
        "center": "title",
        "right": "today",
    },
}

state = calendar(options=calendar_options)

# 2. 날짜 클릭 이벤트 처리 (보정 로직 추가)
if state.get("callback") == "dateClick":
    # 클릭한 날짜를 가져옴
    clicked_date_str = state["dateClick"]["date"].split("T")[0]
    
    # [핵심] 하루가 밀리는 현상을 해결하기 위해 1일을 더해줍니다.
    clicked_date_obj = datetime.strptime(clicked_date_str, "%Y-%m-%d")
    corrected_date_obj = clicked_date_obj + timedelta(days=1)
    selected_date = corrected_date_obj.strftime("%Y-%m-%d")
    
    st.markdown(f"### 📅 {selected_date} 사진첩")
    
    # 노션 데이터와 비교 (문자열 대 문자열 비교)
    filtered_imgs = [item['url'] for item in data if item['date'] == selected_date]
    
    if filtered_imgs:
        if len(filtered_imgs) > 1:
            idx = st.select_slider(f"총 {len(filtered_imgs)}장", options=range(len(filtered_imgs)), key="img_slider")
            st.image(filtered_imgs[idx], use_container_width=True)
        else:
            st.image(filtered_imgs[0], use_container_width=True)
    else:
        st.info(f"{selected_date}에 등록된 사진이 없습니다. 노션 날짜를 확인해 보세요!")
else:
    st.info("날짜를 누르면 해당 날짜의 성찬이 사진이 나옵니다!")
