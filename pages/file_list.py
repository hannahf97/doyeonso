import streamlit as st
import os
from datetime import datetime

def show():
    """파일 목록 페이지"""
    
    st.title("📋 파일 목록")
    st.markdown("---")
    
    st.markdown("### 📁 관리 중인 파일들")
    
    # 데이터 디렉토리들 확인
    directories = {
        "data": "📄 원본 문서",
        "uploads": "📤 업로드 파일", 
        "data/vector_db": "🗃️ 벡터 데이터베이스"
    }
    
    for dir_path, dir_desc in directories.items():
        st.markdown(f"#### {dir_desc}")
        
        if os.path.exists(dir_path):
            files = os.listdir(dir_path)
            
            if files:
                for file in files:
                    file_path = os.path.join(dir_path, file)
                    
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
                        with col1:
                            st.write(f"📄 {file}")
                        with col2:
                            st.write(f"{file_size:,} bytes")
                        with col3:
                            st.write(file_modified.strftime("%Y-%m-%d %H:%M:%S"))
                        with col4:
                            if st.button("🗑️", key=f"delete_{dir_path}_{file}"):
                                try:
                                    os.remove(file_path)
                                    st.success(f"✅ {file} 삭제됨")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ 삭제 실패: {e}")
            else:
                st.info(f"📭 {dir_path} 폴더가 비어있습니다.")
        else:
            st.warning(f"📁 {dir_path} 폴더가 존재하지 않습니다.")
        
        st.markdown("---")

if __name__ == "__main__":
    show() 