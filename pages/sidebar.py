# 사이드바 컴포넌트
# HTML/CSS 기반 사이드바 구현 예정
import streamlit as st
import base64
from pathlib import Path

# SVG 파일들을 base64로 인코딩하는 함수
def get_base64_encoded_svg(svg_path):
    """SVG 파일을 base64로 인코딩"""
    try:
        with open(svg_path, "rb") as f:
            contents = f.read()
        return base64.b64encode(contents).decode("utf-8")
    except FileNotFoundError:
        return None

def render_sidebar():
    """HTML/CSS 기반 사이드바 렌더링"""
    # 현재 페이지 상태 초기화
    if "page_view" not in st.session_state:
        st.session_state["page_view"] = "home"
    
    # SVG 파일들 base64 인코딩
    posco_logo = get_base64_encoded_svg("assets/img/POSCO_CI.svg")
    home_icon = get_base64_encoded_svg("assets/img/home-icon.svg")
    upload_icon = get_base64_encoded_svg("assets/img/upload-icon.svg")
    list_icon = get_base64_encoded_svg("assets/img/list-icon.svg")
    chat_icon = get_base64_encoded_svg("assets/img/chat-icon.svg")
    help_icon = get_base64_encoded_svg("assets/img/help-icon.svg")
    dobi_icon = get_base64_encoded_svg("assets/img/side_dobi.svg")
    user_icon = get_base64_encoded_svg("assets/img/usericon.svg")
    
    # 사이드바 HTML/CSS
    sidebar_html = f"""
    <style>
    .sidebar {{
        position: fixed;
        left: 0;
        top: 0;
        width: 260px;
        height: 100vh;
        background-color: #ffffff;
        border-right: 4px solid #357196;
        padding: 24px 16px;
        overflow: hidden;
        z-index: 1000;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
    }}
    
    .logo-container {{
        display: flex;
        justify-content: center;
        margin-top: 0;
        padding-top: 0;
        margin-bottom: 20px;
    }}
    
    .logo {{
        width: 120px;
        height: auto;
    }}
    
    .search-box {{
        width: 100%;
        padding: 8px 12px;
        border: 1px solid #ccc;
        border-radius: 6px;
        margin: 20px 0;
        font-size: 14px;
        box-sizing: border-box;
    }}
    
    .menu-container {{
        flex: 1;
        margin-bottom: 20px;
    }}
    
    .menu-item {{
        display: flex;
        align-items: center;
        padding: 12px 16px;
        margin: 4px 0;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        color: #333;
    }}
    
    .menu-item:hover {{
        background-color: #f0f2f5;
    }}
    
    .menu-item.active {{
        background-color: #dde7f0;
        font-weight: bold;
    }}
    
    .menu-icon {{
        width: 24px;
        height: 24px;
        margin-right: 12px;
    }}
    
    .menu-text {{
        font-size: 14px;
    }}
    
    .dobi-container {{
        display: flex;
        justify-content: center;
        margin-bottom: 16px;
    }}
    
    .dobi-image {{
        width: 120px;
        height: auto;
    }}
    
    .user-info {{
        background-color: #357196;
        color: white;
        display: flex;
        align-items: center;
        padding: 12px 16px;
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        width: 260px;
        box-sizing: border-box;
    }}
    
    .user-icon {{
        width: 24px;
        height: 24px;
        margin-right: 12px;
    }}
    
    .user-details {{
        flex: 1;
    }}
    
    .user-name {{
        font-weight: bold;
        font-size: 14px;
    }}
    
    .user-role {{
        font-size: 12px;
        opacity: 0.8;
    }}
    </style>
    
    <div class="sidebar">
        <!-- 로고 -->
        <div class="logo-container">
            {f'<img src="data:image/svg+xml;base64,{posco_logo}" class="logo" alt="POSCO Logo" />' if posco_logo else '<div style="width: 120px; height: 40px; background: #357196; text-align: center; line-height: 40px; color: white;">POSCO</div>'}
        </div>
        
        <!-- 검색창 -->
        <input type="text" class="search-box" placeholder="Search for..." />
        
        <!-- 메뉴 -->
        <div class="menu-container">
            <div class="menu-item {'active' if st.session_state.get('page_view') == 'home' else ''}" onclick="document.getElementById('btn_home').click()">
                {f'<img src="data:image/svg+xml;base64,{home_icon}" class="menu-icon" />' if home_icon else '<div class="menu-icon"></div>'}
                <span class="menu-text">HOME</span>
            </div>
            
            <div class="menu-item {'active' if st.session_state.get('page_view') == 'fileupload' else ''}" onclick="document.getElementById('btn_fileupload').click()">
                {f'<img src="data:image/svg+xml;base64,{upload_icon}" class="menu-icon" />' if upload_icon else '<div class="menu-icon"></div>'}
                <span class="menu-text">FILE UPLOAD</span>
            </div>
            
            <div class="menu-item {'active' if st.session_state.get('page_view') == 'filelist' else ''}" onclick="document.getElementById('btn_filelist').click()">
                {f'<img src="data:image/svg+xml;base64,{list_icon}" class="menu-icon" />' if list_icon else '<div class="menu-icon"></div>'}
                <span class="menu-text">FILE LIST</span>
            </div>
            
            <div class="menu-item {'active' if st.session_state.get('page_view') == 'chatbot' else ''}" onclick="document.getElementById('btn_chatbot').click()">
                {f'<img src="data:image/svg+xml;base64,{chat_icon}" class="menu-icon" />' if chat_icon else '<div class="menu-icon"></div>'}
                <span class="menu-text">CHAT-BOT</span>
            </div>
            
            <div class="menu-item {'active' if st.session_state.get('page_view') == 'help' else ''}" onclick="document.getElementById('btn_help').click()">
                {f'<img src="data:image/svg+xml;base64,{help_icon}" class="menu-icon" />' if help_icon else '<div class="menu-icon"></div>'}
                <span class="menu-text">HELP</span>
            </div>
        </div>
        
        <!-- 도비 캐릭터 -->
        <div class="dobi-container">
            {f'<img src="data:image/svg+xml;base64,{dobi_icon}" class="dobi-image" alt="Dobi Character" />' if dobi_icon else '<div style="width: 120px; height: 80px; background: #f0f2f5; display: flex; align-items: center; justify-content: center;">DOBI</div>'}
        </div>
        
        <!-- 유저 정보 -->
        <div class="user-info">
            {f'<img src="data:image/svg+xml;base64,{user_icon}" class="user-icon" />' if user_icon else '<div class="user-icon"></div>'}
            <div class="user-details">
                <div class="user-name">USER NAME</div>
                <div class="user-role">SENIOR ASSISTANT</div>
            </div>
        </div>
    </div>
    

    """
    
    # HTML 렌더링
    st.markdown(sidebar_html, unsafe_allow_html=True)

def handle_menu_click():
    """메뉴 클릭 처리를 위한 버튼들 (실제 페이지 전환용)"""
    # 메뉴 버튼들을 위한 컨테이너 (숨김)
    st.markdown("""
    <style>
    /* 메뉴 버튼들 숨기기 */
    .menu-buttons {
        position: fixed;
        top: -1000px;
        left: -1000px;
        visibility: hidden;
        opacity: 0;
        pointer-events: none;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="menu-buttons">', unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("HOME", key="btn_home"):
                st.session_state["page_view"] = "home"
                st.rerun()
        
        with col2:
            if st.button("FILE UPLOAD", key="btn_fileupload"):
                st.session_state["page_view"] = "fileupload"
                st.rerun()
        
        with col3:
            if st.button("FILE LIST", key="btn_filelist"):
                st.session_state["page_view"] = "filelist"
                st.rerun()
        
        with col4:
            if st.button("CHAT-BOT", key="btn_chatbot"):
                st.session_state["page_view"] = "chatbot"
                st.rerun()
        
        with col5:
            if st.button("HELP", key="btn_help"):
                st.session_state["page_view"] = "help"
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True) 