#!/usr/bin/env python3
"""
도면 변경사항 분석 유틸리티
"""

import os
import json
from typing import Dict, Tuple, Optional
from loguru import logger
from pages.object_detection_change_detector import ObjectDetectionChangeDetector

def get_change_analysis_result(as_is_json: str, to_be_json: str, 
                             as_is_image: str, to_be_image: str,
                             output_path: str) -> Tuple[Optional[Dict], Optional[str]]:
    """변경사항 분석 결과를 반환하는 함수"""
    
    try:
        # 파일 존재 여부 확인
        for file_path in [as_is_json, to_be_json, as_is_image, to_be_image]:
            if not os.path.exists(file_path):
                return None, f"파일이 존재하지 않습니다: {file_path}"
        
        # ObjectDetectionChangeDetector 인스턴스 생성
        detector = ObjectDetectionChangeDetector()
        
        # 검출된 객체들 로드
        as_is_objects, as_is_w, as_is_h = detector.load_detected_objects(as_is_json)
        to_be_objects, to_be_w, to_be_h = detector.load_detected_objects(to_be_json)
        
        if not as_is_objects or not to_be_objects:
            return None, "객체 로드 실패"
        
        # 변경사항 검출
        changes = detector.detect_changes(as_is_objects, as_is_w, as_is_h, 
                                        to_be_objects, to_be_w, to_be_h)
        
        # 이미지 로드 및 비교 이미지 생성
        from PIL import Image
        as_is_img = Image.open(as_is_image)
        to_be_img = Image.open(to_be_image)
        
        # 비교 이미지 생성
        comparison_image = detector.create_side_by_side_comparison(as_is_img, to_be_img, changes)
        
        # 저장
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        comparison_image.save(output_path, quality=98, optimize=True)
        
        # 변경사항 요약 생성
        added_count = len([c for c in changes if c.change_type == 'added'])
        removed_count = len([c for c in changes if c.change_type == 'removed'])
        matched_count = len(as_is_objects) - removed_count
        
        # 결과 반환
        return {
            "comparison_image_path": output_path,
            "total_changes": len(changes),
            "added_objects": added_count,
            "removed_objects": removed_count,
            "matched_objects": matched_count,
            "changes_detail": changes,
            "as_is_total": len(as_is_objects),
            "to_be_total": len(to_be_objects)
        }, None
        
    except Exception as e:
        logger.error(f"변경사항 분석 실패: {str(e)}")
        return None, str(e) 