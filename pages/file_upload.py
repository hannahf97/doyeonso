import streamlit as st
import os
import time
import base64
import pandas as pd
from utils.auto_processor import process_uploaded_file_auto, get_processing_statistics
from utils.file_upload_utils import is_allowed_file, validate_file_size, get_file_info
from services.database_service import db_service

@st.cache_data(ttl=30)  # 30초간 캐시로 더 자주 갱신
def get_cached_domyun_data(cache_key=0):
    """데이터베이스 조회 결과를 캐시"""
    domyun_files = db_service.get_all_domyun_files()
    analysis_result = db_service.analyze_domyun_data(domyun_files)
    return domyun_files, analysis_result

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
    }
    
    .summary-title {
        font-size: 70px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 0px;
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
        .title-korean {
            font-size: 36px;
        }
        
        .upload-area {
            padding: 40px 20px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    

    
    # 제목 섹션
    st.markdown("""
    <div class="title-section">
        <img src="data:image/svg+xml;base64,{}" style="max-width: 400px; height: auto; margin-left: -950px;">
    </div>
    """.format(get_base64_encoded_svg("assets/img/file_upload_title.svg") or ""), unsafe_allow_html=True)
    
    # 파일 업로드 위젯 (스타일링된)
    st.markdown("""
    <style>
    /* 파일 업로더 스타일링 */
    .stFileUploader > div > div {{
        background: #f8f9fa;
        border: 3px dashed #bdc3c7;
        border-radius: 15px;
        padding: 60px 40px;
        text-align: center;
        transition: all 0.3s ease;
    }}
    
    .stFileUploader > div > div:hover {{
        border-color: #3498db;
        background: #ecf0f1;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }}
    
    .stFileUploader label {{
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #2c3e50 !important;
        margin-bottom: 20px !important;
    }}
    
    .stFileUploader small {{
        color: #7f8c8d !important;
        font-size: 14px !important;
    }}
    </style>
    
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Choose a file or drag & drop it here",
        type=['jpg', 'jpeg', 'png', 'pdf'],
        accept_multiple_files=True,
        help="PDF and Images formats • 최대 10MB"
    )
    
    # 업로드된 파일이 있을 때 처리
    if uploaded_files:
        # 세션 상태에서 처리된 파일 추적
        if 'processed_files' not in st.session_state:
            st.session_state.processed_files = set()
        
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
        files_processed = False
        for i, uploaded_file in enumerate(uploaded_files):
            # 이미 처리된 파일인지 확인 (파일명 + 크기로 식별)
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            if file_id in st.session_state.processed_files:
                continue
            
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
                
                # 성공 시 처리 완료 파일 목록에 추가
                if workflow_result['success']:
                    st.session_state.processed_files.add(file_id)
                    files_processed = True
                    # 성공 메시지 제거
                else:
                    st.error(f"❌ {uploaded_file.name} 처리 실패: {workflow_result.get('error_message', '알 수 없는 오류')}")
        
        # 파일 처리 완료 (캐시는 cache_key 변경으로 자동 갱신됨)
    
    # QUICK SUMMARY 섹션
    st.markdown("""
    <div class="summary-section" style="transform: scale(0.5); margin-left: -1050px;">
        <div class="summary-title">QUICK SUMMARY</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 데이터베이스에서 데이터 조회 (파일 업로드 후 또는 페이지 로드 시)
    # 파일이 새로 처리되었다면 캐시를 강제로 새로고침
    cache_key = len(st.session_state.get('processed_files', set()))
    domyun_files, analysis_result = get_cached_domyun_data(cache_key)
    
    # 파일 리스트와 분석된 데이터 표시
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 데이터베이스에서 가져온 파일 리스트
        file_names = [file_data['d_name'] for file_data in domyun_files]
        
        st.subheader(f"📁 FILE LIST ({len(file_names)} files)")
        
        if file_names:
            # 세션 상태에서 선택된 파일 추적
            if 'selected_file' not in st.session_state:
                st.session_state.selected_file = file_names[0] if file_names else None
            
            # 파일 리스트를 테이블로 표시
            file_table_data = []
            for file_name in file_names:
                file_table_data.append({
                    'Select': file_name == st.session_state.selected_file,
                    'File Name': file_name
                })
            
            # 파일 선택 테이블 (데이터 크기에 맞춰 자동 조정)
            table_height = 80 + len(file_table_data) * 40  # 헤더 80px + 각 행 40px
            selected_df = st.data_editor(
                file_table_data,
                column_config={
                    'Select': st.column_config.CheckboxColumn(
                        'Select',
                        help='Select file to analyze',
                        default=False,
                        width='small'
                    ),
                    'File Name': st.column_config.TextColumn(
                        'File Name',
                        help='Uploaded file names',
                        width='large'
                    )
                },
                hide_index=True,
                use_container_width=True,
                height=table_height,  # 데이터 크기에 맞춰 높이 조정
                key=f'file_selector_{len(file_table_data)}'  # 키를 동적으로 변경
            )
            
            # 선택된 파일 업데이트
            selected_files = [row['File Name'] for row in selected_df if row['Select']]
            if selected_files:
                # 가장 마지막에 선택된 파일을 현재 선택으로 설정
                if selected_files[-1] != st.session_state.selected_file:
                    st.session_state.selected_file = selected_files[-1]
                    st.rerun()
        else:
            st.warning("No files uploaded yet")
            st.session_state.selected_file = None
    
    with col2:
        # 선택된 파일에 대한 분석 결과 표시
        selected_file = st.session_state.get('selected_file', None)
        
        if selected_file:
            st.subheader(f"📊 Equipment Analysis Summary - {selected_file}")
            
            # 선택된 파일에 대한 데이터만 분석
            selected_file_data = None
            for file_data in domyun_files:
                if file_data['d_name'] == selected_file:
                    selected_file_data = file_data
                    break
            
            if selected_file_data:
                # 선택된 파일만 분석
                selected_analysis = db_service.analyze_domyun_data([selected_file_data])
                combined_items = selected_analysis.get('combined_items', [])
                
                if combined_items:
                    # DataFrame 직접 생성 (시퀀스 번호 완전 제거)
                    
                    df_data = {
                        'ITEM': [],
                        "Q'ty": [],
                        'Source': []
                    }
                    
                    for item in combined_items[:15]:  # 상위 15개 표시
                        sources_text = " + ".join(item['sources']) if item['sources'] else "Unknown"
                        df_data['ITEM'].append(item['item_name'][:30])
                        df_data["Q'ty"].append(item['quantity'])
                        df_data['Source'].append(sources_text)
                    
                    # DataFrame으로 테이블 표시 (인덱스 완전 숨김)
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # 분석 통계 표시
                    st.markdown("---")
                    col_ocr, col_det = st.columns(2)
                    with col_ocr:
                        st.metric("OCR Items", len(selected_analysis.get('ocr_items', [])))
                    with col_det:
                        st.metric("Detection Items", len(selected_analysis.get('detection_items', [])))
                else:
                    st.info(f"📊 No equipment data found for {selected_file}")
            else:
                st.error(f"❌ File data not found: {selected_file}")
        else:
            st.subheader("📊 Equipment Analysis Summary")
            st.info("👈 Please select a file from the list to view analysis results")
    


if __name__ == "__main__":
    show() 