#!/usr/bin/env python3
"""
자동 파일 처리 유틸리티
업로드된 파일을 OCR 처리하고 통합 JSON으로 변환한 후 데이터베이스에 저장
"""

import os
import json
import uuid
import re
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from PIL import Image
from pdf2image import convert_from_bytes
from io import BytesIO

from utils.naver_ocr import process_image_with_ocr
from services.merge_json import merge_ocr_and_detection_results
from config.database_config import get_db_connection
from config.user_config import USER_NAME

def clean_filename(filename: str) -> str:
    """
    파일명을 정리하는 함수
    - 확장자 제거 (.pdf, .png 등)
    - 끝에 있는 숫자 제거 (예: stream_does_ai_1 -> stream_does_ai, 도면예시1 -> 도면예시)
    
    Args:
        filename: 원본 파일명
    
    Returns:
        str: 정리된 파일명
    """
    # 확장자 제거
    base_name = os.path.splitext(filename)[0]
    
    # 끝에 있는 숫자 제거 (언더스코어 유무 관계없이)
    # 패턴: _숫자 또는 그냥 숫자
    cleaned_name = re.sub(r'_?\d+$', '', base_name)
    
    return cleaned_name

def get_next_testsum_sequence() -> int:
    """다음 testsum 시퀀스 번호를 반환"""
    merged_dir = 'uploads/merged_results'
    if not os.path.exists(merged_dir):
        return 1
    
    existing_files = [f for f in os.listdir(merged_dir) if f.startswith('testsum') and f.endswith('.json')]
    if not existing_files:
        return 1
    
    # 시퀀스 번호 추출하여 최대값 + 1 반환
    sequences = []
    for filename in existing_files:
        try:
            seq_str = filename.replace('testsum', '').replace('.json', '')
            sequences.append(int(seq_str))
        except ValueError:
            continue
    
    return max(sequences) + 1 if sequences else 1

def extract_image_dimensions(image_path: str) -> Tuple[int, int]:
    """이미지에서 width, height 추출"""
    try:
        with Image.open(image_path) as img:
            return img.size  # (width, height)
    except Exception as e:
        print(f"이미지 크기 추출 오류: {e}")
        return 1684, 1190  # 기본값

def convert_uploaded_file_to_images(file_bytes: bytes, original_filename: str) -> Dict[str, Any]:
    """업로드된 파일을 PNG 이미지로 변환 (동일 파일명 시 덮어쓰기)"""
    
    result = {
        'success': False,
        'converted_images': [],
        'error_message': None,
        'updated_files': []
    }
    
    try:
        # 업로드 디렉토리 생성
        upload_dir = 'uploads/uploaded_images'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        file_extension = original_filename.lower().split('.')[-1]
        # 파일명에서 확장자만 제거 (숫자나 _ 제거하지 않음)
        base_filename = os.path.splitext(original_filename)[0]
        
        if file_extension == 'pdf':
            # PDF 처리
            try:
                images = convert_from_bytes(file_bytes, dpi=300)
                for i, image in enumerate(images):
                    if len(images) > 1:
                        filename = f"{base_filename}_page_{i+1}.png"
                    else:
                        filename = f"{base_filename}.png"
                    
                    save_path = os.path.join(upload_dir, filename)
                    
                    # 기존 파일이 있으면 업데이트 표시
                    if os.path.exists(save_path):
                        result['updated_files'].append(save_path)
                        print(f"🔄 기존 파일 업데이트: {filename}")
                    
                    image.save(save_path, 'PNG')
                    result['converted_images'].append(save_path)
                
                result['success'] = True
                
            except Exception as e:
                result['error_message'] = f"PDF 변환 오류: {str(e)}"
                
        else:
            # 이미지 파일 처리
            try:
                image = Image.open(BytesIO(file_bytes))
                
                # RGB로 변환
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                filename = f"{base_filename}.png"
                save_path = os.path.join(upload_dir, filename)
                
                # 기존 파일이 있으면 업데이트 표시
                if os.path.exists(save_path):
                    result['updated_files'].append(save_path)
                    print(f"🔄 기존 파일 업데이트: {filename}")
                
                image.save(save_path, 'PNG')
                result['converted_images'].append(save_path)
                result['success'] = True
                
            except Exception as e:
                result['error_message'] = f"이미지 변환 오류: {str(e)}"
    
    except Exception as e:
        result['error_message'] = f"파일 처리 오류: {str(e)}"
    
    return result

def create_integrated_json(image_path: str, ocr_result: Dict, original_filename: str) -> Dict[str, Any]:
    """OCR과 Detection 결과를 통합하여 testsum{seq}.json 생성 (파일명 매핑 방식)"""
    
    result = {
        'success': False,
        'merged_path': None,
        'error_message': None,
        'sequence': None
    }
    
    try:
        # 파일명에서 확장자만 제거 (숫자나 _ 제거하지 않음)
        base_filename = os.path.splitext(original_filename)[0]
        
        # Detection 결과 파일들을 파일명으로 매핑하여 로드
        detection_dir = 'uploads/detection_results'
        detection_data = None
        matched_detection_files = []
        
        if os.path.exists(detection_dir):
            # detection_results 폴더의 모든 JSON 파일 확인
            for detection_file in os.listdir(detection_dir):
                if detection_file.endswith('.json'):
                    detection_base = os.path.splitext(detection_file)[0]
                    
                    # 파일명이 일치하는 경우 (대소문자 무시, 확장자만 제거해서 비교)
                    if detection_base.lower() == base_filename.lower():
                        detection_path = os.path.join(detection_dir, detection_file)
                        try:
                            with open(detection_path, 'r', encoding='utf-8') as f:
                                file_detection_data = json.load(f)
                            matched_detection_files.append({
                                'filename': detection_file,
                                'data': file_detection_data
                            })
                        except Exception as e:
                            print(f"Detection 파일 로드 오류 ({detection_file}): {e}")
        
        # 매칭된 detection 파일들을 하나로 통합
        if matched_detection_files:
            if len(matched_detection_files) == 1:
                detection_data = matched_detection_files[0]['data']
            else:
                # 여러 detection 파일이 있는 경우 통합
                detection_data = {
                    "merged_detections": True,
                    "source_files": [f['filename'] for f in matched_detection_files],
                    "detections": []
                }
                for detection_file in matched_detection_files:
                    if 'detections' in detection_file['data']:
                        detection_data['detections'].extend(detection_file['data']['detections'])
                    # 다른 필드들도 병합
                    for key, value in detection_file['data'].items():
                        if key not in detection_data and key != 'detections':
                            detection_data[key] = value
        else:
            print(f"경고: '{base_filename}'과 매칭되는 detection 파일을 찾을 수 없습니다.")
        
        # 이미지 크기 정보 추출
        width, height = extract_image_dimensions(image_path)
        
        # Detection 데이터에서 크기 정보 업데이트 (있는 경우)
        if detection_data and 'image_info' in detection_data:
            width = detection_data['image_info'].get('width', width)
            height = detection_data['image_info'].get('height', height)
        
        # OCR 데이터에서 크기 정보 추출 시도
        if ocr_result and 'images' in ocr_result:
            for img_data in ocr_result['images']:
                if 'width' in img_data and 'height' in img_data:
                    width = img_data['width']
                    height = img_data['height']
                    break
        
        # 시퀀스 번호 생성
        sequence = get_next_testsum_sequence()
        
        # 저장할 파일명은 base_filename 사용 (확장자만 제거)
        clean_filename_for_save = base_filename
        
        # 통합 JSON 구조 생성 (중첩 구조)
        integrated_data = {}
        
        # 1. OCR 데이터를 "ocr" 객체 안에 배치
        if ocr_result:
            integrated_data["ocr"] = {
                "label": "ocr",
                **ocr_result
            }
        
        # 2. Detection 데이터를 "detecting" 객체 안에 배치
        if detection_data:
            integrated_data["detecting"] = detection_data
        
        # 3. 메타데이터는 최상위 레벨에 추가
        integrated_data.update({
            "source_filename": original_filename,
            "base_filename": base_filename,
            "clean_filename_for_save": clean_filename_for_save,
            "created_at": datetime.now().isoformat(),
            "width": width,
            "height": height,
            "file_mapping": {
                "matched_detection_files": len(matched_detection_files),
                "detection_sources": [f['filename'] for f in matched_detection_files] if matched_detection_files else []
            }
        })
        
        # merged_results 디렉토리 생성
        merged_dir = 'uploads/merged_results'
        if not os.path.exists(merged_dir):
            os.makedirs(merged_dir)
        
        # clean_filename_for_save를 사용하여 파일명 생성 (_merged 없이)
        merged_filename = f"{clean_filename_for_save}.json"
        merged_path = os.path.join(merged_dir, merged_filename)
        
        # 기존 파일이 있으면 업데이트 표시
        if os.path.exists(merged_path):
            print(f"🔄 기존 통합 JSON 업데이트: {merged_filename}")
        
        with open(merged_path, 'w', encoding='utf-8') as f:
            json.dump(integrated_data, f, ensure_ascii=False, indent=2)
        
        result.update({
            'success': True,
            'merged_path': merged_path,
            'sequence': sequence,
            'integrated_data': integrated_data
        })
        
    except Exception as e:
        result['error_message'] = f"통합 JSON 생성 오류: {str(e)}"
    
    return result

def save_to_database(integrated_data: Dict, image_path: str, original_filename: str) -> Dict[str, Any]:
    """통합 데이터를 PostgreSQL 데이터베이스에 저장 (동일 파일명 시 업데이트)"""
    
    result = {
        'success': False,
        'db_id': None,
        'error_message': None,
        'is_update': False
    }
    
    try:
        conn = get_db_connection()
        if not conn:
            result['error_message'] = "데이터베이스 연결 실패"
            return result
        
        cursor = conn.cursor()
        
        # 데이터베이스에 저장할 때는 확장자와 뒤의 숫자들을 제거한 파일명 사용
        base_filename = os.path.splitext(original_filename)[0]
        # 파일명 뒤의 _숫자, 숫자 패턴 제거 (예: stream_dose_ai_1 -> stream_dose_ai, 도면예시1 -> 도면예시)
        base_filename = clean_filename(base_filename)
        
        # 기존 레코드 확인
        check_query = """
        SELECT d_id FROM domyun WHERE d_name = %s AND "user" = %s;
        """
        cursor.execute(check_query, (base_filename, USER_NAME))
        existing_record = cursor.fetchone()
        
        if existing_record:
            # 기존 레코드 업데이트
            update_query = """
            UPDATE domyun 
            SET create_date = %s, json_data = %s, image_path = %s
            WHERE d_id = %s
            RETURNING d_id;
            """
            cursor.execute(update_query, (
                datetime.now(),
                json.dumps(integrated_data, ensure_ascii=False),
                image_path,
                existing_record[0]
            ))
            db_id = cursor.fetchone()[0]
            result['is_update'] = True
            print(f"🔄 기존 데이터베이스 레코드 업데이트: ID {db_id}")
        else:
            # 새 레코드 삽입
            insert_query = """
            INSERT INTO domyun (d_name, "user", create_date, json_data, image_path)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING d_id;
            """
            cursor.execute(insert_query, (
                base_filename,
                USER_NAME,
                datetime.now(),
                json.dumps(integrated_data, ensure_ascii=False),
                image_path
            ))
            db_id = cursor.fetchone()[0]
            print(f"✅ 새 데이터베이스 레코드 생성: ID {db_id}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        result.update({
            'success': True,
            'db_id': db_id
        })
        
    except Exception as e:
        result['error_message'] = f"데이터베이스 저장 오류: {str(e)}"
        if 'conn' in locals():
            conn.rollback()
            conn.close()
    
    return result

def process_uploaded_file_auto(file_bytes: bytes, original_filename: str) -> Dict[str, Any]:
    """완전 자동화된 파일 처리 워크플로우"""
    
    workflow_result = {
        'success': False,
        'steps_completed': [],
        'total_steps': 6,
        'results': {},
        'error_message': None,
        'rollback_info': []
    }
    
    try:
        # 1단계: 이미지 변환
        workflow_result['steps_completed'].append("🔄 파일 변환 시작")
        convert_result = convert_uploaded_file_to_images(file_bytes, original_filename)
        
        if not convert_result['success']:
            workflow_result['error_message'] = convert_result['error_message']
            return workflow_result
        
        workflow_result['steps_completed'].append("✅ 이미지 변환 완료")
        workflow_result['results']['converted_images'] = convert_result['converted_images']
        
        # 각 변환된 이미지에 대해 처리
        processed_results = []
        
        for image_path in convert_result['converted_images']:
            image_result = {
                'image_path': image_path,
                'ocr_result': None,
                'integrated_result': None,
                'db_result': None
            }
            
            # 2단계: OCR 처리
            workflow_result['steps_completed'].append(f"🔍 OCR 처리 중: {os.path.basename(image_path)}")
            ocr_result = process_image_with_ocr(image_path)
            
            if ocr_result['success']:
                workflow_result['steps_completed'].append(f"✅ OCR 완료: {os.path.basename(image_path)}")
                image_result['ocr_result'] = ocr_result
                
                # OCR 데이터 로드
                if ocr_result['json_path'] and os.path.exists(ocr_result['json_path']):
                    with open(ocr_result['json_path'], 'r', encoding='utf-8') as f:
                        ocr_data = json.load(f)
                else:
                    ocr_data = None
                
                # 3단계: 통합 JSON 생성
                workflow_result['steps_completed'].append(f"📊 통합 JSON 생성 중: {os.path.basename(image_path)}")
                integrated_result = create_integrated_json(image_path, ocr_data, original_filename)
                
                if integrated_result['success']:
                    workflow_result['steps_completed'].append(f"✅ 통합 JSON 완료: testsum{integrated_result['sequence']}.json")
                    image_result['integrated_result'] = integrated_result
                    
                    # 4단계: 데이터베이스 저장
                    workflow_result['steps_completed'].append(f"💾 데이터베이스 저장 중")
                    db_result = save_to_database(
                        integrated_result['integrated_data'], 
                        image_path, 
                        original_filename
                    )
                    
                    if db_result['success']:
                        workflow_result['steps_completed'].append(f"✅ DB 저장 완료: ID {db_result['db_id']}")
                        image_result['db_result'] = db_result
                    else:
                        workflow_result['steps_completed'].append(f"❌ DB 저장 실패: {db_result['error_message']}")
                        image_result['db_result'] = db_result
                else:
                    workflow_result['steps_completed'].append(f"❌ 통합 JSON 실패: {integrated_result['error_message']}")
                    image_result['integrated_result'] = integrated_result
            else:
                workflow_result['steps_completed'].append(f"❌ OCR 실패: {ocr_result['error_message']}")
                image_result['ocr_result'] = ocr_result
            
            processed_results.append(image_result)
        
        workflow_result['results']['processed_images'] = processed_results
        workflow_result['success'] = True
        workflow_result['steps_completed'].append("🎉 모든 처리 완료!")
        
    except Exception as e:
        workflow_result['error_message'] = f"워크플로우 오류: {str(e)}"
        workflow_result['steps_completed'].append(f"❌ 처리 중단: {str(e)}")
    
    return workflow_result

def get_processing_statistics() -> Dict[str, Any]:
    """처리 통계 정보 반환"""
    
    stats = {
        'total_files': 0,
        'today_files': 0,
        'total_merged': 0,
        'total_images': 0,
        'success_rate': 0.0
    }
    
    try:
        # 업로드된 이미지 수
        images_dir = 'uploads/uploaded_images'
        if os.path.exists(images_dir):
            stats['total_images'] = len([f for f in os.listdir(images_dir) if f.endswith('.png')])
        
        # 병합된 결과 수
        merged_dir = 'uploads/merged_results'
        if os.path.exists(merged_dir):
            merged_files = [f for f in os.listdir(merged_dir) if f.startswith('testsum')]
            stats['total_merged'] = len(merged_files)
            
            # 오늘 생성된 파일 수
            today = datetime.now().date()
            today_count = 0
            
            for filename in merged_files:
                filepath = os.path.join(merged_dir, filename)
                file_date = datetime.fromtimestamp(os.path.getctime(filepath)).date()
                if file_date == today:
                    today_count += 1
            
            stats['today_files'] = today_count
        
        # 성공률 계산
        if stats['total_images'] > 0:
            stats['success_rate'] = (stats['total_merged'] / stats['total_images']) * 100
        
        stats['total_files'] = stats['total_images']
        
    except Exception as e:
        print(f"통계 계산 오류: {e}")
    
    return stats 