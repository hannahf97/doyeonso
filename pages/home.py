# 홈 페이지
# HTML/CSS 기반 홈 화면 구현 예정
import streamlit as st

def render_home():
    """홈 페이지 렌더링"""
    home_html = """
    <style>
    .main-content {
        margin-left: 260px;
        padding: 20px;
        min-height: 100vh;
    }
    .page-title {
        font-size: 24px;
        font-weight: bold;
        color: #357196;
        margin-bottom: 20px;
    }
    </style>
    
    <div class="main-content">
        <div class="page-title">홈 페이지입니다</div>
        <!-- 여기에 홈 페이지 내용이 추가될 예정입니다 -->
    </div>
    """
    
    st.markdown(home_html, unsafe_allow_html=True) 