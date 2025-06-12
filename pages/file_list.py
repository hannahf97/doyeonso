import streamlit as st
import os
from datetime import datetime
import math
from pathlib import Path
import psycopg2
import pandas as pd
from config.database_config import get_db_connection
import base64

def load_svg(svg_path):
    """SVG 파일을 문자열로 로드"""
    if os.path.exists(svg_path):
        with open(svg_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def init_session_state():
    """세션 상태 초기화"""
    if "selected_file_id" not in st.session_state:
        st.session_state.selected_file_id = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

def create_pagination(total_pages, current_page):
    """페이지네이션 UI 생성"""
    cols = st.columns([1, 2, 1])
    
    with cols[1]:
        pagination_cols = st.columns(min(5, total_pages + 2))
        
        # Previous 버튼
        if pagination_cols[0].button("Previous", disabled=current_page == 1):
            st.session_state.current_page = max(1, current_page - 1)
            st.rerun()
            
        # 페이지 번호 버튼
        for i, col in enumerate(pagination_cols[1:-1], 1):
            if i <= total_pages:
                button_style = "primary" if i == current_page else "secondary"
                if col.button(str(i), type=button_style):
                    st.session_state.current_page = i
                    st.rerun()
                    
        # Next 버튼
        if pagination_cols[-1].button("Next", disabled=current_page == total_pages):
            st.session_state.current_page = min(total_pages, current_page + 1)
            st.rerun()

def show_file_card(col, file_data, index):
    """파일 카드 UI 생성"""
    with col:
        # 선택 상태 확인
        selected = st.session_state.selected_file_id == index
        
        # 카드 스타일
        card_style = f"""
        <style>
            .file-card-{index} {{
                text-align: center;
                padding: 15px;
                margin-bottom: 0;
                background-color: white;
            }}

            .file-content-{index} img {{
                max-width: 100%;
                height: auto;
                margin-bottom: 10px;
            }}

            .file-info-{index} {{
                margin-bottom: 10px;
            }}

            .select-button-{index} {{
                width: 100%;
            }}

            /* 열 간격 제거 */
            .row-widget.stHorizontal {{
                gap: 0 !important;
            }}
            
            /* Streamlit 기본 여백 제거 */
            .row-widget.stHorizontal > div {{
                margin: 0 !important;
                padding: 0 !important;
            }}
            
            .element-container, .stVerticalBlock {{
                margin: 0 !important;
                padding: 0 !important;
            }}

            /* 이미지 컨테이너 및 이미지 스타일 */
            [data-testid="stImage"] {{
                position: relative;
                width: 100%;
                padding-bottom: 66.67%; /* 3:2 비율 (높이가 너비의 2/3) */
            }}

            [data-testid="stImage"] > img {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                object-fit: cover;
            }}

            /* 기본 아이콘 컨테이너도 동일한 비율 적용 */
            .default-icon-container {{
                position: relative;
                width: 100%;
                padding-bottom: 66.67%;
                background-color: #f0f2f6;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
            }}

            .default-icon {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 40px;
                color: #666;
            }}
        </style>
        """
        st.markdown(card_style, unsafe_allow_html=True)
        
        # 카드 컨테이너 시작
        # st.markdown(f'<div class="file-card-{index}">', unsafe_allow_html=True)
        
        # 이미지 표시
        try:
            st.image(file_data["image_path"], use_column_width=True)
        except Exception:
            try:
                st.image("assets/img/default_bear.png", use_column_width=True)
            except Exception:
                # 기본 이미지도 로드 실패시 아이콘 표시
                st.markdown("""
                    <div class="default-icon-container">
                        <span class="default-icon">📄</span>
                    </div>
                """, unsafe_allow_html=True)
        
        # 파일 정보 컨테이너
        # st.markdown(f'<div class="file-info-{index}">', unsafe_allow_html=True)
        st.markdown(f"**{file_data['d_name']}**")
        st.markdown(f"<small>{file_data['create_date']}</small>", unsafe_allow_html=True)
        # st.markdown('</div>', unsafe_allow_html=True)
        
        # 선택 버튼 컨테이너
        # st.markdown(f'<div class="select-button-{index}">', unsafe_allow_html=True)
        if st.button("선택", key=f"select_{index}"):
            st.session_state.selected_file_id = index if not selected else None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 카드 컨테이너 종료
        st.markdown('</div>', unsafe_allow_html=True)

def get_file_list():
    """DB에서 파일 목록 조회 및 기본 데이터 추가"""
    try:
        conn = get_db_connection()
        if not conn:
            st.error("데이터베이스 연결 실패")
            return []
            
        query = "SELECT image_path, d_name, create_date FROM domyun ORDER BY create_date DESC"
        df = pd.read_sql_query(query, conn)
        file_list = df.to_dict('records')
        
        # DB 데이터가 부족한 경우 기본 데이터로 채우기
        while len(file_list) < 7:  # 최소 7개의 항목 유지
            idx = len(file_list) + 1
            file_list.append({
                "image_path": "assets/img/default_bear.png",
                "d_name": f"파일 {idx}",
                "create_date": datetime.now().strftime("%Y-%m-%d")
            })
        
        return file_list
    except Exception as e:
        st.error(f"DB 조회 중 오류 발생: {str(e)}")
        # 오류 발생 시 기본 데이터만 반환
        return [
            {
                "image_path": "assets/img/default_bear.png",
                "d_name": f"파일 {i}",
                "create_date": datetime.now().strftime("%Y-%m-%d")
            }
            for i in range(1, 8)  # 7개의 기본 데이터
        ]
    finally:
        if 'conn' in locals():
            conn.close()

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
    """파일 목록 페이지"""
    init_session_state()
    
    # 스타일 설정
    st.markdown("""
        <style>
            .block-container {
                padding-top: 0 !important;
                padding-bottom: 0;
            }
            .stButton button {
                width: 100%;
            }
            footer {
                display: none;
            }
            .element-container {
                margin-top: 0 !important;
            }
            .stMarkdown {
                margin-top: 0 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # 전체 화면 스타일 적용
    st.markdown("""
        <style>
            /* 메인 컨테이너 스타일 */
            .main .block-container {
                padding: 1rem 2rem;
                max-width: 100%;
                width: calc(100% - 260px);
                min-height: 100vh;
            }
            
            /* Streamlit 기본 패딩 제거 */
            .stApp {
                margin: 0;
                padding: 0;
            }
            
            /* columns 간격 조정 */
            [data-testid="column"] {
                padding: 0 !important;
                margin: 0 !important;
            }

            [data-testid="stHorizontalBlock"] {
                gap: 0.5rem !important;
            }
            
            /* 타이틀 이미지 스타일 */
            .title-image {
                width: 266px;  
                height: auto;
                margin: 0;
                display: block;
                margin-bottom: 0; 
            }
            
            /* 전체 컨텐츠 컨테이너 */
            .content-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 2rem 0.5rem 2rem; 
            }
            
            /* 카드 그리드 컨테이너 */
            .grid-container {
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 0.33rem;
                padding: 0;
                margin: 0;
            }
            
            /* 카드 스타일 */
            .file-card {
                width: calc(33.33% - 1rem);
                min-width: 250px;
                margin-bottom: 1rem;
                text-align: center;
            }
            
            /* 이미지 크기 조정 */
            .stImage img {
                max-height: 150px;
                object-fit: contain;
                margin: 0 auto;
            }
            
            /* 페이지네이션 스타일 */
            [data-testid="stHorizontalBlock"] {
                justify-content: center;
                gap: 0.5rem;
            }
            
            /* 버튼 스타일 */
            .stButton button {
                min-width: 40px;
                height: 35px;
                padding: 0 10px;
            }

            /* Streamlit 푸터 숨기기 */
            footer {
                display: none !important;
            }

            /* 푸터 영역 제거 */
            .stApp > footer {
                display: none !important;
            }

            /* 기타 Streamlit 워터마크 숨기기 */
            #MainMenu {
                display: none !important;
            }

            [data-testid="stToolbar"] {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # 전체 컨텐츠 컨테이너 시작
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    
    # 타이틀 SVG 로드 및 표시
    title_svg = get_base64_encoded_svg("assets/img/filelisttitle.svg")
    if title_svg:
        st.markdown(f"""
            <img src="data:image/svg+xml;base64,{title_svg}" class="title-image" alt="File List Title">
        """, unsafe_allow_html=True)


    # 카드 그리드 컨테이너 시작
    st.markdown('<div class="grid-container">', unsafe_allow_html=True)
    
    # 파일 목록 가져오기
    files = get_file_list()
    
    # 페이지네이션 계산
    items_per_page = 6
    total_items = len(files)
    total_pages = math.ceil(total_items / items_per_page)
    current_page = st.session_state.current_page
    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    
    # 현재 페이지의 아이템들 표시
    current_items = files[start_idx:end_idx]
    
    # 3열 그리드 생성
    for i in range(0, len(current_items), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(current_items):
                show_file_card(col, current_items[i + j], start_idx + i + j)
    
    # 카드 그리드 컨테이너 종료
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 페이지네이션 UI
    st.markdown("<br>", unsafe_allow_html=True)
    create_pagination(total_pages, current_page)
    
    # 전체 컨텐츠 컨테이너 종료
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    show() 