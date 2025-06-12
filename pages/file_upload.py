import streamlit as st
import os
import time
from utils.auto_processor import process_uploaded_file_auto, get_processing_statistics
from utils.file_upload_utils import is_allowed_file, validate_file_size, get_file_info

def show():
    # 메인 헤더
    st.title("🚀 자동 파일 처리 시스템")
    st.markdown("**파일 업로드 → PNG 변환 → OCR → 통합 JSON → 데이터베이스 저장까지 완전 자동화!**")
    st.markdown("---")
    
    # 통계 정보 표시
    stats = get_processing_statistics()
    
    st.markdown("### 📊 실시간 처리 현황")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📁 총 처리 파일", stats['total_files'])
    
    with col2:
        st.metric("✅ 완료된 통합", stats['total_merged'])
    
    with col3:
        st.metric("📅 오늘 처리", stats['today_files'])
    
    with col4:
        st.metric("📈 성공률", f"{stats['success_rate']:.1f}%")
    
    # 업로드 폴더 생성
    upload_dirs = [
        'uploads/uploaded_images',
        'uploads/ocr_results',
        'uploads/detection_results',
        'uploads/merged_results'
    ]
    
    for dir_path in upload_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    
    # 파일 업로드 섹션
    st.markdown("## 📂 파일 업로드")
    
    uploaded_files = st.file_uploader(
        "🎯 지원 형식: JPG, PNG, PDF | 최대 10MB",
        type=['jpg', 'jpeg', 'png', 'pdf'],
        accept_multiple_files=True,
        help="파일을 선택하면 자동으로 모든 처리가 시작됩니다!"
    )
    
    if uploaded_files:
        for i, uploaded_file in enumerate(uploaded_files):
            st.markdown(f"### 📄 {uploaded_file.name}")
            
            # 파일 검증
            if not is_allowed_file(uploaded_file.name):
                st.error("❌ 지원하지 않는 파일 형식입니다.")
                continue
            
            # 파일 크기 검증
            file_bytes = uploaded_file.getvalue()
            is_valid_size, size_error = validate_file_size(file_bytes)
            if not is_valid_size:
                st.error(f"❌ {size_error}")
                continue
            
            # 파일 정보 표시
            file_info = get_file_info(uploaded_file)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📦 파일 크기", f"{file_info['size']:.2f} MB")
            with col2:
                st.metric("🎨 파일 형식", file_info['type'])
            with col3:
                st.metric("📋 파일명", file_info['name'])
            
            # 자동 처리 시작
            progress_placeholder = st.empty()
            steps_placeholder = st.empty()
            results_placeholder = st.empty()
            
            # 프로그레스 바 초기화
            progress_bar = progress_placeholder.progress(0)
            
            with st.spinner("🔄 자동 처리 시작..."):
                # 완전 자동화 처리 실행 (이미 읽은 file_bytes 재사용)
                workflow_result = process_uploaded_file_auto(
                    file_bytes, 
                    uploaded_file.name
                )
                
                # 단계별 진행 상황 표시
                total_steps = len(workflow_result['steps_completed'])
                
                for idx, step in enumerate(workflow_result['steps_completed']):
                    progress_bar.progress((idx + 1) / max(total_steps, 1))
                    steps_placeholder.info(step)
                    time.sleep(0.2)  # 시각적 효과
                
                # 최종 결과 표시
                if workflow_result['success']:
                    st.balloons()  # 🎉 성공 효과
                    
                    results_placeholder.success("🎉 처리 완료! 모든 단계가 성공적으로 완료되었습니다.")
                    
                    # 처리 결과 상세 정보
                    st.markdown("#### 📋 처리 결과 상세")
                    
                    if 'processed_images' in workflow_result['results']:
                        for img_result in workflow_result['results']['processed_images']:
                            img_name = os.path.basename(img_result['image_path'])
                            
                            # 결과 탭
                            tab1, tab2, tab3 = st.tabs(["🖼️ 이미지 정보", "🔍 OCR 결과", "📊 통합 JSON"])
                            
                            with tab1:
                                st.info(f"💾 저장 경로: `{img_result['image_path']}`")
                                
                                # 이미지 표시
                                if os.path.exists(img_result['image_path']):
                                    st.image(img_result['image_path'], caption=img_name, width=300)
                            
                            with tab2:
                                if img_result['ocr_result'] and img_result['ocr_result']['success']:
                                    ocr_data = img_result['ocr_result']
                                    
                                    if ocr_data.get('extracted_text'):
                                        st.text_area(
                                            "📝 추출된 텍스트",
                                            value=ocr_data['extracted_text'],
                                            height=200,
                                            key=f"ocr_text_{i}_{img_name}"
                                        )
                                    
                                    # OCR 파일 다운로드
                                    if ocr_data.get('json_path') and os.path.exists(ocr_data['json_path']):
                                        with open(ocr_data['json_path'], 'r', encoding='utf-8') as f:
                                            json_content = f.read()
                                        
                                        st.download_button(
                                            label="📥 OCR JSON 다운로드",
                                            data=json_content,
                                            file_name=f"ocr_{img_name}.json",
                                            mime='application/json',
                                            key=f"download_ocr_{i}_{img_name}"
                                        )
                                    
                                    if ocr_data.get('txt_path') and os.path.exists(ocr_data['txt_path']):
                                        with open(ocr_data['txt_path'], 'r', encoding='utf-8') as f:
                                            txt_content = f.read()
                                        
                                        st.download_button(
                                            label="📥 OCR 텍스트 다운로드",
                                            data=txt_content,
                                            file_name=f"ocr_{img_name}.txt",
                                            mime='text/plain',
                                            key=f"download_txt_{i}_{img_name}"
                                        )
                                else:
                                    st.error("OCR 처리에 실패했습니다.")
                            
                            with tab3:
                                if img_result['integrated_result'] and img_result['integrated_result']['success']:
                                    integrated_data = img_result['integrated_result']
                                    
                                    st.success(f"✅ 통합 JSON 생성: `testsum{integrated_data['sequence']}.json`")
                                    
                                    # DB 저장 결과
                                    if img_result['db_result'] and img_result['db_result']['success']:
                                        st.success(f"💾 데이터베이스 저장 완료 (ID: {img_result['db_result']['db_id']})")
                                    
                                    # 통합 JSON 다운로드
                                    if integrated_data['merged_path'] and os.path.exists(integrated_data['merged_path']):
                                        with open(integrated_data['merged_path'], 'r', encoding='utf-8') as f:
                                            merged_content = f.read()
                                        
                                        st.download_button(
                                            label="📥 통합 JSON 다운로드",
                                            data=merged_content,
                                            file_name=f"testsum{integrated_data['sequence']}.json",
                                            mime='application/json',
                                            key=f"download_merged_{i}_{img_name}"
                                        )
                                        
                                        # JSON 미리보기
                                        st.json(integrated_data['integrated_data'])
                                else:
                                    st.error("통합 JSON 생성에 실패했습니다.")
                    
                else:
                    # 오류 처리
                    results_placeholder.error(f"❌ 처리 실패: {workflow_result.get('error_message', '알 수 없는 오류가 발생했습니다.')}")
                    
                    # 완료된 단계 표시
                    if workflow_result['steps_completed']:
                        st.markdown("#### 📋 처리된 단계:")
                        for step in workflow_result['steps_completed']:
                            st.markdown(f"- {step}")
            
            st.markdown("---")
    
    # 파일 목록 섹션
    st.markdown("---")
    st.markdown("## 📋 저장된 파일 목록")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🖼️ 업로드 이미지", 
        "🔍 OCR 결과", 
        "🎯 Detection 결과", 
        "📊 통합 결과"
    ])
    
    directories = [
        ("uploads/uploaded_images", tab1),
        ("uploads/ocr_results", tab2),
        ("uploads/detection_results", tab3),
        ("uploads/merged_results", tab4)
    ]
    
    for dir_path, tab in directories:
        with tab:
            if os.path.exists(dir_path):
                files = sorted(os.listdir(dir_path))
                if files:
                    st.write(f"**총 {len(files)}개 파일**")
                    for file in files:
                        file_path = os.path.join(dir_path, file)
                        file_size = os.path.getsize(file_path) / 1024  # KB
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"📄 {file}")
                        with col2:
                            st.write(f"{file_size:.1f} KB")
                else:
                    st.info("📁 파일이 없습니다.")
            else:
                st.warning("📁 폴더가 존재하지 않습니다.")
    


if __name__ == "__main__":
    show() 