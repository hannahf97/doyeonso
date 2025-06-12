import psycopg2
import json
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter

load_dotenv()

class DatabaseService:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'doyeonso'), 
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password'),
            'port': os.getenv('DB_PORT', '5432')
        }

    def get_connection(self):
        """데이터베이스 연결 생성"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            print(f"Database connection error: {e}")
            return None

    def get_all_domyun_files(self) -> List[Dict[str, Any]]:
        """모든 도면 파일 정보 조회"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d_id, d_name, user, create_date, json_data, image_path 
                FROM domyun 
                ORDER BY create_date DESC
            """)
            
            results = []
            for row in cursor.fetchall():
                d_id, d_name, user, create_date, json_data, image_path = row
                results.append({
                    'd_id': d_id,
                    'd_name': d_name,
                    'user': user,
                    'create_date': create_date,
                    'json_data': json_data,
                    'image_path': image_path
                })
            
            return results
            
        except Exception as e:
            print(f"Error fetching domyun files: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def analyze_domyun_data(self, domyun_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """도면 데이터 분석 및 통계 생성"""
        if not domyun_files:
            return {
                'total_files': 0,
                'ocr_items': [],
                'detection_items': [],
                'combined_items': []
            }
        
        ocr_items = []
        detection_items = []
        all_items = defaultdict(int)
        
        for file_data in domyun_files:
            json_data = file_data.get('json_data', {})
            
            # OCR 데이터 분석
            if 'ocr' in json_data and json_data['ocr']:
                ocr_data = json_data['ocr']
                if isinstance(ocr_data, dict) and 'images' in ocr_data:
                    images = ocr_data['images']
                    if isinstance(images, list) and len(images) > 0:
                        first_image = images[0]
                        if 'fields' in first_image and isinstance(first_image['fields'], list):
                            for field in first_image['fields']:
                                if isinstance(field, dict) and 'inferText' in field:
                                    item_text = str(field['inferText']).strip()
                                    if item_text and item_text != 'null' and len(item_text) > 1:
                                        # 숫자나 특수문자만 있는 경우 제외
                                        if not item_text.isdigit() and len(item_text) > 2:
                                            ocr_items.append({
                                                'file_name': file_data['d_name'],
                                                'field': 'inferText',
                                                'text': item_text
                                            })
                                            all_items[item_text] += 1
            
            # Detection 데이터 분석
            if 'detecting' in json_data and json_data['detecting']:
                detection_data = json_data['detecting']
                if isinstance(detection_data, dict) and 'data' in detection_data:
                    data = detection_data['data']
                    if isinstance(data, dict) and 'boxes' in data:
                        boxes = data['boxes']
                        if isinstance(boxes, list):
                            for box in boxes:
                                if isinstance(box, dict) and 'label' in box:
                                    class_name = str(box['label']).strip()
                                    if class_name:
                                        detection_items.append({
                                            'file_name': file_data['d_name'],
                                            'class_name': class_name,
                                            'confidence': box.get('confidence', 'N/A')
                                        })
                                        all_items[class_name] += 1
        
        # 가장 많이 발견된 아이템들로 통합 리스트 생성
        item_counter = Counter(all_items)
        combined_items = [
            {
                'item_name': item,
                'quantity': count,
                'sources': []  # OCR 또는 Detection에서 온 것인지
            }
            for item, count in item_counter.most_common(20)  # 상위 20개
        ]
        
        # 각 아이템의 소스 정보 추가
        for item in combined_items:
            item_name = item['item_name']
            sources = set()
            
            # OCR에서 발견되었는지 확인
            if any(ocr['text'] == item_name for ocr in ocr_items):
                sources.add('OCR')
            
            # Detection에서 발견되었는지 확인  
            if any(det['class_name'] == item_name for det in detection_items):
                sources.add('Detection')
            
            item['sources'] = list(sources)
        
        return {
            'total_files': len(domyun_files),
            'ocr_items': ocr_items,
            'detection_items': detection_items,
            'combined_items': combined_items
        }

    def get_file_names(self) -> List[str]:
        """데이터베이스에 저장된 파일명 리스트 반환"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT d_name FROM domyun ORDER BY create_date DESC")
            
            file_names = [row[0] for row in cursor.fetchall()]
            return file_names
            
        except Exception as e:
            print(f"Error fetching file names: {e}")
            return []
        finally:
            if conn:
                conn.close()

# 전역 인스턴스
db_service = DatabaseService() 