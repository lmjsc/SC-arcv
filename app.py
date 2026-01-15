import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar

# 1. 설정값 및 레이아웃 (centered로 변경해서 크기 최적화)
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="Sungchan-Archive", layout="centered")

def get_data():
    img_data = []
    # 최신 라이브러리 문법 적용
    response = notion.databases.query(database_id=DATABASE_ID)
    results = response.get("results", [])
    
    for page in results:
        props = page.get('properties', {})
        # '날짜' 정보 가져오기
        date_info = props.get('날짜', {}).get('date')
        date_str = date_info.get('start') if date_info else None
        
        # 'img' 또는 '파일 및 미디어'에서 사진 가져오기
        # (앞서 확인하신 속성 이름 'img'를 기준으로 작성했습니다)
        files = props.get('img', {}).get('files', [])
        for f in files:
            url = f.get('file', {}).get('url') or f.get('external', {}).get('url')
            if url:
                img_data.append({"url": url, "date": date_str})
    return img_data

st.title("성찬 갤러리 (  •  ³  •  )")

data = get_data()

# 3. 달력 설정 (높이 조절 및 시간대 고정)
calendar_options = {
    "contentHeight": 400, # 달력 높이를 줄여서 한눈에 들어오게 함
    "initialView": "dayGridMonth",
    "selectable": True,
    "headerToolbar": {
        "left": "prev,next",
        "center": "title",
        "right": "today",
    },
}

# 달력 생성
state = calendar(options=calendar_options)

# 4. 날짜 클릭 이벤트 처리 (날짜 밀림 방지 로직)
if state.get("callback") == "dateClick":
    # 클릭한 날짜에서 시간 정보를 제외하고 날짜만 추출
    raw_date = state["dateClick"]["date"]
    selected_date = raw_date.split("T")[0] 
    
    st.markdown(f"### 📅 {selected_date} 사진첩")
    
    # 필터링
    filtered_imgs = [item['url'] for item in data if item['date'] == selected_date]
    
    if filtered_imgs:
        # 사진이 여러 장일 경우 넘겨보기
        if len(filtered_imgs) > 1:
            idx = st.select_slider(f"총 {len(filtered_imgs)}장 중 선택", options=range(len(filtered_imgs)))
            st.image(filtered_imgs[idx], use_container_width=True)
        else:
            st.image(filtered_imgs[0], use_container_width=True)
    else:
        st.info("이 날짜에는 등록된 사진이 없어요.")
else:
    st.info("달력에서 날짜를 누르면 해당 날짜의 사진이 나타납니다!")
