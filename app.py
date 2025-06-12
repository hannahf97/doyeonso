import streamlit as st
from streamlit_option_menu import option_menu
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 페이지 임포트
from pages import file_upload, file_list, database_view

def main():
    st.set_page_config(
        page_title="Doyeonso",
        page_icon="🐻",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 사이드바 메뉴
    with st.sidebar:
        selected = option_menu(
            menu_title="Doyeonso",
            options=["파일 업로드", "파일 목록", "데이터베이스 조회"],
            icons=["upload", "list", "table"],
            menu_icon="bear",
            default_index=0,
        )
    
    # 페이지 라우팅
    if selected == "파일 업로드":
        file_upload.show()
    elif selected == "파일 목록":
        file_list.show()
    elif selected == "데이터베이스 조회":
        database_view.show()

if __name__ == "__main__":
    main() 