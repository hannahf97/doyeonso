# 챗봇 페이지
# HTML/CSS 기반 챗봇 화면 구현 예정
import streamlit as st

def render_chatbot():
    """챗봇 페이지 렌더링"""
    chatbot_html = """
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
        <div class="page-title">챗봇 페이지입니다</div>
        <!-- 여기에 챗봇 페이지 내용이 추가될 예정입니다 -->
    </div>
    """
    
    st.markdown(chatbot_html, unsafe_allow_html=True) 