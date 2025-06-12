import streamlit as st
import os
import time
import base64
from utils.auto_processor import process_uploaded_file_auto, get_processing_statistics
from utils.file_upload_utils import is_allowed_file, validate_file_size, get_file_info

def get_base64_encoded_svg(svg_path):
    """SVG 파일을 base64로 인코딩"""
    try:
        with open(svg_path, "rb") as f:
            contents = f.read()
        return base64.b64encode(contents).decode("utf-8")
    except FileNotFoundError:
        return None

def show():
    # 페이지 스타일링
    st.markdown("""
    <style>
    
    /* 메인 컨테이너 */
    .main-container {
        background: white;
        border-radius: 20px;
        padding: 40px;
        margin: 20px auto;
        max-width: 1200px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }
    
    /* 제목 영역 */
    .title-section {
        text-align: center;
        margin-bottom: 40px;
    }
    
    .title-korean {
        font-size: 48px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 10px;
        font-family: 'Noto Sans KR', sans-serif;
    }
    
    .title-english {
        font-size: 24px;
        color: #7f8c8d;
        font-weight: 300;
        letter-spacing: 2px;
    }
    
    /* 업로드 영역 */
    .upload-area {
        border: 3px dashed #bdc3c7;
        border-radius: 15px;
        padding: 60px 40px;
        text-align: center;
        background: #f8f9fa;
        margin: 30px 0;
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: #3498db;
        background: #ecf0f1;
    }
    
    .upload-icon {
        width: 80px;
        height: 80px;
        margin: 0 auto 20px;
        opacity: 0.6;
    }
    
    .upload-text {
        font-size: 24px;
        color: #2c3e50;
        margin-bottom: 10px;
        font-weight: 600;
    }
    
    .upload-subtext {
        font-size: 16px;
        color: #7f8c8d;
        margin-bottom: 30px;
    }
    
    /* 파일 프레임 */
    .file-frame {
        background: white;
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        border: 1px solid #ecf0f1;
    }
    
    .file-frame h4 {
        color: #2c3e50;
        margin-bottom: 15px;
        font-size: 18px;
    }
    
    /* 요약 섹션 */
    .summary-section {
        margin-top: 40px;
        padding: 30px;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
    }
    
    .summary-title {
        font-size: 28px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .file-list-item {
        background: white;
        padding: 15px 20px;
        margin: 10px 0;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .file-list-item.selected {
        border-left-color: #e74c3c;
        background: #fff5f5;
    }
    
    /* 테이블 스타일 */
    .summary-table {
        background: white;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    
    .table-header {
        background: #34495e;
        color: white;
        padding: 15px;
        font-weight: 600;
        text-align: center;
    }
    
    .table-row {
        padding: 12px 15px;
        border-bottom: 1px solid #ecf0f1;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .table-row:hover {
        background: #f8f9fa;
    }
    
    /* 상태 표시 */
    .status-uploading {
        color: #f39c12;
        font-weight: 600;
    }
    
    .status-completed {
        color: #27ae60;
        font-weight: 600;
    }
    
    /* PDF 태그 */
    .pdf-tag {
        background: #e74c3c;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
        margin-right: 10px;
    }
    
    /* 반응형 디자인 */
    @media (max-width: 768px) {
        .main-container {
            margin: 10px;
            padding: 20px;
        }
        
        .title-korean {
            font-size: 36px;
        }
        
        .upload-area {
            padding: 40px 20px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 메인 컨테이너 시작
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # 제목 섹션
    st.markdown("""
    <div class="title-section">
        <img src="data:image/svg+xml;base64,{}" style="max-width: 400px; height: auto;">
    </div>
    """.format(get_base64_encoded_svg("assets/img/file_upload_title.svg") or ""), unsafe_allow_html=True)
    
    # 업로드 영역
    st.markdown("""
    <div class="upload-area">
        <div class="upload-icon">
            <img src="data:image/svg+xml;base64,{}" style="width: 120px; height: 120px;">
        </div>
        <div class="upload-text">Choose a file or drag & drop it here</div>
        <div class="upload-subtext">PDF and Images formats</div>
    </div>
    """.format(get_base64_encoded_svg("assets/img/upload_image.svg") or ""), unsafe_allow_html=True)
    
    # 파일 업로드 위젯
    uploaded_files = st.file_uploader(
        "",
        type=['jpg', 'jpeg', 'png', 'pdf'],
        accept_multiple_files=True,
        help="🎯 지원 형식: JPG, PNG, PDF | 최대 10MB",
        label_visibility="collapsed"
    )
    
    # 업로드된 파일이 있을 때 처리
    if uploaded_files:
        # 파일 프레임들 표시
        col1, col2 = st.columns(2)
        
        for i, uploaded_file in enumerate(uploaded_files):
            with col1 if i % 2 == 0 else col2:
                # 파일 프레임
                st.markdown(f"""
                <div class="file-frame">
                    <h4>Frame {i + 17}</h4>
                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                        <div class="pdf-tag">PDF</div>
                        <div style="flex: 1;">
                            <div style="font-weight: 600; color: #2c3e50;">{uploaded_file.name}</div>
                            <div style="font-size: 12px; color: #7f8c8d;">
                                {uploaded_file.size // 1024} KB of {uploaded_file.size // 1024} KB • 
                                <span class="status-completed">✓ Completed</span>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # 파일 처리 로직 (백그라운드에서 실행)
        for i, uploaded_file in enumerate(uploaded_files):
            # 파일 검증
            if not is_allowed_file(uploaded_file.name):
                st.error("❌ 지원하지 않는 파일 형식입니다.")
                continue
            
            file_bytes = uploaded_file.getvalue()
            is_valid_size, size_error = validate_file_size(file_bytes)
            if not is_valid_size:
                st.error(f"❌ {size_error}")
                continue
            
            # 자동 처리 (백그라운드에서 실행)
            with st.spinner(f"🔄 {uploaded_file.name} 처리 중..."):
                workflow_result = process_uploaded_file_auto(
                    file_bytes, 
                    uploaded_file.name
                )
                
                if workflow_result['success']:
                    st.success(f"✅ {uploaded_file.name} 처리 완료!")
                else:
                    st.error(f"❌ {uploaded_file.name} 처리 실패: {workflow_result.get('error_message', '알 수 없는 오류')}")
    
    # QUICK SUMMARY 섹션
    st.markdown("""
    <div class="summary-section">
        <div class="summary-title">QUICK SUMMARY</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 파일 리스트와 테이블 템플릿
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("""
        <div class="summary-table">
            <div class="table-header">FILE LIST</div>
            <div class="file-list-item selected">
                <input type="checkbox" checked style="margin-right: 10px;">
                <span style="color: #3498db; font-weight: 600;">FILE NAME</span>
            </div>
            <div class="file-list-item">FILE NAME</div>
            <div class="file-list-item">FILE NAME</div>
            <div class="file-list-item">FILE NAME</div>
            <div class="file-list-item">FILE NAME</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="summary-table">
            <div class="table-header">Table Template</div>
            <div class="table-row">
                <span><strong>No.</strong></span>
                <span><strong>ITEM</strong></span>
                <span><strong>Q'ty</strong></span>
            </div>
            <div class="table-row">
                <span>1</span>
                <span>GATE VALVE</span>
                <span>20</span>
            </div>
            <div class="table-row">
                <span>2</span>
                <span>FLOW CONTROLLER</span>
                <span>15</span>
            </div>
            <div class="table-row">
                <span>3</span>
                <span>FLOW VALVE</span>
                <span>3</span>
            </div>
            <div class="table-row">
                <span>4</span>
                <span>LEVEL CONTROLLER</span>
                <span>6</span>
            </div>
            <div class="table-row">
                <span>5</span>
                <span>LEVEL CONTROLLER</span>
                <span>2</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="summary-table">
            <div class="table-header">Table Template</div>
            <div class="table-row">
                <span><strong>No.</strong></span>
                <span><strong>ITEM</strong></span>
                <span><strong>Q'ty</strong></span>
            </div>
            <div class="table-row">
                <span>6</span>
                <span>GATE VALVE</span>
                <span>20</span>
            </div>
            <div class="table-row">
                <span>7</span>
                <span>FLOW CONTROLLER</span>
                <span>15</span>
            </div>
            <div class="table-row">
                <span>8</span>
                <span>FLOW VALVE</span>
                <span>3</span>
            </div>
            <div class="table-row">
                <span>9</span>
                <span>LEVEL CONTROLLER</span>
                <span>6</span>
            </div>
            <div class="table-row">
                <span>10</span>
                <span>LEVEL CONTROLLER</span>
                <span>2</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 메인 컨테이너 종료
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    show() 