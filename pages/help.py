import streamlit as st

def show():
    """도움말 페이지"""
    
    st.title("❓ 도움말")
    st.markdown("---")
    
    # FAQ 섹션
    st.markdown("### 🔍 자주 묻는 질문 (FAQ)")
    
    with st.expander("Q1. RAG 시스템이란 무엇인가요?"):
        st.markdown("""
        **RAG (Retrieval Augmented Generation)**는 검색 기반 생성 AI 기술입니다.
        
        - 📚 문서에서 관련 정보를 검색
        - 🤖 검색된 정보를 바탕으로 정확한 답변 생성
        - ✅ 환상(hallucination) 현상 최소화
        """)
    
    with st.expander("Q2. P&ID 도면이란?"):
        st.markdown("""
        **P&ID (Piping and Instrumentation Diagram)**는 공정 배관 및 계장 다이어그램입니다.
        
        - 🔧 공정 흐름과 배관 연결 정보
        - 📊 계측기기 및 제어장치 배치
        - ⚠️ 안전장치 및 비상정지 시스템
        """)
    
    with st.expander("Q3. 계측기기 태그는 어떻게 읽나요?"):
        st.markdown("""
        **계측기기 태그 구성:**
        
        - **FT-101**: Flow Transmitter (유량 전송기)
        - **FC-201**: Flow Controller (유량 조절기)
        - **PT-301**: Pressure Transmitter (압력 전송기)
        - **TT-401**: Temperature Transmitter (온도 전송기)
        - **LT-501**: Level Transmitter (액위 전송기)
        """)
    
    # 사용 가이드
    st.markdown("### 📖 사용 가이드")
    
    tab1, tab2, tab3 = st.tabs(["🚀 시작하기", "💬 챗봇 활용", "🔧 고급 기능"])
    
    with tab1:
        st.markdown("""
        #### 1. 환경 설정
        ```bash
        # 패키지 설치
        pip install -r requirements.txt
        
        # 환경변수 설정 (.env 파일)
        OPENAI_API_KEY=your_api_key_here
        ```
        
        #### 2. 애플리케이션 실행
        ```bash
        streamlit run app.py
        ```
        
        #### 3. PDF 문서 업로드
        - 파일 업로드 페이지에서 PDF 업로드
        - 챗봇에서 자동으로 RAG 시스템 구축
        """)
    
    with tab2:
        st.markdown("""
        #### 효과적인 질문 방법
        
        **✅ 좋은 질문 예시:**
        - "FT-101의 역할과 설치 위치를 설명해주세요"
        - "압력 조절 시스템의 안전장치는 무엇인가요?"
        - "비상정지 시퀀스를 단계별로 설명해주세요"
        
        **❌ 피해야 할 질문:**
        - "이게 뭐야?"
        - "문제가 있어"
        - "어떻게 해?"
        """)
    
    with tab3:
        st.markdown("""
        #### 고급 설정 옵션
        
        - **웹 검색 보조**: RAG 정보가 부족할 때 웹 검색 활용
        - **참고 문서 출처**: 답변의 근거가 된 문서 페이지 표시
        - **디버그 정보**: 쿼리 유형, 컨텍스트 품질 등 기술 정보
        
        #### 벡터 데이터베이스 관리
        - 새 문서 추가 시 RAG 시스템 재구축 필요
        - 임베딩 모델: 한국어 특화 모델 사용
        - 유사도 임계값: 0.7 이상 문서만 검색 결과로 활용
        """)
    
    # 기술 스택
    st.markdown("### 🛠️ 기술 스택")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Frontend:**
        - Streamlit (웹 인터페이스)
        - streamlit-option-menu (네비게이션)
        
        **AI/ML:**
        - OpenAI GPT-4 (언어 모델)
        - SentenceTransformers (임베딩)
        - FAISS (벡터 검색)
        """)
    
    with col2:
        st.markdown("""
        **Data Processing:**
        - PyPDF2 (PDF 처리)
        - pandas (데이터 처리)
        - numpy (수치 연산)
        
        **Infrastructure:**
        - python-dotenv (환경변수)
        - loguru (로깅)
        """)
    
    # 문의 및 지원
    st.markdown("### 📞 문의 및 지원")
    
    st.info("""
    🔧 **기술 지원**  
    시스템 관련 문의사항은 개발팀에 문의하세요.
    
    ⚠️ **중요 안내**  
    이 시스템은 보조 도구입니다. 중요한 안전 결정은 반드시 전문가와 상의하시기 바랍니다.
    """)

if __name__ == "__main__":
    show() 