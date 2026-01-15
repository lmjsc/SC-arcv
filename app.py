import streamlit as st
from notion_client import Client

# 설정 읽기
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
notion = Client(auth=NOTION_TOKEN)

st.set_page_config(page_title="RIIZE Album", layout="centered")

def get_images():
    img_urls = []
    # 최신 버전 문법으로 쿼리 실행
    results = notion.databases.query(database_id=DATABASE_ID).get("results")
    
    for page in results:
        page_id = page["id"]
        
        # 1. 'img' 속성(칸)에서 사진 찾기
        props = page.get('properties', {})
        photo_attr = props.get('img', {})
        files = photo_attr.get('files', [])
        for f in files:
            url = f.get('file', {}).get('url') or f.get('external', {}).get('url')
            if url: img_urls.append(url)
        
        # 2. 본문(원문)에서 사진 찾기 (추가된 기능!)
        blocks = notion.blocks.children.list(block_id=page_id).get("results")
        for block in blocks:
            if block["type"] == "image":
                img_block = block["image"]
                url = img_block.get('file', {}).get('url') or img_block.get('external', {}).get('url')
                if url: img_urls.append(url)
                
    return img_urls

st.title("My RIIZE Album (  •  ³  •  )")

try:
    images = get_images()
    if not images:
        st.warning("사진을 찾지 못했습니다. 'img' 칸에 사진을 넣거나 원문에 이미지를 추가해 보세요!")
    else:
        if 'idx' not in st.session_state: st.session_state.idx = 0
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ 이전"): st.session_state.idx = (st.session_state.idx - 1) % len(images)
        with col3:
            if st.button("다음 ➡️"): st.session_state.idx = (st.session_state.idx + 1) % len(images)

        st.image(images[st.session_state.idx], use_container_width=True)
        st.write(f"현재 {st.session_state.idx + 1} / {len(images)} 개의 사진 발견")
except Exception as e:
    st.error(f"에러 발생: {e}")
