import os
import json
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Optional, Tuple
from loguru import logger

class ObjectDetectionChangeDetector:
    def __init__(self):
        """객체 감지 변경 분석기 초기화"""
        self.tolerance = 30  # 위치 변경 허용 범위 (픽셀)
    
    def load_json_file(self, file_path: str) -> Optional[Dict]:
        """JSON 파일 로드"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"파일이 존재하지 않습니다: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"JSON 파일 로드 실패: {str(e)}")
            return None
    
    def compare_json_files(self, as_is_path: str, to_be_path: str) -> Dict:
        """두 JSON 파일 비교"""
        try:
            # JSON 파일 로드
            as_is_data = self.load_json_file(as_is_path)
            to_be_data = self.load_json_file(to_be_path)
            
            if not as_is_data or not to_be_data:
                return {
                    'error': 'JSON 파일 로드 실패',
                    'removed_labels': [],
                    'added_labels': [],
                    'modified_labels': [],
                    'unchanged_labels': [],
                    'stats': {
                        'as_is_count': 0,
                        'to_be_count': 0
                    }
                }
            
            # 변경 사항 분석
            return self.analyze_detection_changes(as_is_data, to_be_data)
            
        except Exception as e:
            logger.error(f"JSON 파일 비교 실패: {str(e)}")
            return {
                'error': str(e),
                'removed_labels': [],
                'added_labels': [],
                'modified_labels': [],
                'unchanged_labels': [],
                'stats': {
                    'as_is_count': 0,
                    'to_be_count': 0
                }
            }
    
    def analyze_detection_changes(self, as_is_data: Dict, to_be_data: Dict) -> Dict:
        """AS-IS와 TO-BE 데이터 간의 변경 사항 분석"""
        try:
            # 이미지 크기 비교
            as_is_width = as_is_data.get('width', 0)
            as_is_height = as_is_data.get('height', 0)
            to_be_width = to_be_data.get('width', 0)
            to_be_height = to_be_data.get('height', 0)
            
            size_warning = None
            if abs(as_is_width - to_be_width) > self.tolerance or abs(as_is_height - to_be_height) > self.tolerance:
                size_warning = f"⚠️ 이미지 크기가 크게 다릅니다 (AS-IS: {as_is_width}x{as_is_height}, TO-BE: {to_be_width}x{to_be_height})"
            
            # Detection 데이터 비교
            as_is_boxes = as_is_data.get('detecting', {}).get('data', {}).get('boxes', [])
            to_be_boxes = to_be_data.get('detecting', {}).get('data', {}).get('boxes', [])
            
            # 변경 사항 분석
            removed_labels = []
            added_labels = []
            modified_labels = []
            unchanged_labels = []
            
            # AS-IS 박스의 중심점과 라벨 매핑
            as_is_mapping = {}
            for box in as_is_boxes:
                center = self._get_box_center(box)
                label = box.get('label', '')
                if label:  # 라벨이 있는 경우만 처리
                    as_is_mapping[center] = {
                        'label': label,
                        'box': box
                    }
            
            # TO-BE 박스의 중심점과 라벨 매핑
            to_be_mapping = {}
            for box in to_be_boxes:
                center = self._get_box_center(box)
                label = box.get('label', '')
                if label:  # 라벨이 있는 경우만 처리
                    to_be_mapping[center] = {
                        'label': label,
                        'box': box
                    }
            
            # 변경 사항 분석
            processed_as_is = set()
            processed_to_be = set()
            
            # 1. 위치가 다른 객체 찾기
            position_changes = []
            for as_is_center, as_is_info in as_is_mapping.items():
                found_similar = False
                for to_be_center, to_be_info in to_be_mapping.items():
                    if self._is_similar_position(as_is_center, to_be_center):
                        found_similar = True
                        # 위치가 같으면 라벨 비교
                        if as_is_info['label'] != to_be_info['label']:
                            modified_labels.append({
                                'as_is': as_is_info['label'],
                                'to_be': to_be_info['label'],
                                'position': {
                                    'as_is': as_is_center,
                                    'to_be': to_be_center
                                }
                            })
                        else:
                            unchanged_labels.append(as_is_info['label'])
                        processed_as_is.add(as_is_center)
                        processed_to_be.add(to_be_center)
                        break
                
                if not found_similar:
                    position_changes.append({
                        'center': as_is_center,
                        'label': as_is_info['label']
                    })
            
            # 2. 제거된 객체 찾기 (AS-IS에만 있는 경우)
            for change in position_changes:
                removed_labels.append({
                    'label': change['label'],
                    'position': change['center']
                })
            
            # 3. 추가된 객체 찾기 (TO-BE에만 있는 경우)
            for to_be_center, to_be_info in to_be_mapping.items():
                if to_be_center not in processed_to_be:
                    added_labels.append({
                        'label': to_be_info['label'],
                        'position': to_be_center
                    })
            
            # 통계 계산
            stats = {
                'as_is_count': len(as_is_boxes),
                'to_be_count': len(to_be_boxes),
                'removed_count': len(removed_labels),
                'added_count': len(added_labels),
                'modified_count': len(modified_labels),
                'unchanged_count': len(unchanged_labels),
                'size_warning': size_warning
            }
            
            return {
                'removed_labels': [item['label'] for item in removed_labels],
                'added_labels': [item['label'] for item in added_labels],
                'modified_labels': modified_labels,
                'unchanged_labels': unchanged_labels,
                'stats': stats,
                'details': {
                    'removed': removed_labels,
                    'added': added_labels,
                    'modified': modified_labels,
                    'unchanged': unchanged_labels
                }
            }
            
        except Exception as e:
            logger.error(f"Detection 변경 분석 실패: {str(e)}")
            return {
                'removed_labels': [],
                'added_labels': [],
                'modified_labels': [],
                'unchanged_labels': [],
                'stats': {
                    'as_is_count': 0,
                    'to_be_count': 0,
                    'error': str(e)
                },
                'details': {
                    'removed': [],
                    'added': [],
                    'modified': [],
                    'unchanged': []
                }
            }
    
    def _get_box_center(self, box: Dict) -> Tuple[float, float]:
        """박스의 중심점 좌표 계산"""
        try:
            x1 = float(box.get('x1', 0))
            y1 = float(box.get('y1', 0))
            x2 = float(box.get('x2', 0))
            y2 = float(box.get('y2', 0))
            return ((x1 + x2) / 2, (y1 + y2) / 2)
        except:
            return (0, 0)
    
    def _is_similar_position(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> bool:
        """두 위치가 유사한지 확인 (허용 범위 내)"""
        try:
            x1, y1 = pos1
            x2, y2 = pos2
            return abs(x1 - x2) <= self.tolerance and abs(y1 - y2) <= self.tolerance
        except:
            return False
    
    def visualize_comparison_image(self, image_path: str, json_data: Dict, 
                                 highlight_labels: List[str], title: str, 
                                 highlight_color: str = "red") -> Dict:
        """비교 이미지 시각화"""
        try:
            # 이미지 로드
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            # 폰트 설정
            font_size = 20
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # 박스 그리기
            highlight_count = 0
            for box in json_data.get('detecting', {}).get('data', {}).get('boxes', []):
                label = box.get('label', '')
                if label in highlight_labels:
                    highlight_count += 1
                    x1 = float(box.get('x1', 0))
                    y1 = float(box.get('y1', 0))
                    x2 = float(box.get('x2', 0))
                    y2 = float(box.get('y2', 0))
                    
                    # 박스 그리기
                    draw.rectangle([x1, y1, x2, y2], outline=highlight_color, width=3)
                    
                    # 라벨 그리기
                    text = f"{label}"
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    
                    # 텍스트 배경
                    draw.rectangle(
                        [x1, y1 - text_height - 4, x1 + text_width + 4, y1],
                        fill=highlight_color
                    )
                    
                    # 텍스트
                    draw.text((x1 + 2, y1 - text_height - 2), text, fill="white", font=font)
            
            # Base64 인코딩
            buffered = BytesIO()
            image.save(buffered, format="PNG", quality=95)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return {
                'image_base64': img_str,
                'highlight_count': highlight_count
            }
            
        except Exception as e:
            logger.error(f"비교 이미지 시각화 실패: {str(e)}")
            return None
    
    def generate_change_summary(self, changes: Dict, stats: Dict) -> str:
        """변경 사항 요약 생성"""
        try:
            summary = []
            
            # 크기 경고
            if stats.get('size_warning'):
                summary.append(stats['size_warning'])
            
            # 제거된 객체
            if changes.get('removed_labels'):
                summary.append(f"❌ 제거된 객체: {', '.join(changes['removed_labels'])}")
            
            # 추가된 객체
            if changes.get('added_labels'):
                summary.append(f"➕ 추가된 객체: {', '.join(changes['added_labels'])}")
            
            # 수정된 객체
            if changes.get('modified_labels'):
                mod_summary = []
                for mod in changes['modified_labels']:
                    mod_summary.append(f"{mod['as_is']} → {mod['to_be']}")
                summary.append(f"🔄 수정된 객체: {', '.join(mod_summary)}")
            
            # 통계
            summary.append(f"📊 AS-IS 객체 수: {stats.get('as_is_count', 0)}")
            summary.append(f"📊 TO-BE 객체 수: {stats.get('to_be_count', 0)}")
            summary.append(f"📊 변경되지 않은 객체 수: {stats.get('unchanged_count', 0)}")
            
            return "\n".join(summary)
            
        except Exception as e:
            logger.error(f"변경 사항 요약 생성 실패: {str(e)}")
            return "변경 사항 요약 생성 중 오류가 발생했습니다." 