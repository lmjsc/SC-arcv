import streamlit as st
from notion_client import Client

# 1. 설정값 가져오기
try:
    NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
    DATABASE_ID = st.secrets["DATABASE_ID"]
    # 클라이언트 생성
    notion = Client(auth=NOTION_TOKEN)
except Exception as e:
    st.error("Secrets 설정을 확인해 주세요!")

# 2. 사진 가져오기 함수 (안전한 문법)
def get_images():
    img_urls = []
    try:
        # notion.databases.query(...) 호출 방식을 조금 더 명확하게 작성
        response = notion.databases.query(**{"database_id": DATABASE_ID})
        results = response.get("results", [])
        
        for page in results:
            props = page.get('properties', {})
            # 'img'라는 이름의 속성 확인
            photo_attr = props.get('img', {})
            files = photo_attr.get('files', [])
            
            for f in files:
                # 노션 업로드 파일 또는 외부 링크 URL 추출
                url = f.get('file', {}).get('url') or f.get('external', {}).get('url')
                if url: img_urls.append(url)
                
    except Exception as e:
        # 에러가 나면 화면에 표시
        st.error(f"노션 연결 상세 에러: {e}")
        return []
    return img_urls

st.title("My RIIZE Album (  •  ³  •  )")

images = get_images()

if not images:
    st.info("사진을 불러오지 못했습니다. 노션 페이지 우측 상단 '...' -> '연결 추가'에 내 봇이 있는지 다시 확인해 보세요!")
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
    st.write(f"📸 현재 {st.session_state.idx + 1} / {len(images)}")
