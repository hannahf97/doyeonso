import streamlit as st
import os
import json
from models.chatbotModel import PIDExpertChatbot
from loguru import logger
import time
from datetime import datetime
from config.database_config import get_db_connection

def show():
    """P&ID 전문가 챗봇 페이지"""
    
    st.title("🔧 P&ID 도면 분석 전문가 챗봇")
    st.markdown("---")
    
    # 챗봇 초기화
    if 'chatbot' not in st.session_state:
        with st.spinner("🤖 P&ID 전문가 챗봇을 초기화하는 중..."):
            st.session_state.chatbot = PIDExpertChatbot()
    
    # 파일 리스트에서 선택된 파일들 확인 및 표시
    if 'selected_files_for_chat' in st.session_state and st.session_state.selected_files_for_chat:
        st.markdown("## 📋 선택된 파일들")
        
        selected_files = st.session_state.selected_files_for_chat
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ **{len(selected_files)}개 파일이 선택되었습니다**")
            
            # 파일 정보를 데이터베이스에서 가져와서 표시
            conn = get_db_connection()
            if conn:
                try:
                    for i, file_info in enumerate(selected_files):
                        with st.expander(f"📄 {file_info['name']}", expanded=False):
                            # 데이터베이스에서 상세 정보 조회
                            file_details = get_file_details(conn, file_info['id'])
                            if file_details:
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.write(f"**ID:** {file_details['id']}")
                                    st.write(f"**사용자:** {file_details['user']}")
                                    st.write(f"**등록일:** {file_details['create_date']}")
                                
                                with col_b:
                                    # JSON 데이터에서 OCR/Detection 정보 추출
                                    if file_details['json_data']:
                                        try:
                                            data = file_details['json_data'] if isinstance(file_details['json_data'], dict) else json.loads(file_details['json_data'])
                                            ocr_count = count_ocr_fields(data)
                                            detection_count = count_detection_objects(data)
                                            
                                            st.write(f"**OCR 필드:** {ocr_count}개")
                                            st.write(f"**Detection 객체:** {detection_count}개")
                                        except:
                                            st.write("**OCR 필드:** 0개")
                                            st.write("**Detection 객체:** 0개")
                                
                                # OCR 텍스트 미리보기
                                if file_details['json_data']:
                                    ocr_text = extract_ocr_text_preview(file_details['json_data'])
                                    if ocr_text:
                                        st.markdown("**📄 OCR 텍스트 미리보기:**")
                                        st.text_area("OCR 텍스트 미리보기", value=ocr_text[:200] + "..." if len(ocr_text) > 200 else ocr_text, height=80, disabled=True, key=f"ocr_preview_{i}", label_visibility="collapsed")
                finally:
                    conn.close()
        
        with col2:
            if st.button("🗑️ 파일 선택 초기화", use_container_width=True):
                st.session_state.selected_files_for_chat = []
                st.rerun()
        
        st.markdown("---")
        
        # 선택된 파일들에 대한 빠른 분석 버튼
        st.markdown("### 🚀 빠른 분석")
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("📋 전체 파일 요약", use_container_width=True):
                _add_test_question(f"선택된 {len(selected_files)}개 파일({', '.join([f['name'] for f in selected_files])})에 대한 종합적인 요약을 제공해주세요.")
        
        with col_b:
            if st.button("🔍 상세 분석", use_container_width=True):
                _add_test_question(f"선택된 파일들({', '.join([f['name'] for f in selected_files])})의 상세 분석을 해주세요. 주요 계측기기, 제어 시스템, 안전장치를 중심으로 설명해주세요.")
        
        with col_c:
            if st.button("⚡ OCR 텍스트 분석", use_container_width=True):
                _add_test_question(f"선택된 파일들의 OCR 텍스트를 분석하여 주요 설비명, 계측기 태그, 제어 포인트를 추출해주세요.")
    
    # 기존 단일 도면 선택 기능 (호환성 유지)
    selected_drawing = st.session_state.get('selected_drawing_name', None)
    
    if selected_drawing and not st.session_state.get('selected_files_for_chat'):
        st.success(f"✅ 선택된 도면: **{selected_drawing}**")
        st.info("💡 이 도면에 대해 질문하시면 데이터베이스의 정보를 활용하여 답변해드립니다.")
        
        # 빠른 도면 요약 버튼
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 선택된 도면 요약", use_container_width=True):
                with st.spinner("도면 요약 생성 중..."):
                    summary_result = st.session_state.chatbot.generate_drawing_summary(
                        selected_drawing, 
                        "latest"
                    )
                    
                    # 요약 결과를 대화에 추가
                    if 'messages' not in st.session_state:
                        st.session_state.messages = []
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": summary_result['response'],
                        "timestamp": datetime.now(),
                        "sources": summary_result.get('sources', []),
                        "debug_info": {
                            "query_type": summary_result.get('query_type'),
                            "context_quality": summary_result.get('context_quality'),
                            "web_search_used": summary_result.get('web_search_used', False)
                        }
                    })
                    
                    st.success("✅ 요약 완료!")
                    st.rerun()
        
        with col2:
            if st.button("🔍 도면 상세 분석", use_container_width=True):
                # 상세 분석 질문을 대화에 추가
                analysis_prompt = f"'{selected_drawing}' 도면의 상세 분석을 해주세요. 주요 계측기기, 제어 시스템, 안전장치를 중심으로 설명해주세요."
                
                if 'messages' not in st.session_state:
                    st.session_state.messages = []
                
                # 사용자 질문 추가
                st.session_state.messages.append({
                    "role": "user",
                    "content": analysis_prompt,
                    "timestamp": datetime.now()
                })
                
                # 자동 응답 생성
                with st.spinner("🤔 상세 분석 중..."):
                    response_data = st.session_state.chatbot.generate_response(
                        analysis_prompt,
                        use_web_search=False,
                        selected_drawing=selected_drawing,
                        selected_files=st.session_state.get('selected_files_for_chat')
                    )
                
                # 어시스턴트 메시지 저장
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_data['response'],
                    "timestamp": datetime.now(),
                    "sources": response_data.get('sources', []),
                    "debug_info": {
                        "query_type": response_data.get('query_type'),
                        "context_quality": response_data.get('context_quality'),
                        "web_search_used": response_data.get('web_search_used', False)
                    }
                })
                
                st.success("✅ 상세 분석 완료!")
                st.rerun()
    
    # 파일이 선택되지 않은 경우
    if not selected_drawing and not st.session_state.get('selected_files_for_chat'):
        st.info("💡 도면을 선택하려면 📋 FILE LIST 페이지로 이동하세요.")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📋 파일 리스트로 이동", use_container_width=True, type="primary"):
                st.session_state['page_view'] = 'filelist'
                st.rerun()

    # 테스트용 질문 버튼들
    st.markdown("## 🧪 테스트 질문")
    st.markdown("아래 버튼을 클릭하여 다양한 질문을 테스트해보세요:")
    
    # 질문 카테고리별로 버튼 배치
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔧 계측기기")
        if st.button("FT-101 설명", key="test_ft101", use_container_width=True):
            _add_test_question("FT-101 계측기의 역할과 위치를 자세히 설명해주세요.")
        
        if st.button("압력 조절 시스템", key="test_pressure", use_container_width=True):
            _add_test_question("압력 조절 시스템(PC)의 구성과 작동 원리를 설명해주세요.")
        
        if st.button("온도 제어", key="test_temp", use_container_width=True):
            _add_test_question("온도 제어 시스템(TC)에서 PID 제어의 역할은 무엇인가요?")
    
    with col2:
        st.markdown("### 🛡️ 안전 시스템")
        if st.button("비상정지 시스템", key="test_esd", use_container_width=True):
            _add_test_question("비상정지(ESD) 시스템의 구성과 작동 순서를 설명해주세요.")
        
        if st.button("안전밸브", key="test_safety_valve", use_container_width=True):
            _add_test_question("안전밸브(PSV)의 설정압력과 동작 원리를 설명해주세요.")
        
        if st.button("인터록 시스템", key="test_interlock", use_container_width=True):
            _add_test_question("공정 인터록 시스템의 종류와 각각의 역할을 설명해주세요.")
    
    with col3:
        st.markdown("### 📊 분석 질문")
        if st.button("제어루프 분석", key="test_control_loop", use_container_width=True):
            _add_test_question("주요 제어루프들의 상호작용과 최적화 방안을 분석해주세요.")
        
        if st.button("운전 절차", key="test_operation", use_container_width=True):
            _add_test_question("정상 운전 시작 절차와 주의사항을 설명해주세요.")
        
        if st.button("도면 시각화", key="test_visualization", use_container_width=True):
            _add_test_question("stream_does_ai_1 도면을 시각화해서 분석해줘")
        
        if st.button("변경사항 비교", key="test_change_comparison", use_container_width=True):
            _add_test_question("stream_dose_ai_1과 stream_dose_ai_3의 변경사항을 비교 분석해주세요.")
        
        if st.button("종합 분석", key="test_comprehensive", use_container_width=True):
            _add_test_question("stream_does_ai_1 도면을 종합적으로 분석해줘")
    
    st.markdown("---")
    
    # 사이드바 설정
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        
        # 선택된 도면 정보
        if selected_drawing:
            st.success(f"📄 선택된 도면")
            st.info(selected_drawing)
        else:
            st.info("📄 도면 미선택")
            st.caption("FILE LIST에서 도면을 선택하세요")
        
        # RAG 시스템 상태 확인
        pdf_path = "data/공정 Description_글.pdf"
        pdf_exists = os.path.exists(pdf_path)
        
        if pdf_exists:
            st.success("✅ PDF 문서 발견")
            st.info(f"📄 {os.path.basename(pdf_path)}")
        else:
            st.error("❌ PDF 문서를 찾을 수 없습니다")
            st.info(f"📂 예상 경로: {pdf_path}")
        
        # 고급 설정
        st.markdown("### 🎛️ 고급 설정")
        use_web_search = st.checkbox("웹 검색 보조 활용", help="RAG 정보가 부족할 때 웹 검색 결과를 보조적으로 활용")
        show_sources = st.checkbox("참고 문서 출처 표시", value=True)
        show_debug_info = st.checkbox("디버그 정보 표시", help="쿼리 유형, 컨텍스트 품질 등 기술 정보 표시")
    
    # RAG 시스템 초기화
    if pdf_exists:
        if 'rag_initialized' not in st.session_state:
            with st.spinner("🤖 RAG 시스템을 초기화하는 중..."):
                success = st.session_state.chatbot.initialize_rag_system(pdf_path)
                if success:
                    st.session_state.rag_initialized = True
                    st.success("✅ RAG 시스템이 성공적으로 초기화되었습니다!")
                else:
                    st.error("❌ RAG 시스템 초기화에 실패했습니다.")
    else:
        st.warning("⚠️ PDF 문서가 없어 RAG 시스템을 초기화할 수 없습니다.")
    
    # 대화 기록 초기화
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        # 환영 메시지
        welcome_message = """
안녕하세요! 저는 P&ID 도면 분석 전문가 챗봇입니다. 🔧

**전문 분야:**
- P&ID 도면 해석 및 분석
- 계측기기 설명 (FT, FC, FV, PT, PC, TT, TC, LT, LC, AT, AC 등)
- 공정제어 시스템 분석
- 안전장치 및 비상정지 시스템 검토
- 도면 변경사항 분석

**질문 예시:**
- "FT-101의 역할은 무엇인가요?"
- "이 공정에서 안전장치는 어떻게 구성되어 있나요?"
- "압력 조절 시스템에 대해 설명해주세요"
- "도면 변경 시 고려해야 할 사항은?"

무엇이든 궁금한 점을 물어보세요!
        """
        st.session_state.messages.append({
            "role": "assistant", 
            "content": welcome_message,
            "timestamp": datetime.now()
        })
    
    # 대화 인터페이스
    st.markdown("### 💬 전문가와 대화하기")
    
    # 대화 기록 표시
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # 타임스탬프 표시
                if "timestamp" in message:
                    st.caption(f"⏰ {message['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 소스 정보 표시
                if show_sources and "sources" in message and message["sources"]:
                    with st.expander("📚 참고 문서 출처"):
                        _display_sources(message["sources"], message.get("debug_info", {}))
                
                # 시각화 결과 표시 (있는 경우)
                if "visualization" in message and message["visualization"]:
                    with st.expander("🖼️ 도면 시각화 결과", expanded=True):
                        _display_visualization(message["visualization"])
                
                # 디버그 정보 표시
                if show_debug_info and "debug_info" in message:
                    debug = message["debug_info"]
                    _display_debug_info(debug)
    
    # 사용자 입력
    if prompt := st.chat_input("P&ID 관련 질문을 입력하세요..."):
        
        # 사용자 메시지 추가
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "timestamp": datetime.now()
        })
        
        # 사용자 메시지 표시
        with st.chat_message("user"):
            st.write(prompt)
            st.caption(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 봇 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("🤔 분석 중..."):
                response_data = st.session_state.chatbot.generate_response(
                    prompt, 
                    use_web_search=use_web_search,
                    selected_drawing=st.session_state.get('selected_drawing_name'),
                    selected_files=st.session_state.get('selected_files_for_chat')
                )
            
            # 응답 표시
            st.write(response_data['response'])
            st.caption(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 소스 정보 표시
            if show_sources and response_data['sources']:
                with st.expander("📚 참고 문서 출처"):
                    _display_sources(response_data['sources'], response_data)
            
            # 시각화 결과 표시 (있는 경우)
            if response_data.get('visualization'):
                with st.expander("🖼️ 도면 시각화 결과", expanded=True):
                    _display_visualization(response_data['visualization'])
            
            # 디버그 정보 표시
            if show_debug_info:
                _display_debug_info(response_data)
        
        # 어시스턴트 메시지 저장
        assistant_message = {
            "role": "assistant",
            "content": response_data['response'],
            "timestamp": datetime.now(),
            "sources": response_data.get('sources', []),
            "debug_info": {
                "query_type": response_data.get('query_type'),
                "context_quality": response_data.get('context_quality'),
                "web_search_used": response_data.get('web_search_used', False),
                "extracted_text_length": response_data.get('extracted_text_length', 0),
                "rag_chunks_count": response_data.get('rag_chunks_count', 0),
                "json_analysis": response_data.get('json_analysis'),
                "similarity_threshold": response_data.get('similarity_threshold')
            }
        }
        
        # 시각화 결과가 있으면 추가
        if response_data.get('visualization'):
            assistant_message["visualization"] = response_data['visualization']
        
        st.session_state.messages.append(assistant_message)
        
        # 페이지 새로고침으로 새 메시지 표시
        st.rerun()
    
    # 하단 유틸리티
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🗑️ 대화 기록 삭제"):
            st.session_state.messages = []
            st.session_state.chatbot.clear_conversation_history()
            st.success("대화 기록이 삭제되었습니다.")
            st.rerun()
    
    with col2:
        if st.button("📊 대화 통계"):
            if hasattr(st.session_state, 'chatbot'):
                summary = st.session_state.chatbot.get_conversation_summary()
                if summary:
                    st.json(summary)
                else:
                    st.info("대화 기록이 없습니다.")
    
    with col3:
        if st.button("💾 대화 내보내기"):
            if hasattr(st.session_state, 'chatbot'):
                export_data = st.session_state.chatbot.export_conversation_history()
                st.download_button(
                    label="📄 다운로드",
                    data=export_data,
                    file_name=f"pid_chatbot_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    
    with col4:
        if st.button("🔄 RAG 시스템 재구축"):
            if pdf_exists:
                with st.spinner("RAG 시스템을 재구축하는 중..."):
                    success = st.session_state.chatbot.rag_system.build_vector_database(pdf_path)
                    if success:
                        st.success("✅ RAG 시스템이 재구축되었습니다!")
                    else:
                        st.error("❌ RAG 시스템 재구축에 실패했습니다.")
            else:
                st.error("PDF 파일을 찾을 수 없습니다.")
    
    # 도움말
    with st.expander("📖 사용법 및 팁"):
        st.markdown("""
        ### 🎯 효과적인 질문 방법
        
        **1. 구체적인 질문하기**
        - ❌ "이게 뭐야?"
        - ✅ "FT-101 계측기의 역할과 위치를 설명해주세요"
        
        **2. 컨텍스트 제공**
        - ❌ "문제가 있어"
        - ✅ "압력 조절 시스템에서 PC-201이 제대로 작동하지 않는 경우 확인해야 할 사항"
        
        **3. 분석 요청**
        - "도면의 안전장치 시스템을 분석해주세요"
        - "이 공정의 제어 로직을 설명해주세요"
        - "비상정지 시퀀스를 검토해주세요"
        
        ### 🔧 지원하는 기능
        - P&ID 도면 해석
        - 계측기기 설명 (FT, FC, FV, PT, PC, TT, TC, LT, LC, AT, AC 등)
        - 공정 안전성 분석
        - 제어 시스템 검토
        - 도면 변경사항 분석
        """)
    
    # 면책사항
    st.markdown("---")
    st.caption("⚠️ 이 챗봇은 보조 도구이며, 중요한 안전 결정은 반드시 전문가와 상의하시기 바랍니다.")

def _add_test_question(question_text):
    """테스트 질문을 대화에 추가하고 자동 응답 생성"""
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # 사용자 질문 추가
    st.session_state.messages.append({
        "role": "user",
        "content": question_text,
        "timestamp": datetime.now()
    })
    
    # 자동 응답 생성
    with st.spinner("🤔 분석 중..."):
        response_data = st.session_state.chatbot.generate_response(
            question_text,
            use_web_search=False,
            selected_drawing=st.session_state.get('selected_drawing_name'),
            selected_files=st.session_state.get('selected_files_for_chat')
        )
    
    # 어시스턴트 메시지 저장
    assistant_message = {
        "role": "assistant",
        "content": response_data['response'],
        "timestamp": datetime.now(),
        "sources": response_data.get('sources', []),
        "debug_info": {
            "query_type": response_data.get('query_type'),
            "context_quality": response_data.get('context_quality'),
            "web_search_used": response_data.get('web_search_used', False),
            "selected_files_count": response_data.get('selected_files_count', 0),
            "files_processed": response_data.get('selected_files_count', 0)  # 이미지 처리 대신 파일 처리 수로 변경
        }
    }
    
    # 시각화 결과가 있으면 추가
    if response_data.get('visualization'):
        assistant_message["visualization"] = response_data['visualization']
    
    st.session_state.messages.append(assistant_message)
    
    # 페이지 새로고침
    st.rerun()

def get_file_details(conn, file_id):
    """데이터베이스에서 파일 상세 정보 조회"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d_id, d_name, "user", create_date, image_path, json_data
            FROM domyun WHERE d_id = %s
        """, (file_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'user': row[2],
                'create_date': row[3],
                'image_path': row[4],
                'json_data': row[5]
            }
        return None
    except Exception:
        return None

def count_ocr_fields(json_data):
    """JSON 데이터에서 OCR 필드 개수 계산"""
    try:
        # 새로운 구조 ('ocr')
        if 'ocr' in json_data and json_data['ocr']:
            ocr_data = json_data['ocr']
            if isinstance(ocr_data, dict) and 'images' in ocr_data:
                total_fields = 0
                for img in ocr_data['images']:
                    if 'fields' in img:
                        total_fields += len(img['fields'])
                return total_fields
        # 이전 구조 ('ocr_data')
        elif 'ocr_data' in json_data and json_data['ocr_data']:
            ocr_data = json_data['ocr_data']
            if isinstance(ocr_data, dict) and 'images' in ocr_data:
                total_fields = 0
                for img in ocr_data['images']:
                    if 'fields' in img:
                        total_fields += len(img['fields'])
                return total_fields
        return 0
    except:
        return 0

def count_detection_objects(json_data):
    """JSON 데이터에서 Detection 객체 개수 계산"""
    try:
        # 새로운 구조 ('detecting')
        if 'detecting' in json_data and json_data['detecting']:
            detection_data = json_data['detecting']
            if isinstance(detection_data, dict) and 'data' in detection_data and 'boxes' in detection_data['data']:
                boxes = detection_data['data']['boxes']
                return len([box for box in boxes if isinstance(box, dict) and 'label' in box])
        # 이전 구조 ('detection_data')
        elif 'detection_data' in json_data and json_data['detection_data']:
            detection_data = json_data['detection_data']
            if isinstance(detection_data, dict) and 'detections' in detection_data:
                detections = detection_data['detections']
                return len([det for det in detections if isinstance(det, dict) and 'label' in det])
        return 0
    except:
        return 0

def extract_ocr_text_preview(json_data):
    """JSON 데이터에서 OCR 텍스트 미리보기 추출"""
    try:
        if not json_data:
            return ""
        
        data = json_data if isinstance(json_data, dict) else json.loads(json_data)
        texts = []
        
        # 새로운 구조 ('ocr')
        if 'ocr' in data and data['ocr']:
            ocr_data = data['ocr']
            if isinstance(ocr_data, dict) and 'images' in ocr_data:
                for img in ocr_data['images']:
                    if 'fields' in img:
                        for field in img['fields']:
                            if 'inferText' in field and field['inferText']:
                                texts.append(field['inferText'])
        
        # 이전 구조 ('ocr_data')
        elif 'ocr_data' in data and data['ocr_data']:
            ocr_data = data['ocr_data']
            if isinstance(ocr_data, dict) and 'images' in ocr_data:
                for img in ocr_data['images']:
                    if 'fields' in img:
                        for field in img['fields']:
                            if 'inferText' in field and field['inferText']:
                                texts.append(field['inferText'])
        
        return " | ".join(texts)
    except:
        return ""

def _display_sources(sources, debug_info):
    """소스 정보 표시 함수 - 모든 소스 타입 지원"""
    if not sources:
        return
    
    # 고유 키 생성을 위한 타임스탬프
    timestamp = str(int(time.time() * 1000))
    
    # 소스 타입별 분류
    database_sources = [s for s in sources if s.get('type') == 'database']
    drawing_search_sources = [s for s in sources if s.get('type') == 'drawing_search']
    rag_sources = [s for s in sources if s.get('type') == 'rag']
    web_sources = [s for s in sources if s.get('type') == 'web']
    
    # 유사도 임계값 정보
    threshold = debug_info.get('similarity_threshold', 0.4)
    
    # 통계 정보 표시
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🗄️ 데이터베이스", len(database_sources))
    with col2:
        st.metric("🔍 도면 검색", len(drawing_search_sources))
    with col3:
        st.metric("📖 RAG 소스", len(rag_sources))
    with col4:
        st.metric("🌐 웹 소스", len(web_sources))
    
    # 추가 통계 행
    if threshold:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🎯 유사도 임계값", f"{threshold}")
        with col2:
            total_sources = len(database_sources) + len(drawing_search_sources) + len(rag_sources) + len(web_sources)
            st.metric("📊 총 소스 수", total_sources)
    
    st.markdown("---")
    
    # 도면 검색 결과 표시 (최우선)
    if drawing_search_sources:
        st.markdown("### 🔍 도면 검색 결과")
        for i, source in enumerate(drawing_search_sources, 1):
            st.write(f"{source.get('icon', '🔍')} **{source.get('source', 'N/A')}**")
            
            st.markdown(f"**🔸 검색 결과 {i}:**")
            st.write(f"- **정보:** {source.get('content_preview', 'N/A')}")
            st.write(f"- **품질:** {source.get('quality', 'N/A').upper()}")
            st.markdown("")  # 빈 줄 추가
    
    # 데이터베이스 소스 표시
    if database_sources:
        st.markdown("### 🗄️ 데이터베이스 소스 (선택된 도면)")
        for i, source in enumerate(database_sources, 1):
            st.write(f"{source.get('icon', '🗄️')} **{source.get('source', 'N/A')}**")
            
            # expander 대신 indented content 사용
            st.markdown(f"**🔸 도면 정보 {i}:**")
            st.write(f"- **설명:** {source.get('content_preview', 'N/A')}")
            st.write(f"- **품질:** {source.get('quality', 'N/A').upper()}")
            st.markdown("")  # 빈 줄 추가
    
    # RAG 소스 표시
    if rag_sources:
        st.markdown("### 📖 RAG 데이터베이스 소스")
        
        # 고품질과 저품질 분리
        high_quality = [s for s in rag_sources if s.get('quality') == 'high']
        low_quality = [s for s in rag_sources if s.get('quality') == 'low']
        
        if high_quality:
            st.markdown(f"**🟢 고품질 소스 (유사도 ≥ {threshold})**")
            for i, source in enumerate(high_quality, 1):
                score = source.get('score', 0)
                page = source.get('page', 'N/A')
                
                # 유사도에 따른 색상 결정
                if score >= 0.7:
                    score_color = "🟢"
                elif score >= 0.5:
                    score_color = "🟡"
                else:
                    score_color = "🟠"
                
                st.write(f"{source.get('icon', '📖')} **소스 {i}** - 페이지 {page} {score_color} (유사도: {score:.3f})")
                
                # expander 대신 toggle 형태로 표시
                show_content = st.checkbox(f"내용 미리보기 보기 - 소스 {i}", key=f"show_source_{i}_{timestamp}")
                if show_content:
                    st.code(source.get('content_preview', 'N/A'), language='text')
                st.markdown("")  # 빈 줄 추가
        
        if low_quality:
            st.markdown(f"**🟡 참고용 소스 (유사도 < {threshold})**")
            for i, source in enumerate(low_quality, len(high_quality) + 1):
                score = source.get('score', 0)
                page = source.get('page', 'N/A')
                
                st.write(f"{source.get('icon', '📖')} **참고 {i}** - 페이지 {page} 🟡 (유사도: {score:.3f})")
                
                # expander 대신 toggle 형태로 표시
                show_content = st.checkbox(f"내용 미리보기 보기 - 참고 {i}", key=f"show_ref_{i}_{timestamp}")
                if show_content:
                    st.code(source.get('content_preview', 'N/A'), language='text')
                st.markdown("")  # 빈 줄 추가
    
    # 웹 소스 표시
    if web_sources:
        st.markdown("### 🌐 웹 검색 소스")
        for i, source in enumerate(web_sources, 1):
            st.write(f"{source.get('icon', '🌐')} **{source.get('source', 'N/A')}**")
            
            # expander 대신 toggle 형태로 표시
            show_content = st.checkbox(f"웹 검색 결과 보기 - {i}", key=f"show_web_{i}_{timestamp}")
            if show_content:
                st.code(source.get('content_preview', 'N/A'), language='text')
            st.markdown("")  # 빈 줄 추가
    
    # 시각화 소스 표시
    visualization_sources = [s for s in sources if s.get('type') == 'visualization']
    if visualization_sources:
        st.markdown("### 🎨 시각화 소스")
        for i, source in enumerate(visualization_sources, 1):
            st.write(f"{source.get('icon', '🎨')} **{source.get('source', 'N/A')}**")
            st.write(f"- **내용:** {source.get('content_preview', 'N/A')}")
            st.write(f"- **품질:** {source.get('quality', 'N/A').upper()}")
            st.markdown("")  # 빈 줄 추가
    
    # 소스가 없는 경우
    if not database_sources and not drawing_search_sources and not rag_sources and not web_sources and not visualization_sources:
        st.info("📝 이 답변은 일반적인 P&ID 지식을 바탕으로 생성되었습니다.")

def _display_debug_info(debug_info):
    """디버그 정보 표시 함수"""
    query_type = debug_info.get('query_type', 'N/A')
    
    # 쿼리 타입별 색상 및 아이콘
    if query_type == "comprehensive_analysis":
        type_display = "🔬 분석"
        color = "purple"
    elif query_type == "drawing_visualization":
        type_display = "🎨 도면시각화"
        color = "teal"
    
    # 메트릭 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔍 쿼리 유형", type_display)
    
    with col2:
        context_quality = debug_info.get('context_quality', 'N/A')
        quality_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(context_quality, "⚪")
        st.metric("📊 컨텍스트 품질", f"{quality_icon} {context_quality}")
    
    with col3:
        web_used = debug_info.get('web_search_used', False)
        # 내부 데이터인 경우 웹 검색 금지 표시
        if query_type == "internal_data":
            st.metric("🌐 웹 검색", "🔒 금지됨")
        else:
            st.metric("🌐 웹 검색", "✅ 사용됨" if web_used else "❌ 사용안됨")
    
    with col4:
        if 'high_quality_sources' in debug_info and 'low_quality_sources' in debug_info:
            high_count = debug_info.get('high_quality_sources', 0)
            low_count = debug_info.get('low_quality_sources', 0)
            st.metric("📈 소스 품질", f"고품질: {high_count}, 참고: {low_count}")
    
    # 선택된 파일 정보 표시
    selected_files_count = debug_info.get('selected_files_count', 0)
    if selected_files_count > 0:
        st.markdown("---")
        st.markdown("### 📁 선택된 파일 데이터")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📄 선택된 파일", f"{selected_files_count}개")
        
        with col2:
            ocr_data_included = debug_info.get('ocr_data_included', False)
            st.metric("📝 OCR 데이터", "✅ 포함됨" if ocr_data_included else "❌ 없음")
        
        with col3:
            detection_data_included = debug_info.get('detection_data_included', False)
            st.metric("🎯 Detection 데이터", "✅ 포함됨" if detection_data_included else "❌ 없음")
        
        with col4:
            total_context_length = debug_info.get('total_context_length', 0)
            st.metric("📊 총 컨텍스트", f"{total_context_length}자")
        
        # 파일별 상세 정보 표시
        if debug_info.get('file_details'):
            with st.expander("🔍 파일별 상세 정보", expanded=False):
                for i, file_detail in enumerate(debug_info['file_details'], 1):
                    st.markdown(f"**파일 {i}: {file_detail.get('name', 'Unknown')}**")
                    st.write(f"- OCR 텍스트: {file_detail.get('ocr_count', 0)}개")
                    st.write(f"- Detection 객체: {file_detail.get('detection_count', 0)}개")
                    st.write(f"- JSON 데이터 크기: {file_detail.get('json_size', 0)}자")
                    
                    # OCR 텍스트 미리보기
                    if file_detail.get('ocr_preview'):
                        st.text_area(f"OCR 텍스트 미리보기 (파일 {i})", 
                                   value=file_detail['ocr_preview'][:200] + "..." if len(file_detail['ocr_preview']) > 200 else file_detail['ocr_preview'], 
                                   height=80, disabled=True, key=f"debug_ocr_{i}", label_visibility="collapsed")
                    
                    # Detection 객체 미리보기
                    if file_detail.get('detection_preview'):
                        st.text_area(f"Detection 객체 미리보기 (파일 {i})", 
                                   value=file_detail['detection_preview'][:200] + "..." if len(file_detail['detection_preview']) > 200 else file_detail['detection_preview'], 
                                   height=80, disabled=True, key=f"debug_detection_{i}", label_visibility="collapsed")
                    
                    if i < len(debug_info['file_details']):
                        st.divider()
    
    # 종합 분석 전용 정보 표시
    if query_type == "comprehensive_analysis":
        st.markdown("---")
        st.markdown("### 🔬 종합 분석 상세 정보")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            extracted_length = debug_info.get('extracted_text_length', 0)
            st.metric("📝 추출 텍스트", f"{extracted_length}자")
        
        with col2:
            rag_chunks = debug_info.get('rag_chunks_count', 0)
            st.metric("📖 RAG 청크", f"{rag_chunks}개")
        
        with col3:
            has_visualization = "✅ 포함" if debug_info.get('visualization') else "❌ 없음"
            st.metric("🎨 시각화", has_visualization)
        
        with col4:
            has_json = "✅ 포함" if debug_info.get('json_analysis') else "❌ 없음"
            st.metric("📊 JSON 분석", has_json)
    
    # 추가 세부 정보
    if debug_info.get('similarity_threshold'):
        extra_info = f"🎯 유사도 임계값: {debug_info['similarity_threshold']} | ⏱️ 생성 시간: {datetime.now().strftime('%H:%M:%S')}"
        
        # 내부 데이터 타입인 경우 보안 알림 추가
        if query_type == "internal_data":
            extra_info += " | 🔒 보안: RAG 전용"
        elif query_type == "comprehensive_analysis":
            extra_info += " | 🔬 통합: RAG+JSON+시각화"
        
        # 선택된 파일이 있는 경우 파일 정보 추가
        if selected_files_count > 0:
            extra_info += f" | 📁 파일: {selected_files_count}개"
        
        st.caption(extra_info)

def _display_visualization(visualization_data):
    """시각화 결과 표시 함수"""
    if not visualization_data:
        st.error("시각화 데이터가 없습니다.")
        return
    
    # 변경 비교 시각화인지 확인
    if 'as_is_image' in visualization_data and 'to_be_image' in visualization_data:
        # 변경 비교 시각화 처리
        st.markdown("### 🔄 변경 비교 시각화")
        
        # 통계 정보 표시
        stats = visualization_data.get('statistics', {})
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 AS-IS 객체", f"{stats.get('total_as_is', 0)}개")
        with col2:
            st.metric("📋 TO-BE 객체", f"{stats.get('total_to_be', 0)}개")
        with col3:
            st.metric("🔴 제거된 객체", f"{stats.get('removed_count', 0)}개")
        with col4:
            st.metric("🟢 추가된 객체", f"{stats.get('added_count', 0)}개")
        
        # AS-IS와 TO-BE 이미지를 나란히 표시
        st.markdown("### 🖼️ 비교 이미지")
        
        col1, col2 = st.columns(2)
        
        with col1:
            as_is_data = visualization_data.get('as_is_image', {})
            if as_is_data and 'image_base64' in as_is_data:
                st.markdown(f"#### {as_is_data.get('title', 'AS-IS')}")
                image_html = f'<img src="data:image/png;base64,{as_is_data["image_base64"]}" style="max-width: 100%; height: auto;" />'
                st.markdown(image_html, unsafe_allow_html=True)
                st.caption(f"강조된 객체: {as_is_data.get('highlight_count', 0)}개 / 전체: {as_is_data.get('total_objects', 0)}개")
        
        with col2:
            to_be_data = visualization_data.get('to_be_image', {})
            if to_be_data and 'image_base64' in to_be_data:
                st.markdown(f"#### {to_be_data.get('title', 'TO-BE')}")
                image_html = f'<img src="data:image/png;base64,{to_be_data["image_base64"]}" style="max-width: 100%; height: auto;" />'
                st.markdown(image_html, unsafe_allow_html=True)
                st.caption(f"강조된 객체: {to_be_data.get('highlight_count', 0)}개 / 전체: {to_be_data.get('total_objects', 0)}개")
        
        # 범례 표시
        st.markdown("### 📌 변경 비교 범례")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("🔴 **빨간색 박스**: 변경된 객체 (제거/추가)")
        with col2:
            st.markdown("⚪ **회색 박스**: 변경되지 않은 객체")
        
        # 상세 변경 내역 표시
        if visualization_data.get('analysis_summary'):
            st.markdown("### 📋 상세 변경 내역")
            st.text_area("상세 변경 내역", value=visualization_data['analysis_summary'], height=300, disabled=True, label_visibility="collapsed")
        
    else:
        # 기존 단일 도면 시각화 처리
        st.markdown("### 📊 시각화 정보")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📄 도면명", visualization_data.get('drawing_name', 'N/A'))
        with col2:
            st.metric("🔢 OCR 텍스트", f"{visualization_data.get('ocr_count', 0)}개")
        with col3:
            st.metric("🎯 Detection", f"{visualization_data.get('detection_count', 0)}개")
        with col4:
            original_size = visualization_data.get('original_size', (0, 0))
            st.metric("📐 이미지 크기", f"{original_size[0]}×{original_size[1]}")
        
        # 이미지 표시
        if 'image_base64' in visualization_data:
            st.markdown("### 🖼️ 분석된 도면")
            
            # Base64 이미지 표시
            import base64
            image_html = f'<img src="data:image/png;base64,{visualization_data["image_base64"]}" style="max-width: 100%; height: auto;" />'
            st.markdown(image_html, unsafe_allow_html=True)
            
            # 범례 표시
            st.markdown("### 📌 범례")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("🔵 **파란색 박스**: OCR 텍스트 영역")
            with col2:
                st.markdown("🔴 **빨간색 박스**: AI 감지 객체")
            
            # 상세 정보 - expander 대신 일반 컨테이너 사용
            st.markdown("### 📋 상세 분석 정보")
            
            # JSON 데이터에서 이미지 크기 정보 가져오기
            json_data = visualization_data.get('json_data', {})
            image_size = json_data.get('image_size', {})
            width = image_size.get('width', 0)
            height = image_size.get('height', 0)
            
            st.write(f"**원본 크기:** {width} × {height}")
            st.write(f"**분석 크기:** {resized_size[0]} × {resized_size[1]}")
            
            # OCR과 Detection 미리보기 표시
            st.markdown("### 📝 데이터 미리보기")
            
            # OCR 미리보기
            ocr_preview = visualization_data.get('ocr_preview', '')
            if ocr_preview:
                st.markdown("#### 🔵 OCR 텍스트")
                st.text_area("OCR 텍스트 미리보기", 
                           value=ocr_preview[:200] + "..." if len(ocr_preview) > 200 else ocr_preview,
                           height=100, disabled=True, key="ocr_preview", label_visibility="collapsed")
            
            # Detection 미리보기
            detection_preview = visualization_data.get('detection_preview', '')
            if detection_preview:
                st.markdown("#### 🔴 Detection 객체")
                st.text_area("Detection 객체 미리보기",
                           value=detection_preview[:200] + "..." if len(detection_preview) > 200 else detection_preview,
                           height=100, disabled=True, key="detection_preview", label_visibility="collapsed")
            
            # 분석 요약 정보를 보기 좋게 표시
            analysis_summary = visualization_data.get('analysis_summary', {})
            if isinstance(analysis_summary, dict):
                st.markdown("#### 📊 분석 통계")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("총 객체 수", analysis_summary.get('total_objects', 0))
                    if 'image_size' in analysis_summary:
                        st.write(f"**이미지 크기:** {analysis_summary['image_size'].get('width', 0)} × {analysis_summary['image_size'].get('height', 0)}")
                with col2:
                    st.metric("OCR 텍스트 수", analysis_summary.get('ocr_text_count', 0))
                    if 'detected_objects' in analysis_summary:
                        st.write(f"**감지된 객체:** {len(analysis_summary['detected_objects'])}개")
            else:
                st.write(f"**분석 요약:** {analysis_summary}")
            
            # 도면 데이터 정보
            drawing_data = visualization_data.get('drawing_data', {})
            if drawing_data:
                st.write(f"**등록일:** {drawing_data.get('create_date', 'N/A')}")
                st.write(f"**등록자:** {drawing_data.get('user', 'N/A')}")
        else:
            st.error("시각화된 이미지가 없습니다.")

if __name__ == "__main__":
    show() 