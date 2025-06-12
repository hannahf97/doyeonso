import os
import uuid
from PIL import Image
from pdf2image import convert_from_bytes
import streamlit as st
from dotenv import load_dotenv
from io import BytesIO

# 환경변수 로드
load_dotenv()

# 설정값들
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 10485760))  # 10MB
ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,pdf,bmp,tiff').split(',')
UPLOAD_DIR = 'uploads/uploaded_images'

def create_upload_directory():
    """업로드 디렉토리 생성"""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

def is_allowed_file(filename):
    """허용된 파일 확장자인지 확인"""
    if not filename:
        return False
    
    extension = filename.lower().split('.')[-1]
    return extension in [ext.strip().lower() for ext in ALLOWED_EXTENSIONS]

def generate_unique_filename(original_filename):
    """고유한 파일명 생성 (충돌 방지)"""
    file_extension = original_filename.lower().split('.')[-1]
    unique_id = str(uuid.uuid4())[:8]
    return f"{unique_id}_{original_filename.replace(' ', '_')}"

def convert_to_png(file_bytes, original_filename):
    """
    업로드된 파일을 PNG로 변환
    
    Args:
        file_bytes: 업로드된 파일의 바이트 데이터
        original_filename: 원본 파일명
    
    Returns:
        tuple: (success, converted_images_paths, error_message)
    """
    try:
        create_upload_directory()
        
        file_extension = original_filename.lower().split('.')[-1]
        converted_paths = []
        
        if file_extension == 'pdf':
            # PDF를 이미지로 변환
            try:
                images = convert_from_bytes(file_bytes)
                for i, image in enumerate(images):
                    # 각 페이지별로 고유 파일명 생성
                    base_filename = original_filename.replace('.pdf', '').replace('.PDF', '')
                    unique_filename = f"{str(uuid.uuid4())[:8]}_{base_filename}_page_{i+1}.png"
                    save_path = os.path.join(UPLOAD_DIR, unique_filename)
                    
                    # PNG로 저장
                    image.save(save_path, 'PNG')
                    converted_paths.append(save_path)
                    
                return True, converted_paths, None
                
            except Exception as e:
                return False, [], f"PDF 변환 중 오류: {str(e)}"
                
        else:
            # 이미지 파일 처리
            try:
                image = Image.open(BytesIO(file_bytes))
                
                # RGB로 변환 (PNG 호환성을 위해)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # 고유 파일명 생성
                unique_filename = generate_unique_filename(original_filename.replace(f'.{file_extension}', '.png'))
                save_path = os.path.join(UPLOAD_DIR, unique_filename)
                
                # PNG로 저장
                image.save(save_path, 'PNG')
                converted_paths.append(save_path)
                
                return True, converted_paths, None
                
            except Exception as e:
                return False, [], f"이미지 변환 중 오류: {str(e)}"
                
    except Exception as e:
        return False, [], f"파일 처리 중 오류: {str(e)}"

def validate_file_size(file_bytes):
    """파일 크기 검증"""
    file_size = len(file_bytes)
    if file_size > MAX_FILE_SIZE:
        max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
        current_size_mb = file_size / (1024 * 1024)
        return False, f"파일 크기가 너무 큽니다. 최대 {max_size_mb:.1f}MB, 현재 {current_size_mb:.1f}MB"
    return True, None

def get_file_info(uploaded_file):
    """업로드된 파일 정보 반환"""
    if uploaded_file is None:
        return None
    
    return {
        'name': uploaded_file.name,
        'size': uploaded_file.size,
        'type': uploaded_file.type,
        'size_mb': round(uploaded_file.size / (1024 * 1024), 2)
    } 