import streamlit as st
import base64

def get_base64_encoded_svg(svg_path):
    """SVG 파일을 base64로 인코딩"""
    try:
        with open(svg_path, "rb") as f:
            contents = f.read()
        return base64.b64encode(contents).decode("utf-8")
    except FileNotFoundError:
        print(f"SVG 파일을 찾을 수 없습니다: {svg_path}")
        return None

def show():
    """홈 페이지"""
    
    # CSS를 통한 레이아웃 조정 - 사이드바 우측 정렬
    st.markdown("""
    <style>
    /* 전체 페이지 오버플로우 방지 */
    .main .block-container {
        padding-top: 0rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 2rem;
        max-width: 100%;
        overflow-x: hidden;
        box-sizing: border-box;
    }
    
    /* 사이드바가 없을 때 기본 여백 조정 */
    @media (max-width: 768px) {
        .main .block-container {
            margin-left: 0px;
            padding-right: 0.5rem;
            padding-left: 0.5rem;
        }
    }
    
    /* 제목 그룹 스타일 */
    .title-group {
        display: flex;
        justify-content: center;
        align-items: flex-start;
        gap: min(5px, 1vw);
        margin-top: 10px;
        width: 100%;
        max-width: 100%;
        padding: 0;
        flex-wrap: wrap;
        box-sizing: border-box;
        overflow: hidden;
    }
    
    .title-group > div {
        flex-shrink: 1;
        flex-grow: 0;
        min-width: 0;
        max-width: 45%;
        box-sizing: border-box;
    }
    
    .title-group img {
        max-width: 100%;
        height: auto;
        object-fit: contain;
        display: block;
        margin: 0 auto;
    }
    
    /* 버튼 그룹 스타일 */
    .button-group {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 40px;
        margin-top: 60px;
        width: 100%;
        max-width: 100%;
        padding: 0;
        flex-wrap: wrap;
        box-sizing: border-box;
        overflow: hidden;
    }
    
    /* 반응형 조정 */
    @media (max-width: 768px) {
        .title-group {
            gap: 5px;
        }
        .title-group > div {
            max-width: 48%;
        }
        .button-group {
            gap: 20px;
        }
    }
    
    @media (max-width: 480px) {
        .title-group > div {
            max-width: 100%;
            margin-bottom: 10px;
        }
        .button-group {
            gap: 15px;
        }
    }
    
    /* 개별 버튼 컨테이너 스타일 */
    .button-group > div {
        position: relative;
        display: inline-block;
        width: 174px;
        height: 161px;
        transition: transform 0.2s ease;
    }
    
    .button-group > div:hover {
        transform: scale(1.05);
    }

    /* 메인 버튼 이미지 */
    .button-group img {
        width: 174px;
        height: 161px;
        display: block;
        object-fit: contain;
    }

    /* 투명한 클릭 오버레이 */
    .main-button-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 174px;
        height: 161px;
        background-color: transparent;
        cursor: pointer;
        z-index: 2;
        opacity: 0;
        transition: opacity 0.2s ease;
        display: block;
    }

    .main-button-overlay:hover {
        opacity: 0.1;
        background-color: rgba(53, 113, 150, 0.2);
    }

    /* 반응형 조정 - 버튼 크기 */
    @media (max-width: 768px) {
        .button-group > div {
            width: 140px;
            height: 130px;
        }
        
        .button-group img,
        .main-button-overlay {
            width: 140px;
            height: 130px;
        }
    }
    
    @media (max-width: 480px) {
        .button-group > div {
            width: 120px;
            height: 111px;
        }
        
        .button-group img,
        .main-button-overlay {
            width: 120px;
            height: 111px;
        }
    }



    </style>
    """, unsafe_allow_html=True)
    
    # SVG 파일들을 base64로 인코딩
    main_dobi_logo = get_base64_encoded_svg("assets/img/main_dobi.svg")
    title_logo = get_base64_encoded_svg("assets/img/title.svg")
    
    # 버튼 이미지들 base64 인코딩
    fileupload_button = get_base64_encoded_svg("assets/img/main_fileupload_butt.svg")
    filelist_button = get_base64_encoded_svg("assets/img/main_filelist_butt.svg")
    chatbot_button = get_base64_encoded_svg("assets/img/main_chatbot_butt.svg")
    help_button = get_base64_encoded_svg("assets/img/main_help_butt.svg")
    
    # 사이드바 CI와 같은 방식으로 상단에 배치
    if main_dobi_logo and title_logo:
        st.markdown(f"""
        <div class="title-group">
            <div style="text-align: center;">
                <img src="data:image/svg+xml;base64,{main_dobi_logo}" alt="Main Dobi" style="height: min(180px, 22vh); max-width: 100%; width: auto; margin: 0; padding: 0; display: block;" />
            </div>
            <div style="text-align: center;">
                <img src="data:image/svg+xml;base64,{title_logo}" alt="Title" style="height: min(160px, 18vh); max-width: 100%; width: auto; margin: 0; padding: 0; display: block;" />
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 파일 로딩 실패시 대체 표시
        st.markdown(f"""
        <div class="title-group">
            <div style="text-align: center;">
                {f'<img src="data:image/svg+xml;base64,{main_dobi_logo}" alt="Main Dobi" style="height: min(120px, 15vh); max-width: 100%; width: auto; margin: 0; padding: 0; display: block;" />' if main_dobi_logo else '<div style="height: min(120px, 15vh); max-width: 100%; background: #357196; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; border-radius: 4px;">DOBI</div>'}
            </div>
            <div style="text-align: center;">
                {f'<img src="data:image/svg+xml;base64,{title_logo}" alt="Title" style="height: min(100px, 12vh); max-width: 100%; width: auto; margin: 0; padding: 0; display: block;" />' if title_logo else '<div style="height: min(100px, 12vh); max-width: 100%; background: #357196; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; border-radius: 4px;">도면연구소</div>'}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 주요 기능 버튼들 - JavaScript 이벤트 리스너 사용
    button_html = f"""
    <div class="button-group">
        <div style="position: relative; text-align: center;">
            <div class="main-button-overlay" data-page="upload" title="FILE UPLOAD"></div>
            <img src="data:image/svg+xml;base64,{fileupload_button}" alt="File Upload" style="width: 174px; height: 161px;" />
        </div>
        <div style="position: relative; text-align: center;">
            <div class="main-button-overlay" data-page="filelist" title="FILE LIST"></div>
            <img src="data:image/svg+xml;base64,{filelist_button}" alt="File List" style="width: 174px; height: 161px;" />
        </div>
        <div style="position: relative; text-align: center;">
            <div class="main-button-overlay" data-page="chatbot" title="CHAT-BOT"></div>
            <img src="data:image/svg+xml;base64,{chatbot_button}" alt="Chat Bot" style="width: 174px; height: 161px;" />
        </div>
        <div style="position: relative; text-align: center;">
            <div class="main-button-overlay" data-page="help" title="HELP"></div>
            <img src="data:image/svg+xml;base64,{help_button}" alt="Help" style="width: 174px; height: 161px;" />
        </div>
    </div>
    
    <script>
    function navigateToPage(page) {{
        console.log('Navigating to:', page);
        
        // 세션 상태 업데이트를 위한 이벤트 발생
        const event = new CustomEvent('pageNavigation', {{ 
            detail: {{ page: page }}
        }});
        document.dispatchEvent(event);
        
        // Streamlit에 페이지 변경 신호 전송
        if (window.parent) {{
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                data: {{ page_view: page }}
            }}, '*');
        }}
    }}
    
    // DOM이 로드된 후 이벤트 리스너 등록
    document.addEventListener('DOMContentLoaded', function() {{
        const overlays = document.querySelectorAll('.main-button-overlay');
        overlays.forEach(overlay => {{
            overlay.addEventListener('click', function() {{
                const page = this.getAttribute('data-page');
                if (page) {{
                    navigateToPage(page);
                }}
            }});
        }});
    }});
    
    // 페이지가 이미 로드된 경우를 위한 즉시 실행
    setTimeout(() => {{
        const overlays = document.querySelectorAll('.main-button-overlay');
        overlays.forEach(overlay => {{
            if (!overlay.hasAttribute('data-listener-added')) {{
                overlay.addEventListener('click', function() {{
                    const page = this.getAttribute('data-page');
                    if (page) {{
                        navigateToPage(page);
                    }}
                }});
                overlay.setAttribute('data-listener-added', 'true');
            }}
        }});
    }}, 100);
    </script>
    """
    
    st.markdown(button_html, unsafe_allow_html=True)

if __name__ == "__main__":
    show()
