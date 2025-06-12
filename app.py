import streamlit as st
from pages.sidebar import render_sidebar, handle_menu_click
from pages.home import render_home
from pages.fileupload import render_fileupload
from pages.filelist import render_filelist
from pages.chatbot import render_chatbot
from pages.help import render_help

# 페이지 설정
st.set_page_config(
    page_title="POSCO AI Assistant",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 기본 Streamlit 스타일 숨기기
st.markdown("""
<style>
/* Streamlit 기본 요소들 숨기기 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 기본 패딩 제거 */
.block-container {
    padding-top: 0rem;
    padding-bottom: 0rem;
    padding-left: 0rem;
    padding-right: 0rem;
}

/* 사이드바 숨기기 */
.css-1d391kg {display: none;}

/* 전체 배경 설정 */
.stApp {
    background-color: #f8f9fa;
}

/* 메인 컨테이너 설정 */
.main .block-container {
    max-width: none;
    padding: 0;
}
</style>
""", unsafe_allow_html=True)

def main():
    """메인 애플리케이션 함수"""
    
    # 세션 상태 초기화
    if "page_view" not in st.session_state:
        st.session_state["page_view"] = "home"
    
    # 사이드바 렌더링
    render_sidebar()
    
    # 메뉴 클릭 처리를 위한 숨겨진 버튼들
    handle_menu_click()
    
    # 현재 페이지에 따라 콘텐츠 렌더링
    current_page = st.session_state.get("page_view", "home")
    
    if current_page == "home":
        render_home()
    elif current_page == "fileupload":
        render_fileupload()
    elif current_page == "filelist":
        render_filelist()
    elif current_page == "chatbot":
        render_chatbot()
    elif current_page == "help":
        render_help()
    else:
        # 기본값으로 홈 페이지 표시
        render_home()

if __name__ == "__main__":
    main() 