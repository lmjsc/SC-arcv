import streamlit as st
from notion_client import Client

# 1. 보안 설정에서 정보 가져오기
try:
    NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
    DATABASE_ID = st.secrets["DATABASE_ID"]
    notion = Client(auth=NOTION_TOKEN)
except Exception as e:
    st.error("Secrets 설정을 확인해 주세요!")

# 2. 사진 가져오기 함수 (최신 버전 문법으로 수정)
def get_images():
    try:
        # 최신 버전은 notion.databases.query(...) 형식을 사용합니다.
        # 만약 여기서 에러가 나면 괄호 위치 문제일 수 있어 안전하게 작성했습니다.
        response = notion.databases.query(database_id=DATABASE_ID)
        return response.get("results", [])
    except Exception as e:
        st.error(f"노션 연결 에러 발생: {e}")
        return []

st.title("My RIIZE Album (  •  ³  •  )")

raw_results = get_images()

if raw_results:
    img_urls = []
    for page in raw_results:
        # 수정 전: props.get('사진', {})
        # 수정 후: props.get('img', {})
        props = page.get('properties', {})
        photo_attr = props.get('img', {})  # <--- 이 부분을 'img'로 수정!
        files = photo_attr.get('files', [])
        
        if files:
            # 이미지 타입에 따라 URL 가져오기
            file_info = files[0]
            if file_info['type'] == 'file':
                img_urls.append(file_info['file']['url'])
            else:
                img_urls.append(file_info['external']['url'])
    
    if img_urls:
        if 'idx' not in st.session_state:
            st.session_state.idx = 0
            
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ 이전"):
                st.session_state.idx = (st.session_state.idx - 1) % len(img_urls)
        with col3:
            if st.button("다음 ➡️"):
                st.session_state.idx = (st.session_state.idx + 1) % len(img_urls)
        
        st.image(img_urls[st.session_state.idx], use_container_width=True)
        st.write(f"📸 {st.session_state.idx + 1} / {len(img_urls)}")
    else:
        st.warning("노션 DB에 '사진' 속성은 있는데, 안에 이미지가 올라와 있지 않아요!")
else:
    st.info("노션에서 데이터를 가져오지 못했습니다. ID와 '연결 추가'를 다시 확인해주세요.")

