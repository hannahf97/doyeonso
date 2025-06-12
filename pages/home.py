import streamlit as st
import os
from datetime import datetime

def show():
    """홈 페이지"""
    
    st.title("🐻 Doyeonso - P&ID 도면 분석 시스템")
    st.markdown("---")
    
    # 환영 메시지
    st.markdown("""
    ## 👋 환영합니다!
    
    **Doyeonso**는 P&ID(Piping and Instrumentation Diagram) 도면 분석을 위한 
    RAG 기반 전문가 시스템입니다.
    """)
    
    # 주요 기능 소개
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🤖 AI 챗봇
        - P&ID 전문가 AI 챗봇
        - RAG 기반 정확한 답변
        - 실시간 도면 분석
        """)
    
    with col2:
        st.markdown("""
        ### 📄 문서 관리
        - PDF 파일 업로드
        - 자동 텍스트 추출
        - 벡터 데이터베이스 구축
        """)
    
    with col3:
        st.markdown("""
        ### 🔍 고급 분석
        - 계측기기 식별
        - 안전장치 검토
        - 공정 흐름 분석
        """)
    
    st.markdown("---")
    
    # 시스템 상태
    st.markdown("### 📊 시스템 상태")
    
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        # PDF 파일 상태 확인
        pdf_path = "data/공정 Description_글.pdf"
        if os.path.exists(pdf_path):
            st.success("✅ PDF 문서 로드됨")
        else:
            st.error("❌ PDF 문서 없음")
    
    with status_col2:
        # 벡터 DB 상태 확인
        vector_db_path = "data/vector_db"
        if os.path.exists(f"{vector_db_path}/index.faiss"):
            st.success("✅ 벡터 DB 준비됨")
        else:
            st.warning("⚠️ 벡터 DB 없음")
    
    with status_col3:
        # API 키 상태 확인
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            st.success("✅ OpenAI API 설정됨")
        else:
            st.error("❌ OpenAI API 키 필요")
    
    # 빠른 시작 가이드
    st.markdown("### 🚀 빠른 시작")
    
    with st.expander("📖 사용 가이드"):
        st.markdown("""
        **1단계: 환경 설정**
        - `.env` 파일에 OpenAI API 키 설정
        - `data/` 폴더에 PDF 문서 업로드
        
        **2단계: 시스템 초기화**
        - 챗봇 페이지에서 RAG 시스템 자동 초기화
        - 벡터 데이터베이스 구축 (최초 1회)
        
        **3단계: AI 챗봇 사용**
        - P&ID 관련 질문 입력
        - 전문가 수준의 답변 확인
        - 참고 문서 출처 검토
        
        **주요 기능:**
        - 계측기기 설명 (FT, FC, FV, PT, PC 등)
        - 공정 안전성 분석
        - 도면 변경사항 검토
        - 제어 시스템 해석
        """)
    
    # 최근 활동 (향후 구현 예정)
    st.markdown("### 📈 최근 활동")
    st.info("이 섹션은 향후 업데이트에서 구현될 예정입니다.")
    
    # 푸터
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: gray;'>
        <small>
        Doyeonso v1.0 | 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d')}
        </small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    show() 