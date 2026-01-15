import streamlit as st
from notion_client import Client

# 1. 설정값 가져오기
try:
    NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
    DATABASE_ID = st.secrets["DATABASE_ID"]
    notion = Client(auth=NOTION_TOKEN)
except Exception as e:
    st.error("Secrets 설정을 확인해 주세요!")

# 2. 사진 가져오기 함수 (최신 문법 적용)
def get_images():
    img_urls = []
    try:
        # 최신 버전에서는 아래와 같이 .databases.query(...)를 호출합니다.
        # 기존 코드에서 오타가 날 수 있는 부분을 안전하게 수정했습니다.
        response = notion.databases.query(database_id=DATABASE_ID)
        results = response.get("results", [])
        
        for page in results:
            props = page.get('properties', {})
            # 'img'라는 이름의 속성을 확인 (없으면 넘어감)
            photo_attr = props.get('img', {})
            files = photo_attr.get('files', [])
            
            for f in files:
                url = f.get('file', {}).get('url') or f.get('external', {}).get('url')
                if url: img_urls.append(url)
                
    except Exception as e:
        st.error(f"노션 연결 에러: {e}")
        return []
    return img_urls

st.title("My RIIZE Album (  •  ³  •  )")

images = get_images()

if not images:
    st.info("사진을 불러오지 못했습니다. 'img' 열 이름과 '연결 추가'를 확인해 보세요!")
else:
    if 'idx' not in st.session_state:
        st.session_state.idx = 0

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ 이전"):
            st.session_state.idx = (st.session_state.idx - 1) % len(images)
    with col3:
        if st.button("다음 ➡️"):
            st.session_state.idx = (st.session_state.idx + 1) % len(images)

    # 이미지 출력
    st.image(images[st.session_state.idx], use_container_width=True)
    st.write(f"현재 {st.session_state.idx + 1} / {len(images)}")
