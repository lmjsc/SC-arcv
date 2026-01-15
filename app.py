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
    try:
        results = notion.databases.query(database_id=DATABASE_ID).get("results")
        
        for page in results:
            page_id = page["id"]
            props = page.get('properties', {})
            
            # [날짜 가져오기]
            date_info = props.get('날짜', {}).get('date')
            date_str = date_info.get('start') if date_info else None
            
            # [사진 가져오기 1: '파일 및 미디어' 열 확인]
            files = props.get('파일 및 미디어', {}).get('files', [])
            for f in files:
                url = f.get('file', {}).get('url') or f.get('external', {}).get('url')
                if url: img_data.append({"url": url, "date": date_str})
            
            # [사진 가져오기 2: 페이지 본문(Block) 확인]
            blocks = notion.blocks.children.list(block_id=page_id).get("results")
            for block in blocks:
                if block["type"] == "image":
                    img_block = block["image"]
                    url = img_block.get('file', {}).get('url') or img_block.get('external', {}).get('url')
                    if url: img_data.append({"url": url, "date": date_str})
                    
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
    return img_data

st.title("성찬 갤러리 (  •  ³  •  )")

data = get_data()

# 달력 설정
calendar_options = {
    "contentHeight": 400,
    "selectable": True,
    "headerToolbar": {"left": "prev,next", "center": "title", "right": "today"},
}

state = calendar(options=calendar_options)

# 2. 날짜 클릭 및 사진 표시
if state.get("callback") == "dateClick":
    click_raw = state["dateClick"]["date"]
    click_dt = datetime.fromisoformat(click_raw.replace("Z", "+00:00"))
    # 12시간 보정으로 날짜 밀림 방지
    corrected_dt = click_dt + timedelta(hours=12)
    selected_date = corrected_dt.strftime("%Y-%m-%d")
    
    st.markdown(f"### 📅 {selected_date} 사진첩")
    
    # 해당 날짜 사진 필터링
    filtered_imgs = [item['url'] for item in data if item['date'] == selected_date]
    
    if filtered_imgs:
        if len(filtered_imgs) > 1:
            idx = st.select_slider(f"총 {len(filtered_imgs)}장", options=range(len(filtered_imgs)))
            st.image(filtered_imgs[idx], use_container_width=True)
        else:
            st.image(filtered_imgs[0], use_container_width=True)
    else:
        # 등록된 날짜 목록 보여주기 (디버깅용)
        dates = list(set([item['date'] for item in data if item['date']]))
        st.info(f"{selected_date}에 사진이 없어요. (등록된 날짜들: {dates})")
else:
    st.info("달력에서 날짜를 누르면 사진이 보입니다!")
