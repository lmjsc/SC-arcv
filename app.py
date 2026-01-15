import streamlit as st
from notion_client import Client

# 설정값 가져오기
try:
    NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
    DATABASE_ID = st.secrets["DATABASE_ID"]
    # 최신 라이브러리 방식에 맞춰 수정
    notion = Client(auth=NOTION_TOKEN)
except Exception as e:
    st.error("Secrets 설정을 확인해 주세요!")

def get_images():
    img_urls = []
    try:
        # 데이터베이스 정보를 가져옵니다
        response = notion.databases.query(database_id=DATABASE_ID)
        results = response.get("results", [])
        
        for page in results:
            props = page.get('properties', {})
            
            # 중요! 노션 표의 제목이 '파일 및 미디어'라면 아래와 같이 써야 합니다.
            # 만약 제목이 'img'라면 'img'로 써주세요.
            photo_attr = props.get('파일 및 미디어', {}) 
            files = photo_attr.get('files', [])
            
            for f in files:
                url = f.get('file', {}).get('url') or f.get('external', {}).get('url')
                if url:
                    img_urls.append(url)
                    
    except Exception as e:
        st.error(f"노션 연결 상세 에러: {e}")
        return []
    return img_urls

st.title("성찬 갤러리 (  •  ³  •  )")

images = get_images()

if not images:
    st.info("데이터베이스에서 사진을 찾지 못했습니다. '파일 및 미디어' 열 이름을 확인해 보세요!")
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

    st.image(images[st.session_state.idx], use_container_width=True)
    st.write(f"📸 {st.session_state.idx + 1} / {len(images)}")
