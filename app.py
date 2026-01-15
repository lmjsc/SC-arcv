# --- 페이지 2: 스케줄 달력 (디자인 통합 및 속성명 수정) ---
else:
    st.markdown("<h1 style='text-align: center;'>Sungchan Schedule 🗓️</h1>", unsafe_allow_html=True)
    
    # 데이터 가져오기
    try:
        raw_schedule = notion.databases.query(database_id=SCHEDULE_DB_ID).get("results")
        schedule_events = []
        
        for page in raw_schedule:
            props = page.get('properties', {})
            
            # 1. 제목 가져오기 (속성명: '스케줄명')
            title_prop = props.get('스케줄명', {})
            title_list = title_prop.get('title', [])
            title = title_list[0].get('plain_text', '제목없음') if title_list else '제목없음'

            # 2. 오프라인 필터 (수식 - 체크박스 대응)
            offline_prop = props.get('오프라인', {})
            is_offline = False
            if offline_prop.get('type') == 'formula':
                is_offline = offline_prop.get('formula', {}).get('boolean', False)
            elif offline_prop.get('type') == 'checkbox':
                is_offline = offline_prop.get('checkbox', False)

            # 3. 날짜 및 이벤트 추가 (오프라인 체크된 것만!)
            if is_offline:
                date_info = props.get('날짜', {}).get('date', {})
                if date_info:
                    schedule_events.append({
                        "title": title,
                        "start": date_info.get('start'),
                        "end": date_info.get('end'),
                        "color": "#7aa2f7",      # 스케줄 바 색상 (하늘색)
                        "textColor": "#ffffff"   # 글자색 (흰색)
                    })
        
        # 달력 디자인 설정 (배경색 일체감 부여)
        calendar_options = {
            "contentHeight": 650,
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,dayGridWeek"
            },
            "initialView": "dayGridMonth",
            "locale": "en",
            "dayMaxEvents": True, # 이벤트가 많으면 'more'로 표시
        }
        
        # 커스텀 CSS로 달력 내부 텍스트 시인성 확보
        st.markdown("""
            <style>
            .fc-event-title { font-weight: bold !important; padding: 2px !important; }
            .fc-daygrid-event { border-radius: 4px !important; border: none !important; }
            </style>
        """, unsafe_allow_html=True)

        calendar(events=schedule_events, options=calendar_options)
        
        if not schedule_events:
            st.info("현재 체크된 '오프라인' 스케줄이 없습니다.")
        else:
            st.success(f"총 {len(schedule_events)}개의 오프라인 스케줄을 불러왔습니다.")

    except Exception as e:
        st.error(f"스케줄 로드 중 오류 발생: {e}")
