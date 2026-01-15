import streamlit as st
from notion_client import Client

# 노션 설정 (Secrets에서 안전하게 가져오기)
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]

notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="RIIZE Album", layout="centered")

def get_images():
    # 최신 문법에 맞춰 .get("results")를 한 번에 처리
    results = notion.databases.query(database_id=DATABASE_ID).get("results")
    img_urls = []
    for page in results:
        # 속성 이름을 'img'로 변경했습니다!
        files = page['properties'].get('img', {}).get('files', [])
        if files:
            # 노션 자체 업로드 파일과 외부 링크 파일 모두 대응
            file_info = files[0]
            if file_info['type'] == 'file':
                img_urls.append(file_info['file']['url'])
            else:
                img_urls.append(file_info['external']['url'])
    return img_urls

st.title("My RIIZE Album (  •  ³  •  )")

# 이미지 가져오기 실행
try:
    images = get_images()
except Exception as e:
    st.error(f"연결 에러: {e}")
    images = []

if not images:
    st.warning("노션 DB의 'img' 칸에 사진을 올려주세요! (혹은 '연결 추가' 확인)")
else:
    # 사진 넘기기 로직
    if 'idx' not in st.session_state:
        st.session_state.idx = 0

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ 이전"):
            st.session_state.idx = (st.session_state.idx - 1) % len(images)
    with col3:
        if st.button("다음 ➡️"):
            st.session_state.idx = (st.session_state.idx + 1) % len(images)

    # 선택된 사진 보여주기
    st.image(images[st.session_state.idx], use_container_width=True)
    st.write(f"현재 {st.session_state.idx + 1} / {len(images)}")
