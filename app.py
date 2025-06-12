import streamlit as st
from streamlit_option_menu import option_menu
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 페이지 임포트
from pages import home, file_upload, file_list, chat_bot, help, database_admin, preprocessing_analysis, database_view

def main():
    st.set_page_config(
        page_title="도연소 (DoyeonSo)",
        page_icon="🐻",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 사이드바 메뉴
    with st.sidebar:
        selected = option_menu(
            menu_title="도연소 (DoyeonSo)",
            options=[
                "🏠 홈", 
                "🔧 P&ID 전문가 챗봇", 
                "📤 파일 업로드", 
                "📋 파일 목록", 
                "💾 데이터베이스 조회",
                "🔍 전처리 분석",
                "⚙️ 데이터베이스 관리",
                "❓ 도움말"
            ],
            icons=["house", "robot", "upload", "list", "table", "search", "gear", "question-circle"],
            menu_icon="bear",
            default_index=0,
        )
    
    # 페이지 라우팅
    if selected == "🏠 홈":
        home.show()
    elif selected == "🔧 P&ID 전문가 챗봇":
        chat_bot.show()
    elif selected == "📤 파일 업로드":
        file_upload.show()
    elif selected == "📋 파일 목록":
        file_list.show()
    elif selected == "💾 데이터베이스 조회":
        database_view.show()
    elif selected == "🔍 전처리 분석":
        preprocessing_analysis.show_preprocessing_analysis()
    elif selected == "⚙️ 데이터베이스 관리":
        database_admin.show()
    elif selected == "❓ 도움말":
        help.show()

if __name__ == "__main__":
    main() 