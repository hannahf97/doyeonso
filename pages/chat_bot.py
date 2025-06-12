import streamlit as st
import os
from models.chatbotModel import PIDExpertChatbot
from loguru import logger
import time
from datetime import datetime

def show():
    """P&ID 전문가 챗봇 페이지"""
    
    st.title("🔧 P&ID 도면 분석 전문가 챗봇")
    st.markdown("---")
    
    # 챗봇 초기화
    if 'chatbot' not in st.session_state:
        with st.spinner("🤖 P&ID 전문가 챗봇을 초기화하는 중..."):
            st.session_state.chatbot = PIDExpertChatbot()
    
    # 선택된 도면 정보 표시 (file list에서 선택된 것)
    selected_drawing = st.session_state.get('selected_drawing_name', None)
    
    if selected_drawing:
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
                        selected_drawing=selected_drawing
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
    else:
        st.info("💡 도면을 선택하려면 📋 FILE LIST 페이지로 이동하세요.")
    
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
                    selected_drawing=st.session_state.get('selected_drawing_name')
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
                "web_search_used": response_data.get('web_search_used', False)
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
    """테스트 질문을 대화에 추가하는 헬퍼 함수"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # 사용자 질문 추가
    st.session_state.messages.append({
        "role": "user",
        "content": question_text,
        "timestamp": datetime.now()
    })
    
    # 페이지 새로고침으로 질문이 추가된 것을 표시
    st.rerun()

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
    if query_type == "change_analysis":
        type_display = "🔄 변경분석"
        color = "orange"
    elif query_type == "internal_data":
        type_display = "🔒 내부데이터"
        color = "blue"
    elif query_type == "safety_analysis":
        type_display = "🛡️ 안전분석"
        color = "red"
    elif query_type == "instrument_explanation":
        type_display = "⚙️ 계측설명"
        color = "green"
    else:
        type_display = "💬 일반"
        color = "gray"
    
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
    
    # 추가 세부 정보
    if debug_info.get('similarity_threshold'):
        extra_info = f"🎯 유사도 임계값: {debug_info['similarity_threshold']} | ⏱️ 생성 시간: {datetime.now().strftime('%H:%M:%S')}"
        
        # 내부 데이터 타입인 경우 보안 알림 추가
        if query_type == "internal_data":
            extra_info += " | 🔒 보안: RAG 전용"
        
        st.caption(extra_info)

def _display_visualization(visualization_data):
    """시각화 결과 표시 함수"""
    if not visualization_data:
        st.error("시각화 데이터가 없습니다.")
        return
    
    # 기본 정보 표시
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
        
        # 상세 정보
        with st.expander("📋 상세 분석 정보"):
            resized_size = visualization_data.get('resized_size', (0, 0))
            st.write(f"**원본 크기:** {original_size[0]} × {original_size[1]}")
            st.write(f"**분석 크기:** {resized_size[0]} × {resized_size[1]}")
            st.write(f"**분석 요약:** {visualization_data.get('analysis_summary', 'N/A')}")
            
            # 도면 데이터 정보
            drawing_data = visualization_data.get('drawing_data', {})
            if drawing_data:
                st.write(f"**등록일:** {drawing_data.get('create_date', 'N/A')}")
                st.write(f"**등록자:** {drawing_data.get('user', 'N/A')}")
    else:
        st.error("시각화된 이미지가 없습니다.")

if __name__ == "__main__":
    show() 