import streamlit as st
import base64
import os

# 페이지 설정
st.set_page_config(
    page_title="POSCO AI Assistant",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_base64_encoded_svg(svg_path):
    """SVG 파일을 base64로 인코딩"""
    try:
        with open(svg_path, "rb") as f:
            contents = f.read()
        return base64.b64encode(contents).decode("utf-8")
    except FileNotFoundError:
        print(f"SVG 파일을 찾을 수 없습니다: {svg_path}")
        return None

def render_sidebar():
    """좌측 고정 사이드바 렌더링"""
    # 세션 상태 초기화
    if "page_view" not in st.session_state:
        st.session_state["page_view"] = "home"
    
    # SVG 파일들 base64 인코딩
    posco_logo = get_base64_encoded_svg("assets/img/POSCO_CI.svg")
    home_icon = get_base64_encoded_svg("assets/img/home-icon.svg")
    upload_icon = get_base64_encoded_svg("assets/img/upload-icon.svg")
    list_icon = get_base64_encoded_svg("assets/img/list-icon.svg")
    chat_icon = get_base64_encoded_svg("assets/img/chat-icon.svg")
    help_icon = get_base64_encoded_svg("assets/img/help-icon.svg")
    dobi_character = get_base64_encoded_svg("assets/img/side_dobi.svg")
    
    # 현재 페이지 확인
    current_page = st.session_state.get('page_view', 'home')
    
    # 전체 페이지 레이아웃을 위한 CSS
    st.markdown("""
    <style>
    /* Streamlit 기본 요소들 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .css-1d391kg {display: none !important;}
    .css-1aumxhk {display: none !important;}
    .st-emotion-cache-1d391kg {display: none !important;}
    .st-emotion-cache-1aumxhk {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    .stSidebar {display: none !important;}
    button[data-testid="collapsedControl"] {display: none !important;}

    /* 전체 앱 기본 설정 */
    .stApp {
        background-color: #f8f9fa;
        margin: 0;
        padding: 0;
    }

    /* 메인 컨테이너 설정 - 사이드바 공간 확보 */
    .main .block-container {
        margin-left: 260px !important;
        padding: 20px !important;
        max-width: none !important;
        padding-top: 20px !important;
    }

    /* 사이드바 스타일 */
    .custom-sidebar {
        position: fixed;
        top: 0;
        left: 0;
        width: 260px;
        height: 100vh;
        background-color: #ffffff;
        border-right: 4px solid #357196;
        padding: 24px 16px;
        box-sizing: border-box;
        z-index: 9999;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    /* 로고 영역 */
    .sidebar-logo {
        margin-top: 0;
        padding-top: 0;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .sidebar-logo img {
        width: 120px;
        height: auto;
    }
    
    /* 검색창 */
    .sidebar-search {
        width: 100%;
        padding: 8px 12px;
        border: 1px solid #ccc;
        border-radius: 6px;
        margin: 20px 0;
        box-sizing: border-box;
        font-size: 14px;
        outline: none;
    }
    
    .sidebar-search:focus {
        border-color: #357196;
    }
    
    /* 메뉴 리스트 */
    .sidebar-menu {
        flex: 1;
        margin-top: 20px;
        position: relative;
    }
    
    .menu-item {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        margin: 4px 0;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.3s ease;
        color: #333;
        text-decoration: none;
        border: none;
        background: none;
        width: 100%;
        text-align: left;
    }

    .menu-item:hover {
        background-color: #f0f2f5;
    }

    .menu-item.active {
        background-color: #dde7f0;
        font-weight: bold;
    }

    .menu-icon {
        width: 24px;
        height: 24px;
        margin-right: 12px;
        flex-shrink: 0;
    }
    
    .menu-text {
        font-size: 14px;
        white-space: nowrap;
    }

    /* 투명한 네비게이션 버튼들 */
    .nav-button-overlay {
        position: absolute;
        background: transparent;
        border: none;
        cursor: pointer;
        width: calc(100% - 8px);
        height: 48px;
        left: 4px;
        z-index: 10000;
        margin: 0;
        padding: 0;
        opacity: 0;
    }

    .nav-button-overlay:hover {
        opacity: 0.1;
        background-color: #f0f2f5;
    }

    /* 각 메뉴 버튼의 위치 */
    .nav-home { top: 0px; }
    .nav-upload { top: 52px; }
    .nav-filelist { top: 104px; }
    .nav-chatbot { top: 156px; }
    .nav-help { top: 208px; }

    /* 도비 캐릭터 */
    .sidebar-dobi {
        text-align: center;
        margin: 20px 0;
    }

    .sidebar-dobi img {
        width: 80px;
        height: auto;
    }

    /* 유저 정보 박스 */
    .user-info {
        background-color: #357196;
        color: white;
        padding: 16px;
        border-radius: 8px;
        text-align: center;
        margin-top: auto;
        margin-bottom: 0;
    }

    .user-info h4 {
        margin: 0 0 8px 0;
        font-size: 14px;
        font-weight: bold;
    }

    .user-info p {
        margin: 4px 0;
        font-size: 12px;
        opacity: 0.9;
    }

    /* 반응형 처리 */
    @media (max-width: 768px) {
        .custom-sidebar {
            width: 200px;
        }
        .main .block-container {
            margin-left: 200px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 사이드바 HTML 구성
    logo_html = f'<img src="data:image/svg+xml;base64,{posco_logo}" alt="POSCO Logo" />' if posco_logo else '<div style="width: 120px; height: 40px; background: #357196; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold;">POSCO</div>'
    home_html = f'<img src="data:image/svg+xml;base64,{home_icon}" class="menu-icon" alt="Home" />' if home_icon else '<div class="menu-icon" style="background: #357196; border-radius: 4px;"></div>'
    upload_html = f'<img src="data:image/svg+xml;base64,{upload_icon}" class="menu-icon" alt="Upload" />' if upload_icon else '<div class="menu-icon" style="background: #357196; border-radius: 4px;"></div>'
    list_html = f'<img src="data:image/svg+xml;base64,{list_icon}" class="menu-icon" alt="List" />' if list_icon else '<div class="menu-icon" style="background: #357196; border-radius: 4px;"></div>'
    chat_html = f'<img src="data:image/svg+xml;base64,{chat_icon}" class="menu-icon" alt="Chat" />' if chat_icon else '<div class="menu-icon" style="background: #357196; border-radius: 4px;"></div>'
    help_html = f'<img src="data:image/svg+xml;base64,{help_icon}" class="menu-icon" alt="Help" />' if help_icon else '<div class="menu-icon" style="background: #357196; border-radius: 4px;"></div>'
    dobi_html = f'<img src="data:image/svg+xml;base64,{dobi_character}" alt="Dobi Character" />' if dobi_character else '<div style="width: 80px; height: 80px; background: #357196; border-radius: 50%; margin: 0 auto;"></div>'
    
    # 각 메뉴 아이템 HTML 생성 - 클릭 가능하도록 수정
    menu_home = f'<div class="menu-item {"active" if current_page == "home" else ""}" onclick="clickMenuButton(\'nav_home\')">{home_html}<span class="menu-text">HOME</span></div>'
    menu_upload = f'<div class="menu-item {"active" if current_page == "upload" else ""}" onclick="clickMenuButton(\'nav_upload\')">{upload_html}<span class="menu-text">FILE UPLOAD</span></div>'
    menu_filelist = f'<div class="menu-item {"active" if current_page == "filelist" else ""}" onclick="clickMenuButton(\'nav_filelist\')">{list_html}<span class="menu-text">FILE LIST</span></div>'
    menu_chatbot = f'<div class="menu-item {"active" if current_page == "chatbot" else ""}" onclick="clickMenuButton(\'nav_chatbot\')">{chat_html}<span class="menu-text">CHAT-BOT</span></div>'
    menu_help = f'<div class="menu-item {"active" if current_page == "help" else ""}" onclick="clickMenuButton(\'nav_help\')">{help_html}<span class="menu-text">HELP</span></div>'
    
    sidebar_content = f'<div class="custom-sidebar"><div class="sidebar-logo">{logo_html}</div><input type="text" class="sidebar-search" placeholder="Search for..." /><div class="sidebar-menu">{menu_home}{menu_upload}{menu_filelist}{menu_chatbot}{menu_help}</div><div class="sidebar-dobi">{dobi_html}</div><div class="user-info"><h4>김철수 님</h4><p>POSCO 제철소 직원</p><p>마지막 접속: 2024.01.15</p></div></div>'

    # 사이드바 렌더링
    st.markdown(sidebar_content, unsafe_allow_html=True)

def handle_page_navigation():
    """사이드바에서 직접 네비게이션 처리"""
    # st.sidebar 사용하여 직접 메뉴 버튼들 배치
    with st.sidebar:

        
        # POSCO 로고 표시 (모든 여백 제거)
        posco_logo = get_base64_encoded_svg("assets/img/POSCO_CI.svg")
        if posco_logo:
            st.markdown(f"""
            <div style="text-align: center; margin: 0; padding: 0; margin-bottom: 20px;">
                <img src="data:image/svg+xml;base64,{posco_logo}" alt="POSCO Logo" style="width: 120px; height: auto; margin: 0; padding: 0; display: block;" />
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; margin: 0; padding: 0; margin-bottom: 20px;">
                <div style="width: 120px; height: 40px; background: #357196; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; margin: 0 auto; border-radius: 4px;">POSCO</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 검색창 추가
        st.markdown("""
        <input type="text" placeholder="Search for..." style="padding: 8px 12px; border: 1px solid #ccc; border-radius: 6px; width: 100%; margin: 20px 0; box-sizing: border-box; font-size: 14px; outline: none;" />
        """, unsafe_allow_html=True)
        
        # 메뉴 버튼들
        if st.button("🏠 HOME", key="nav_home", use_container_width=True):
                st.session_state["page_view"] = "home"
                st.rerun()
        
        if st.button("📁 FILE UPLOAD", key="nav_upload", use_container_width=True):
            st.session_state["page_view"] = "upload"
            st.rerun()
        
        if st.button("📋 FILE LIST", key="nav_filelist", use_container_width=True):
            st.session_state["page_view"] = "filelist"
            st.rerun()
        
        if st.button("💬 CHAT-BOT", key="nav_chatbot", use_container_width=True):
            st.session_state["page_view"] = "chatbot"
            st.rerun()
        
        if st.button("❓ HELP", key="nav_help", use_container_width=True):
            st.session_state["page_view"] = "help"
            st.rerun()
        
        # 사용자 정보
        st.markdown("""
        <div style="background-color: #357196; color: white; padding: 16px; border-radius: 8px; text-align: center; margin-top: 20px; width: 100%;">
            <div style="font-weight: bold; font-size: 14px; line-height: 1.4;">
                제로<br/>
                SENIOR ASSISTANT
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 사이드바 스타일링
    current_page = st.session_state.get("page_view", "home")
    st.markdown(f"""
    <style>
    /* 사이드바 네비게이션만 숨기기 (사이드바 자체는 유지) */
    [data-testid="stSidebarNav"] {{display: none !important;}}
    
    /* 사이드바 전체 배경 스타일 */
    .stSidebar {{
        background-color: #ffffff !important;
        border-right: 4px solid #357196 !important;
        padding: 0px 16px 24px 16px !important;
        overflow: hidden !important;
    }}
    
    .stSidebar > div {{
        background-color: #ffffff !important;
        padding: 0px 16px 24px 16px !important;
        overflow: hidden !important;
    }}
    
    /* 사이드바 내용 영역의 스크롤바 제거 */
    .stSidebar [data-testid="stSidebarContent"] {{
        overflow: hidden !important;
        overflow-y: hidden !important;
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }}
    
    .stSidebar [data-testid="stSidebarContent"]::-webkit-scrollbar {{
        display: none !important;
    }}
    
    /* 사이드바 내용의 상단 여백 제거 */
    .stSidebar [data-testid="stSidebarContent"] {{
        padding-top: 0 !important;
        margin-top: 0 !important;
    }}
    
    /* 사이드바 내 첫 번째 요소의 여백 제거 */
    .stSidebar [data-testid="stSidebarContent"] > div:first-child {{
        margin-top: 0 !important;
        padding-top: 0 !important;
    }}
    
    /* 모든 마크다운 요소의 상단 여백 제거 */
    .stSidebar .stMarkdown:first-child {{
        margin-top: 0 !important;
        padding-top: 0 !important;
    }}
    
    /* 사이드바 내 모든 버튼 기본 스타일 */
    .stSidebar .stButton > button {{
        width: 100% !important;
        border: none !important;
        padding: 12px 16px !important;
        text-align: left !important;
        background-color: transparent !important;
        color: #333 !important;
        border-radius: 6px !important;
        margin: 4px 0 !important;
        transition: all 0.3s ease !important;
    }}
    
    /* 사이드바 내 버튼 hover 효과 */
    .stSidebar .stButton > button:hover {{
        background-color: #f0f2f5 !important;
        color: #333 !important;
    }}
    
    /* 더 광범위한 선택자로 현재 페이지 스타일 적용 */
    .stSidebar button[data-testid="baseButton-secondary"]:has-text("HOME") {{
        background-color: {('#dde7f0' if current_page == 'home' else 'transparent')} !important;
        font-weight: {('bold' if current_page == 'home' else 'normal')} !important;
    }}
    
    .stSidebar button[data-testid="baseButton-secondary"]:has-text("FILE UPLOAD") {{
        background-color: {('#dde7f0' if current_page == 'upload' else 'transparent')} !important;
        font-weight: {('bold' if current_page == 'upload' else 'normal')} !important;
    }}
    
    .stSidebar button[data-testid="baseButton-secondary"]:has-text("FILE LIST") {{
        background-color: {('#dde7f0' if current_page == 'filelist' else 'transparent')} !important;
        font-weight: {('bold' if current_page == 'filelist' else 'normal')} !important;
    }}
    
    .stSidebar button[data-testid="baseButton-secondary"]:has-text("CHAT-BOT") {{
        background-color: {('#dde7f0' if current_page == 'chatbot' else 'transparent')} !important;
        font-weight: {('bold' if current_page == 'chatbot' else 'normal')} !important;
    }}
    
    .stSidebar button[data-testid="baseButton-secondary"]:has-text("HELP") {{
        background-color: {('#dde7f0' if current_page == 'help' else 'transparent')} !important;
        font-weight: {('bold' if current_page == 'help' else 'normal')} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

def render_main_content():
    """현재 페이지에 따른 메인 콘텐츠 렌더링"""
    current_page = st.session_state.get("page_view", "home")
    
    try:
        # 현재 페이지에 따라 해당 파일을 import하고 실행
        if current_page == "home":
            from pages import home
            home.show()
        elif current_page == "upload":
            from pages import file_upload
            file_upload.show()
        elif current_page == "filelist":
            from pages import file_list
            file_list.show()
        elif current_page == "chatbot":
            from pages import chat_bot
            chat_bot.show()
        elif current_page == "help":
            from pages import help
            help.show()
    except ImportError as e:
        st.error(f"페이지를 불러올 수 없습니다: {e}")
        st.markdown(f"""
        <div style="padding: 40px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 20px;">
            <h1 style="color: #357196; margin-bottom: 20px;">페이지 로드 오류</h1>
            <p style="font-size: 18px; color: #666;">{current_page} 페이지를 불러오는 중 오류가 발생했습니다.</p>
            <p>pages/{current_page}.py 파일이 존재하는지 확인해주세요.</p>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"페이지 실행 중 오류가 발생했습니다: {e}")
        st.markdown(f"""
        <div style="padding: 40px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 20px;">
            <h1 style="color: #357196; margin-bottom: 20px;">실행 오류</h1>
            <p style="font-size: 18px; color: #666;">{current_page} 페이지 실행 중 오류가 발생했습니다.</p>
            <p>오류 내용: {str(e)}</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """메인 애플리케이션 함수"""
    # 세션 상태 초기화
    if "page_view" not in st.session_state:
        st.session_state["page_view"] = "home"
    
    # Streamlit 네이티브 사이드바로 네비게이션
    handle_page_navigation()
    
    # 메인 콘텐츠 렌더링
    render_main_content()

if __name__ == "__main__":
    main() 
