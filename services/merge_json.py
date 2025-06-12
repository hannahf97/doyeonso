#!/usr/bin/env python3
"""
OCR과 Detection 결과를 병합하는 모듈
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

def merge_ocr_and_detection_results(
    ocr_data: Optional[Dict[str, Any]], 
    detection_data: Optional[Dict[str, Any]], 
    image_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    OCR 데이터와 Detection 데이터를 병합하여 통합 결과 반환
    
    Args:
        ocr_data: OCR 처리 결과 데이터
        detection_data: Detection 처리 결과 데이터
        image_info: 이미지 정보 (width, height 등)
    
    Returns:
        Dict: 병합된 통합 데이터
    """
    
    # 기본 구조 생성
    merged_result = {
        "merged_at": datetime.now().isoformat(),
        "data_sources": [],
        "image_info": image_info or {},
        "ocr_data": None,
        "detection_data": None,
        "merged_annotations": []
    }
    
    # OCR 데이터 처리
    if ocr_data:
        merged_result["ocr_data"] = {
            "label": "ocr",
            "timestamp": datetime.now().isoformat(),
            **ocr_data
        }
        merged_result["data_sources"].append("ocr")
        
        # OCR 텍스트 영역을 annotations에 추가
        if "images" in ocr_data:
            for img_data in ocr_data["images"]:
                if "fields" in img_data:
                    for field in img_data["fields"]:
                        if "boundingPoly" in field:
                            annotation = {
                                "type": "text",
                                "source": "ocr",
                                "text": field.get("inferText", ""),
                                "confidence": field.get("inferConfidence", 0),
                                "bounding_poly": field["boundingPoly"]
                            }
                            merged_result["merged_annotations"].append(annotation)
    
    # Detection 데이터 처리
    if detection_data:
        merged_result["detection_data"] = {
            "label": "detection",
            "timestamp": datetime.now().isoformat(),
            **detection_data
        }
        merged_result["data_sources"].append("detection")
        
        # Detection 객체를 annotations에 추가
        if "detections" in detection_data:
            for detection in detection_data["detections"]:
                annotation = {
                    "type": "object",
                    "source": "detection",
                    "class": detection.get("class", "unknown"),
                    "confidence": detection.get("confidence", 0),
                    "bbox": detection.get("bbox", [])
                }
                merged_result["merged_annotations"].append(annotation)
    
    # 이미지 정보 업데이트
    if not merged_result["image_info"]:
        # OCR 데이터에서 이미지 정보 추출 시도
        if ocr_data and "images" in ocr_data:
            for img_data in ocr_data["images"]:
                if "width" in img_data and "height" in img_data:
                    merged_result["image_info"] = {
                        "width": img_data["width"],
                        "height": img_data["height"]
                    }
                    break
        
        # Detection 데이터에서 이미지 정보 추출 시도
        if detection_data and "image_info" in detection_data:
            merged_result["image_info"].update(detection_data["image_info"])
    
    # 통계 정보 추가
    merged_result["statistics"] = {
        "total_annotations": len(merged_result["merged_annotations"]),
        "ocr_texts": len([a for a in merged_result["merged_annotations"] if a["type"] == "text"]),
        "detected_objects": len([a for a in merged_result["merged_annotations"] if a["type"] == "object"]),
        "data_sources_count": len(merged_result["data_sources"])
    }
    
    return merged_result

def save_merged_result(merged_data: Dict[str, Any], output_path: str) -> bool:
    """
    병합된 결과를 JSON 파일로 저장
    
    Args:
        merged_data: 병합된 데이터
        output_path: 저장할 파일 경로
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"병합 결과 저장 오류: {e}")
        return False

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    JSON 파일을 로드하여 딕셔너리로 반환
    
    Args:
        file_path: 로드할 JSON 파일 경로
    
    Returns:
        Dict 또는 None: 로드된 데이터 또는 실패시 None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"JSON 파일 로드 오류 ({file_path}): {e}")
        return None 