import streamlit as st
import os
from datetime import datetime

def show():
    """데이터베이스 관리 페이지"""
    
    st.title("🗄️ 데이터베이스 관리")
    st.markdown("---")
    
    st.warning("⚠️ 관리자 전용 페이지입니다. 신중하게 사용하세요.")
    
    # 벡터 데이터베이스 관리
    st.markdown("### 🗃️ 벡터 데이터베이스 관리")
    
    vector_db_path = "data/vector_db"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 상태 정보")
        
        if os.path.exists(f"{vector_db_path}/index.faiss"):
            st.success("✅ FAISS 인덱스 존재")
            index_size = os.path.getsize(f"{vector_db_path}/index.faiss")
            st.info(f"📏 인덱스 크기: {index_size:,} bytes")
        else:
            st.error("❌ FAISS 인덱스 없음")
        
        if os.path.exists(f"{vector_db_path}/metadata.pkl"):
            st.success("✅ 메타데이터 존재")
            metadata_size = os.path.getsize(f"{vector_db_path}/metadata.pkl")
            st.info(f"📏 메타데이터 크기: {metadata_size:,} bytes")
        else:
            st.error("❌ 메타데이터 없음")
    
    with col2:
        st.markdown("#### 🔧 관리 작업")
        
        if st.button("🗑️ 벡터 DB 삭제", type="secondary"):
            if st.checkbox("정말로 삭제하시겠습니까?"):
                try:
                    if os.path.exists(f"{vector_db_path}/index.faiss"):
                        os.remove(f"{vector_db_path}/index.faiss")
                    if os.path.exists(f"{vector_db_path}/metadata.pkl"):
                        os.remove(f"{vector_db_path}/metadata.pkl")
                    if os.path.exists(vector_db_path) and not os.listdir(vector_db_path):
                        os.rmdir(vector_db_path)
                    
                    st.success("✅ 벡터 데이터베이스가 삭제되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 삭제 실패: {e}")
        
        if st.button("🔄 벡터 DB 재구축"):
            pdf_path = "data/공정 Description_글.pdf"
            if os.path.exists(pdf_path):
                st.info("💡 챗봇 페이지에서 RAG 시스템 재구축을 실행하세요.")
            else:
                st.error("❌ PDF 파일을 찾을 수 없습니다.")
    
    st.markdown("---")
    
    # 시스템 정보
    st.markdown("### 💻 시스템 정보")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown("#### 📂 디렉토리 구조")
        
        directories = ["data", "uploads", "data/vector_db", "models", "utils", "pages"]
        
        for directory in directories:
            if os.path.exists(directory):
                size = sum(os.path.getsize(os.path.join(directory, f)) 
                          for f in os.listdir(directory) 
                          if os.path.isfile(os.path.join(directory, f)))
                st.success(f"✅ {directory} ({size:,} bytes)")
            else:
                st.error(f"❌ {directory}")
    
    with info_col2:
        st.markdown("#### 🔑 환경 변수")
        
        env_vars = ["OPENAI_API_KEY", "DATABASE_URL", "DB_HOST", "DB_USER"]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                # 보안을 위해 일부만 표시
                masked_value = value[:4] + "*" * (len(value) - 4) if len(value) > 4 else "****"
                st.success(f"✅ {var}: {masked_value}")
            else:
                st.error(f"❌ {var}: 설정되지 않음")
    
    st.markdown("---")
    
    # 로그 관리
    st.markdown("### 📋 로그 관리")
    
    st.info("💡 로그 기능은 향후 업데이트에서 구현될 예정입니다.")
    
    # 백업/복원
    st.markdown("### 💾 백업 및 복원")
    
    backup_col1, backup_col2 = st.columns(2)
    
    with backup_col1:
        st.markdown("#### 📤 백업 생성")
        if st.button("💾 시스템 백업"):
            st.info("💡 백업 기능은 향후 업데이트에서 구현될 예정입니다.")
    
    with backup_col2:
        st.markdown("#### 📥 백업 복원")
        uploaded_backup = st.file_uploader("백업 파일 선택", type=['zip'])
        if uploaded_backup and st.button("🔄 복원 실행"):
            st.info("💡 복원 기능은 향후 업데이트에서 구현될 예정입니다.")

if __name__ == "__main__":
    show() 