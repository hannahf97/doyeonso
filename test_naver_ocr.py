#!/usr/bin/env python3
"""
Naver OCR API 연결 테스트 스크립트
"""

import os
from dotenv import load_dotenv
from utils.naver_ocr import call_naver_ocr_api, process_image_with_ocr

def test_naver_ocr_config():
    """Naver OCR 설정 테스트"""
    print("🔍 Naver OCR 설정 검사 중...")
    
    # 환경변수 로드
    load_dotenv()
    
    # 환경변수 확인
    api_url = os.getenv('NAVER_OCR_API_URL')
    secret_key = os.getenv('NAVER_OCR_SECRET_KEY')
    
    print(f"API URL: {api_url}")
    print(f"Secret Key: {'설정됨' if secret_key else '설정되지 않음'}")
    
    if not api_url or not secret_key:
        print("❌ Naver OCR API 설정이 누락되었습니다!")
        print("💡 .env 파일에 다음 설정을 추가하세요:")
        print("NAVER_OCR_API_URL=https://naveropenapi.apigw.ntruss.com/vision/v1/ocr")
        print("NAVER_OCR_SECRET_KEY=여기에_실제_시크릿키_입력")
        return False
    
    print("✅ Naver OCR 설정이 완료되었습니다!")
    return True

def test_with_sample_image():
    """샘플 이미지로 OCR 테스트"""
    
    # 테스트용 이미지 경로들
    test_images = [
        "uploads/uploaded_images",
        "data",
        "assets/img"
    ]
    
    sample_image = None
    
    # 테스트 이미지 찾기
    for img_dir in test_images:
        if os.path.exists(img_dir):
            for file in os.listdir(img_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    sample_image = os.path.join(img_dir, file)
                    break
            if sample_image:
                break
    
    if not sample_image:
        print("⚠️ 테스트할 이미지 파일을 찾을 수 없습니다.")
        print("💡 uploads/uploaded_images/ 폴더에 이미지 파일을 넣고 다시 시도하세요.")
        return False
    
    print(f"🖼️ 테스트 이미지: {sample_image}")
    
    # OCR 처리 테스트
    print("🔍 OCR 처리 중...")
    success, ocr_result, error_msg = call_naver_ocr_api(sample_image)
    
    if success:
        print("✅ OCR 처리 성공!")
        
        # 텍스트 추출
        extracted_text = ""
        if 'images' in ocr_result:
            for image in ocr_result['images']:
                if 'fields' in image:
                    for field in image['fields']:
                        if 'inferText' in field:
                            extracted_text += field['inferText'] + "\n"
        
        print(f"📝 추출된 텍스트:")
        print(extracted_text or "텍스트가 없습니다.")
        
        return True
    else:
        print(f"❌ OCR 처리 실패: {error_msg}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 Naver OCR 연결 테스트 시작")
    print("=" * 50)
    
    # 1. 설정 확인
    if not test_naver_ocr_config():
        return
    
    print("\n" + "=" * 50)
    
    # 2. 실제 API 테스트
    test_with_sample_image()
    
    print("\n🎉 테스트 완료!")

if __name__ == "__main__":
    main() 