import os
import json
import base64
import requests
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# Naver OCR API 설정
NAVER_OCR_API_URL = os.getenv('NAVER_OCR_API_URL')
NAVER_OCR_SECRET_KEY = os.getenv('NAVER_OCR_SECRET_KEY')

def encode_image_to_base64(image_path):
    """이미지 파일을 base64로 인코딩"""
    try:
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"이미지 인코딩 오류: {e}")
        return None

def call_naver_ocr_api(image_path):
    """
    Naver OCR API 호출
    
    Args:
        image_path: 분석할 이미지 파일 경로
    
    Returns:
        tuple: (success, ocr_result, error_message)
    """
    
    # API 키 확인
    if not NAVER_OCR_API_URL or not NAVER_OCR_SECRET_KEY:
        return False, None, "Naver OCR API 설정이 없습니다. .env 파일을 확인하세요."
    
    # 이미지 파일 존재 확인
    if not os.path.exists(image_path):
        return False, None, f"이미지 파일이 존재하지 않습니다: {image_path}"
    
    try:
        # 이미지를 base64로 인코딩
        image_base64 = encode_image_to_base64(image_path)
        if not image_base64:
            return False, None, "이미지 인코딩에 실패했습니다."
        
        # API 요청 데이터 구성
        request_json = {
            'images': [
                {
                    'format': 'png',
                    'name': 'demo',
                    'data': image_base64
                }
            ],
            'requestId': str(os.path.basename(image_path)),
            'version': 'V2',
            'timestamp': str(int(1000))
        }
        
        # API 요청 헤더
        headers = {
            'X-OCR-SECRET': NAVER_OCR_SECRET_KEY,
            'Content-Type': 'application/json'
        }
        
        # API 호출
        response = requests.post(
            NAVER_OCR_API_URL,
            headers=headers,
            data=json.dumps(request_json),
            timeout=30
        )
        
        # 응답 처리
        if response.status_code == 200:
            ocr_result = response.json()
            return True, ocr_result, None
        else:
            error_msg = f"OCR API 호출 실패: {response.status_code} - {response.text}"
            return False, None, error_msg
            
    except requests.exceptions.Timeout:
        return False, None, "OCR API 요청 시간이 초과되었습니다."
    except requests.exceptions.ConnectionError:
        return False, None, "OCR API 서버에 연결할 수 없습니다."
    except Exception as e:
        return False, None, f"OCR API 호출 중 오류 발생: {str(e)}"

def save_ocr_result_to_json(ocr_result, image_path):
    """
    OCR 결과를 JSON 파일로 저장 (label: "ocr" 추가, 동일 파일명 시 덮어쓰기)
    
    Args:
        ocr_result: OCR API 응답 결과
        image_path: 원본 이미지 파일 경로
    
    Returns:
        tuple: (success, json_file_path, error_message)
    """
    try:
        # OCR 결과 저장 디렉토리 생성
        ocr_dir = 'uploads/ocr_results'
        if not os.path.exists(ocr_dir):
            os.makedirs(ocr_dir)
        
        # JSON 파일 경로 생성 (uploads/ocr_results/이미지파일명.json)
        image_filename = os.path.basename(image_path)
        base_name = os.path.splitext(image_filename)[0]
        json_file_path = os.path.join(ocr_dir, f"{base_name}.json")
        
        # 기존 파일이 있으면 업데이트 표시
        if os.path.exists(json_file_path):
            print(f"🔄 기존 OCR 결과 업데이트: {base_name}.json")
        
        # 기존 OCR 결과에 label 추가
        enhanced_ocr_result = {
            "label": "ocr",
            **ocr_result  # 기존 OCR 결과의 모든 데이터를 그대로 유지
        }
        
        # JSON 파일로 저장 (덮어쓰기)
        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(enhanced_ocr_result, json_file, ensure_ascii=False, indent=2)
        
        return True, json_file_path, None
        
    except Exception as e:
        return False, None, f"JSON 파일 저장 중 오류: {str(e)}"

def extract_text_from_ocr_result(ocr_result):
    """
    OCR 결과에서 텍스트만 추출
    
    Args:
        ocr_result: OCR API 응답 결과
    
    Returns:
        str: 추출된 텍스트
    """
    try:
        extracted_text = []
        
        if 'images' in ocr_result:
            for image in ocr_result['images']:
                if 'fields' in image:
                    for field in image['fields']:
                        if 'inferText' in field:
                            extracted_text.append(field['inferText'])
        
        return '\n'.join(extracted_text)
        
    except Exception as e:
        print(f"텍스트 추출 오류: {e}")
        return ""

def process_image_with_ocr(image_path):
    """
    이미지 파일에 대해 OCR 처리를 수행하고 결과를 저장
    
    Args:
        image_path: 처리할 이미지 파일 경로
    
    Returns:
        dict: 처리 결과 정보
    """
    result = {
        'success': False,
        'image_path': image_path,
        'json_path': None,
        'extracted_text': '',
        'error_message': None
    }
    
    # OCR API 호출
    success, ocr_result, error_msg = call_naver_ocr_api(image_path)
    
    if not success:
        result['error_message'] = error_msg
        return result
    
    # JSON 파일로 저장
    success, json_path, error_msg = save_ocr_result_to_json(ocr_result, image_path)
    
    if not success:
        result['error_message'] = error_msg
        return result
    
    # 텍스트 추출
    extracted_text = extract_text_from_ocr_result(ocr_result)
    
    result.update({
        'success': True,
        'json_path': json_path,
        'extracted_text': extracted_text
    })
    
    return result 