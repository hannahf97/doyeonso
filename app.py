import streamlit as st
from streamlit_option_menu import option_menu
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 페이지 임포트
from pages import home, file_upload, file_list, chat_bot, help, database_admin

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
            options=["홈", "파일 업로드", "파일 목록", "챗봇", "도움말", "데이터베이스 관리"],
            icons=["house", "upload", "list", "chat", "question", "database"],
            menu_icon="bear",
            default_index=0,
        )
    
    # 페이지 라우팅
    if selected == "홈":
        home.show()
    elif selected == "파일 업로드":
        file_upload.show()
    elif selected == "파일 목록":
        file_list.show()
    elif selected == "챗봇":
        chat_bot.show()
    elif selected == "도움말":
        help.show()
    elif selected == "데이터베이스 관리":
        database_admin.show()

if __name__ == "__main__":
    main() 