import streamlit as st
from notion_client import Client
from streamlit_calendar import calendar

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

# [테스트용] 노션에서 가져온 날짜들이 어떤 모양인지 화면에 보여줍니다
all_dates = list(set([item['date'] for item in data if item['date']]))
st.write(f"현재 노션에 등록된 날짜들: {all_dates}")

calendar_options = {"contentHeight": 400, "selectable": True}
state = calendar(options=calendar_options)

if state.get("callback") == "dateClick":
    # 보정 없이 클릭한 날짜 그대로 가져오기
    selected_date = state["dateClick"]["date"].split("T")[0]
    st.markdown(f"### 📅 클릭한 날짜: {selected_date}")
    
    filtered_imgs = [item['url'] for item in data if item['date'] == selected_date]
    
    if filtered_imgs:
        st.image(filtered_imgs[0], use_container_width=True)
    else:
        st.info(f"이 날짜({selected_date})와 일치하는 사진이 데이터에 없어요.")
