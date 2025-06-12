import streamlit as st
import base64
from config.database_config import get_db_connection

@st.cache_data(ttl=30)  # 30초 캐시
def get_recent_drawings():
    """최근 도면 데이터를 DB에서 가져오기"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d_name, "user", create_date 
            FROM domyun 
            ORDER BY create_date DESC 
            LIMIT 4
        """)
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # 결과를 리스트로 변환
        drawings = []
        for result in results:
            d_name, user, create_date = result
            # 날짜 포맷팅
            formatted_date = create_date.strftime("%Y-%m-%d") if create_date else "N/A"
            drawings.append({
                'name': d_name,
                'user': user,
                'date': formatted_date
            })
        
        return drawings
        
    except Exception as e:
        print(f"데이터베이스 조회 오류: {e}")
        return []

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

    /* 테이블 컨테이너 스타일 */
    .home-table-container {
        margin-top: 80px;
        display: flex;
        justify-content: center;
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
    }
    
    /* 테이블 스타일 - 파일업로드 페이지와 동일 */
    .home-summary-table {
        background: white;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        margin: 20px 0;
        width: 100%;
        max-width: 736px; /* 버튼 4개 + 간격 너비 (174*4 + 40*3) */
    }
    
    .home-table-header {
        background: #34495e;
        color: white;
        padding: 15px;
        font-weight: 600;
        text-align: center;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .home-table-header > div {
        flex: 1;
        text-align: center;
    }
    
    .home-table-row {
        padding: 12px 15px;
        border-bottom: 1px solid #ecf0f1;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .home-table-row > div {
        flex: 1;
        text-align: center;
        padding: 0 10px;
    }
    
    .home-table-row:hover {
        background: #f8f9fa;
    }
    
    .home-table-row:last-child {
        border-bottom: none;
    }
    
    /* 반응형 조정 */
    @media (max-width: 768px) {
        .home-summary-table {
            max-width: 560px; /* 140*4 */
        }
    }
    
    @media (max-width: 480px) {
        .home-summary-table {
            max-width: 480px; /* 120*4 */
        }
        
        .home-table-header {
            padding: 10px 8px;
            font-size: 14px;
        }
        
        .home-table-row {
            padding: 8px 5px;
            font-size: 12px;
        }
        
        .home-table-row > div {
            padding: 0 5px;
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
    
    # 테이블 데이터 가져오기
    drawings = get_recent_drawings()
    
    # Streamlit 컬럼을 사용하여 테이블 형태로 만들기
    # 공통 스타일 정의
    common_style = """
    <style>
    .home-table-container {
        display: flex;
        justify-content: center;
        width: 100%;
        margin-top: 80px;
    }
    
    .home-table {
        width: 776px;  /* 버튼 4개(174*4=696px) + 간격(40*2=80px) */
        background: white;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        overflow: hidden;
    }
    
    .home-table-header {
        background: #34495e;
        color: white;
        padding: 15px;
        font-weight: 600;
        display: flex;
        align-items: center;
    }
    
    .table-cell {
        flex: 1;
        text-align: center;
        padding: 0 10px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .table-row {
        display: flex;
        align-items: center;
        padding: 12px 15px;
        border-bottom: 1px solid #ecf0f1;
    }
    
    .table-row:last-child {
        border-bottom: none;
    }
    
    .table-row:hover {
        background-color: #f8f9fa;
    }
    </style>
    """
    st.markdown(common_style, unsafe_allow_html=True)
    
    # 헤더 렌더링
    st.markdown("""
    <div class="home-table-container">
        <div class="home-table">
            <div class="home-table-header">
                <div class="table-cell">FILE NAME</div>
                <div class="table-cell">DRAWN BY</div>
                <div class="table-cell">DRAWN DATE</div>
            </div>
    """, unsafe_allow_html=True)
    
    # 4개 행 생성
    for i in range(4):
        if i < len(drawings):
            drawing = drawings[i]
            name = drawing["name"]
            user = drawing["user"] 
            date = drawing["date"]
        else:
            name = "-"
            user = "-"
            date = "-"
        
        # 행 스타일 (마지막 행은 border 없음)
        border_style = "" if i == 3 else "border-bottom: 1px solid #ecf0f1;"
        row_html = f"""
            <div class="table-row" style="{border_style}">
                <div class="table-cell">{name}</div>
                <div class="table-cell">{user}</div>
                <div class="table-cell">{date}</div>
            </div>
        """
        st.markdown(row_html, unsafe_allow_html=True)
    
    # 테이블 닫기
    st.markdown("</div></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    show()
