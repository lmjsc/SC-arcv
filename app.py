import streamlit as st
from notion_client import Client

# 노션 설정
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]

notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="RIIZE Album", layout="centered")

def get_images():
    results = notion.databases.query(database_id=DATABASE_ID).get("results")
    img_urls = []
    for page in results:
        # '사진'이라는 이름의 Files&Media 속성이 있다고 가정
        files = page['properties'].get('사진', {}).get('files', [])
        if files:
            img_urls.append(files[0]['file']['url'])
    return img_urls

st.title("My RIIZE Album (  •  ³  •  )")

images = get_images()

if not images:
    st.warning("노션 DB에 '사진' 속성을 만들고 이미지를 올려주세요!")
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

    st.image(images[st.session_state.idx], use_container_width=True)
    st.write(f"현재 {st.session_state.idx + 1} / {len(images)}")