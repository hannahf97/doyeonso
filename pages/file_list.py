#!/usr/bin/env python3
"""
도면 파일 리스트 페이지
데이터베이스에 저장된 도면 파일들을 미리보기와 상세 정보로 조회
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from PIL import Image
import base64
import io
import os
from config.database_config import get_db_connection
from config.user_config import USER_NAME

def show():
    """파일 리스트 페이지 메인 함수"""
    
    # 헤더
    st.title("📋 도면 파일 리스트")
    st.markdown("데이터베이스에 저장된 도면 파일들을 확인하고 관리할 수 있습니다.")
    
    # 선택된 파일들을 저장할 세션 스테이트 초기화
    if 'selected_files' not in st.session_state:
        st.session_state.selected_files = []
    
    # 데이터베이스 연결 확인
    conn = get_db_connection()
    if not conn:
        st.error("❌ 데이터베이스 연결에 실패했습니다.")
        st.info("PostgreSQL 서버가 실행 중인지 확인해주세요.")
        return
    
    try:
        # 사이드바 - 필터 옵션
        with st.sidebar:
            st.header("🔍 필터 옵션")
            
            # 정렬 옵션
            sort_options = {
                "최신순": "create_date DESC",
                "오래된 순": "create_date ASC", 
                "이름순": "d_name ASC",
                "ID순": "d_id ASC"
            }
            selected_sort = st.selectbox(
                "정렬 방식",
                list(sort_options.keys()),
                key="sort_option"
            )
            
            # 표시 개수
            limit = st.slider(
                "표시할 파일 수",
                min_value=6,
                max_value=50,
                value=12,
                step=6,
                key="limit_slider"
            )
            
            # 검색
            search_term = st.text_input(
                "파일명 검색",
                placeholder="파일명을 입력하세요...",
                key="search_input"
            )
            
            # 새로고침 버튼
            if st.button("🔄 새로고침", key="refresh_btn"):
                st.rerun()
            
            # 선택된 파일 관리 (사이드바에는 목록만 표시)
            st.markdown("---")
            st.header("🎯 선택된 파일")
            
            if st.session_state.selected_files:
                st.write(f"**선택된 파일: {len(st.session_state.selected_files)}개**")
                
                # 선택된 파일 목록 표시
                for file_info in st.session_state.selected_files:
                    st.write(f"• {file_info['name']}")
                
                # 선택 초기화 버튼만 사이드바에 유지
                if st.button("🗑️ 선택 초기화", key="clear_selection", use_container_width=True):
                    st.session_state.selected_files = []
                    st.rerun()
            else:
                st.info("선택된 파일이 없습니다.")
        
        # 메인 컨텐츠 헤더 영역
        header_col1, header_col2 = st.columns([3, 1])
        
        with header_col1:
            st.subheader("📁 파일 목록")
        
        with header_col2:
            # 선택된 파일이 있을 때만 챗봇 전송 버튼 표시
            if st.session_state.selected_files and len(st.session_state.selected_files) > 0:
                if st.button(
                    f"💬 챗봇으로 전송 ({len(st.session_state.selected_files)}개)", 
                    key="send_to_chatbot_main", 
                    use_container_width=True,
                    type="primary"
                ):
                    # 선택된 파일들을 챗봇으로 전송
                    st.session_state['selected_files_for_chat'] = st.session_state.selected_files.copy()
                    # 챗봇 페이지로 자동 이동
                    st.session_state['page_view'] = 'chatbot'
                    st.success(f"{len(st.session_state.selected_files)}개 파일이 챗봇으로 전송되었습니다!")
                    st.rerun()
            else:
                # 선택된 파일이 없을 때는 플레이스홀더 표시
                st.markdown(
                    """
                    <div style="
                        height: 38px; 
                        display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        color: #888; 
                        font-size: 14px;
                    ">
                        파일을 선택해주세요
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        
        # 파일 데이터 조회
        files_data = get_files_data(
            conn, 
            sort_by=sort_options[selected_sort],
            limit=limit,
            search_term=search_term
        )
        
        if not files_data:
            st.warning("📭 조건에 맞는 파일이 없습니다.")
            st.info("다른 필터 조건을 시도해보세요.")
            return
        
        # 전체 선택/해제 체크박스
        col1, col2, col3, col4, col5 = st.columns([1, 1, 3, 2, 2])
        with col1:
            select_all = st.checkbox("전체 선택", key="select_all")
        with col2:
            st.write("**이미지**")
        with col3:
            st.write("**파일명**")
        with col4:
            st.write("**업로드 정보**")
        with col5:
            st.write("**데이터 통계**")

        # 전체 선택 상태 처리 (즉시 반영)
        if select_all and len(st.session_state.selected_files) != len(files_data):
            # 전체 선택 - 전체 파일 데이터 전달
            st.session_state.selected_files = files_data.copy()
            st.rerun()
        elif not select_all and len(st.session_state.selected_files) > 0:
            # 전체 해제 (단, 사용자가 직접 체크를 해제한 경우만)
            if st.session_state.get('manual_uncheck', False):
                st.session_state.selected_files = []
                st.session_state.manual_uncheck = False
                st.rerun()
        
        # 수동 체크 해제 감지
        if not select_all and st.session_state.get('select_all_prev', False):
            st.session_state.manual_uncheck = True
        
        st.session_state['select_all_prev'] = select_all

        # 파일 목록 표시
        for file_data in files_data:
            display_file_row(file_data)
        
    except Exception as e:
        st.error(f"❌ 오류가 발생했습니다: {str(e)}")
    finally:
        if conn:
            conn.close()

def get_files_data(conn, sort_by="create_date DESC", limit=12, search_term=""):
    """파일 데이터 조회"""
    try:
        cursor = conn.cursor()
        
        # 기본 쿼리
        query = """
        SELECT 
            d_id, 
            d_name, 
            "user", 
            create_date, 
            image_path, 
            json_data
        FROM domyun
        """
        
        # WHERE 조건
        conditions = []
        params = []
        
        if search_term:
            conditions.append('d_name ILIKE %s')
            params.append(f'%{search_term}%')
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # ORDER BY와 LIMIT 추가
        query += f" ORDER BY {sort_by} LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        files_data = []
        for row in results:
            d_id, d_name, user, create_date, image_path, json_data = row
            
            # 이미지 경로 확인 및 기본 이미지 설정
            if not image_path or not os.path.exists(image_path):
                image_path = "assets/img/default_bear.png"
            
            # 미리보기 정보 추출
            ocr_count, detection_count, total_objects = extract_preview_info(json_data)
            
            files_data.append({
                'id': d_id,
                'name': d_name,
                'user': user,
                'create_date': create_date,
                'image_path': image_path,
                'ocr_count': ocr_count,
                'detection_count': detection_count,
                'total_objects': total_objects,
                'json_data': json_data
            })
        
        cursor.close()
        return files_data
        
    except Exception as e:
        st.error(f"데이터 조회 중 오류 발생: {str(e)}")
        return []

def extract_preview_info(json_data):
    """JSON 데이터에서 미리보기 정보 추출"""
    ocr_count = 0
    detection_count = 0
    total_objects = 0
    
    if json_data:
        try:
            # OCR 필드 개수 계산
            if 'ocr_data' in json_data and json_data['ocr_data']:
                ocr_data = json_data['ocr_data']
                if 'images' in ocr_data:
                    for image in ocr_data['images']:
                        if 'fields' in image:
                            ocr_count += len(image['fields'])
            
            # Detection 객체 개수 계산 (detection_data 또는 data에서)
            if 'detection_data' in json_data and json_data['detection_data']:
                detection_data = json_data['detection_data']
                if 'detections' in detection_data:
                    detection_count = len(detection_data['detections'])
            elif 'data' in json_data and 'boxes' in json_data['data']:
                detection_count = len(json_data['data']['boxes'])
            
            total_objects = ocr_count + detection_count
            
        except Exception as e:
            # JSON 파싱 오류 시 기본값 유지
            pass
    
    return ocr_count, detection_count, total_objects

def display_file_row(file_data):
    """개별 파일 행 표시"""
    
    # 개별 체크박스 상태 계산
    is_checked = any(
        selected['id'] == file_data['id'] for selected in st.session_state.selected_files
    )
    
    # 개별 체크박스
    col1, col2, col3, col4, col5 = st.columns([0.5, 1, 3, 2, 2])
    
    with col1:
        checkbox_key = f"checkbox_{file_data['id']}"
        checkbox_state = st.checkbox(
            f"파일 {file_data['name']} 선택",
            value=is_checked,
            key=checkbox_key,
            label_visibility="collapsed"
        )
        
        # 체크박스 상태 변경 처리
        if checkbox_state != is_checked:
            if checkbox_state:
                # 체크됨 - 전체 파일 데이터 추가
                if not any(selected['id'] == file_data['id'] for selected in st.session_state.selected_files):
                    st.session_state.selected_files.append(file_data.copy())
            else:
                # 체크 해제됨
                st.session_state.selected_files = [
                    selected for selected in st.session_state.selected_files 
                    if selected['id'] != file_data['id']
                ]
            st.rerun()
    
    with col2:
        # 이미지 표시
        try:
            if os.path.exists(file_data['image_path']):
                with open(file_data['image_path'], "rb") as image_file:
                    encoded_image = base64.b64encode(image_file.read()).decode()
                    st.image(f"data:image/png;base64,{encoded_image}", width=100)
            else:
                st.write("🖼️ 이미지 없음")
        except Exception as e:
            st.write(f"❌ 이미지 로드 실패: {str(e)}")
    
    with col3:
        # 파일 이름과 기본 정보
        st.write(f"**{file_data['name']}**")
        st.caption(f"ID: {file_data['id']}")
    
    with col4:
        # 업로드 정보
        st.write(f"**업로드자:** {file_data['user']}")
        st.caption(f"**날짜:** {file_data['create_date']}")
    
    with col5:
        # 데이터 정보
        json_data = file_data.get('json_data', {})
        if json_data:
            # OCR 통계
            ocr_count = 0
            if 'ocr_data' in json_data:
                for img in json_data['ocr_data'].get('images', []):
                    ocr_count += len(img.get('fields', []))
            
            # Detection 통계
            det_count = len(json_data.get('detection_data', {}).get('detections', []))
            
            st.write(f"**OCR:** {ocr_count}개")
            st.write(f"**Detection:** {det_count}개")
        else:
            st.write("데이터 없음")
    
    # 액션 버튼들
    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
    
    with btn_col1:
        if st.button("⚡ 빠른선택", key=f"quick_select_{file_data['id']}", use_container_width=True):
            # 기존 선택 초기화 후 이 파일만 선택 (전체 데이터 포함)
            st.session_state.selected_files = [file_data.copy()]
            st.rerun()
    
    with btn_col2:
        if st.button("💬 챗봇으로 분석", key=f"chat_{file_data['id']}", use_container_width=True):
            # 이 파일만 선택하고 챗봇으로 이동 (전체 데이터 포함)
            st.session_state['selected_files_for_chat'] = [file_data.copy()]
            st.session_state['page_view'] = 'chatbot'
            st.success(f"{file_data['name']} 파일이 챗봇으로 전송되었습니다!")
            st.rerun()
    
    with btn_col3:
        if st.button("📋 상세정보", key=f"detail_{file_data['id']}", use_container_width=True):
            show_file_detail_modal(file_data)
    
    with btn_col4:
        if st.button("🗑️ 삭제", key=f"delete_{file_data['id']}", use_container_width=True):
            if st.button("삭제 확인", key=f"confirm_delete_{file_data['id']}"):
                if delete_file(file_data['id']):
                    st.success("파일이 삭제되었습니다.")
                    st.rerun()
                else:
                    st.error("파일 삭제에 실패했습니다.")
    
    st.divider()

@st.dialog("파일 상세 정보")
def show_file_detail_modal(file_data):
    """파일 상세 정보 모달"""
    
    st.markdown(f"### 📋 {file_data['name']}")
    
    # 기본 정보
    st.markdown("#### 📄 기본 정보")
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.write(f"**파일 ID:** {file_data['id']}")
        st.write(f"**파일명:** {file_data['name']}")
        st.write(f"**등록자:** {file_data['user']}")
    
    with info_col2:
        st.write(f"**등록일:** {file_data['create_date']}")
        st.write(f"**OCR 필드:** {file_data['ocr_count']}개")
        st.write(f"**Detection 객체:** {file_data['detection_count']}개")
    
    # 이미지 미리보기
    st.markdown("#### 🖼️ 이미지 미리보기")
    try:
        if os.path.exists(file_data['image_path']):
            st.image(file_data['image_path'], use_container_width=True)
        else:
            st.image("assets/img/default_bear.png", use_container_width=True)
    except Exception:
        st.error("이미지를 로드할 수 없습니다.")
    
    # JSON 데이터 상세 보기
    if file_data.get('json_data'):
        st.markdown("#### 📊 데이터 분석")
        
        tab1, tab2 = st.tabs(["OCR 데이터", "Detection 데이터"])
        
        with tab1:
            if 'ocr_data' in file_data['json_data']:
                display_ocr_data(file_data['json_data']['ocr_data'])
            else:
                st.info("OCR 데이터가 없습니다.")
        
        with tab2:
            json_data = file_data['json_data']
            if 'detection_data' in json_data:
                display_detection_data(json_data['detection_data'])
            elif 'data' in json_data and 'boxes' in json_data['data']:
                display_detection_data({'detections': json_data['data']['boxes']})
            else:
                st.info("Detection 데이터가 없습니다.")

def display_ocr_data(ocr_data):
    """OCR 데이터 표시"""
    if 'images' in ocr_data:
        for i, image in enumerate(ocr_data['images']):
            if 'fields' in image:
                st.write(f"**이미지 {i+1} - OCR 결과 ({len(image['fields'])}개 필드)**")
                
                for j, field in enumerate(image['fields']):
                    if 'inferText' in field:
                        confidence = field.get('inferConfidence', 0)
                        st.write(f"• {field['inferText']} (신뢰도: {confidence:.3f})")

def display_detection_data(detection_data):
    """Detection 데이터 표시"""
    if 'detections' in detection_data:
        detections = detection_data['detections']
        st.write(f"**Detection 결과 ({len(detections)}개 객체)**")
        
        for i, detection in enumerate(detections):
            label = detection.get('label', detection.get('id', f'객체 {i+1}'))
            confidence = detection.get('confidence', 0)
            
            # 위치 정보
            if 'boundingBox' in detection:
                bbox = detection['boundingBox']
                pos_info = f"위치: ({bbox.get('x', 0):.1f}, {bbox.get('y', 0):.1f})"
            elif all(k in detection for k in ['x', 'y']):
                pos_info = f"위치: ({detection['x']}, {detection['y']})"
            else:
                pos_info = "위치 정보 없음"
            
            if confidence > 0:
                st.write(f"• {label} (신뢰도: {confidence:.3f}, {pos_info})")
            else:
                st.write(f"• {label} ({pos_info})")

def delete_file(file_id):
    """파일 삭제"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM domyun WHERE d_id = %s", (file_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"파일 삭제 중 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    show() 