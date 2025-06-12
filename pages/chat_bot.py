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
    
    # 사이드바 설정
    with st.sidebar:
        st.markdown("### ⚙️ 설정")
        
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
    
    # 챗봇 초기화
    if 'chatbot' not in st.session_state:
        with st.spinner("🤖 P&ID 전문가 챗봇을 초기화하는 중..."):
            st.session_state.chatbot = PIDExpertChatbot()
            
            if pdf_exists:
                success = st.session_state.chatbot.initialize_rag_system(pdf_path)
                if success:
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
                        for i, source in enumerate(message["sources"], 1):
                            st.write(f"**{i}. 페이지 {source['page']}** (유사도: {source['score']:.3f})")
                            st.write(f"```\n{source['content_preview']}\n```")
                
                # 디버그 정보 표시
                if show_debug_info and "debug_info" in message:
                    debug = message["debug_info"]
                    query_type = debug.get('query_type', 'N/A')
                    
                    # 쿼리 타입별 색상 및 아이콘
                    if query_type == "change_analysis":
                        type_display = "🔄 변경분석"
                        color = "orange"
                    elif query_type == "safety_analysis":
                        type_display = "🛡️ 안전분석"
                        color = "red"
                    elif query_type == "instrument_explanation":
                        type_display = "⚙️ 계측설명"
                        color = "blue"
                    else:
                        type_display = "💬 일반"
                        color = "gray"
                    
                    st.info(f"🔍 쿼리 유형: :{color}[{type_display}] | "
                           f"컨텍스트 품질: {debug.get('context_quality', 'N/A')} | "
                           f"웹 검색: {'✅' if debug.get('web_search_used', False) else '❌'}")
    
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
                    use_web_search=use_web_search
                )
            
            # 응답 표시
            st.write(response_data['response'])
            st.caption(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 소스 정보 표시
            if show_sources and response_data['sources']:
                with st.expander("📚 참고 문서 출처"):
                    for i, source in enumerate(response_data['sources'], 1):
                        st.write(f"**{i}. 페이지 {source['page']}** (유사도: {source['score']:.3f})")
                        st.write(f"```\n{source['content_preview']}\n```")
            
            # 디버그 정보 표시
            if show_debug_info:
                query_type = response_data.get('query_type', 'N/A')
                
                # 쿼리 타입별 색상 및 아이콘
                if query_type == "change_analysis":
                    type_display = "🔄 변경분석"
                    color = "orange"
                elif query_type == "safety_analysis":
                    type_display = "🛡️ 안전분석"
                    color = "red"
                elif query_type == "instrument_explanation":
                    type_display = "⚙️ 계측설명"
                    color = "blue"
                else:
                    type_display = "💬 일반"
                    color = "gray"
                
                st.info(f"🔍 쿼리 유형: :{color}[{type_display}] | "
                       f"컨텍스트 품질: {response_data.get('context_quality', 'N/A')} | "
                       f"웹 검색: {'✅' if response_data.get('web_search_used', False) else '❌'}")
        
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

if __name__ == "__main__":
    show() 