#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
첫 번째 데이터셋 객체 검출 시각화 도구
stream_does_ai_1.pdf + stream_dose_detect_1.json
JSON의 x,y 좌표를 바운딩 박스의 중심점으로 해석
"""

import json
from PIL import Image, ImageDraw, ImageFont
import os
from typing import Dict, List, Tuple

class FirstDatasetVisualizer:
    """첫 번째 데이터셋 중심점 좌표 기반 시각화 클래스"""
    
    def __init__(self):
        """초기화"""
        self.colors = self._generate_colors()
        self.font_size = 20
        
    def _generate_colors(self) -> List[Tuple[int, int, int]]:
        """RGB 색상 팔레트 생성"""
        colors = [
            (255, 107, 107),  # Red
            (78, 205, 196),   # Teal  
            (69, 183, 209),   # Blue
            (150, 206, 180),  # Green
            (255, 234, 167),  # Yellow
            (221, 160, 221),  # Plum
            (244, 164, 96),   # Sandy Brown
            (135, 206, 235),  # Sky Blue
            (255, 182, 193),  # Pink
            (144, 238, 144),  # Light Green
            (255, 228, 181),  # Moccasin
            (211, 211, 211),  # Light Gray
            (255, 160, 122),  # Light Salmon
            (32, 178, 170),   # Light Sea Green
            (119, 136, 153),  # Light Slate Gray
            (255, 105, 180),  # Hot Pink
            (50, 205, 50),    # Lime Green
            (255, 69, 0),     # Orange Red
            (147, 112, 219),  # Medium Purple
            (0, 206, 209),    # Dark Turquoise
        ]
        return colors
    
    def load_data(self, png_path: str, json_path: str) -> Tuple[Image.Image, Dict]:
        """이미지와 JSON 데이터 로드"""
        try:
            # 이미지 로드
            image = Image.open(png_path)
            
            # JSON 로드
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # JSON의 width와 height에 맞게 이미지 크기 조정
            expected_width = json_data.get('width', image.width)
            expected_height = json_data.get('height', image.height)
            
            if image.size != (expected_width, expected_height):
                image = image.resize((expected_width, expected_height), Image.Resampling.LANCZOS)
            
            print(f"✅ 이미지 로드: {image.size[0]} x {image.size[1]}")
            print(f"✅ JSON 로드: {json_data['width']} x {json_data['height']}")
            
            # OCR과 Detection 데이터 확인
            ocr_data = json_data.get('ocr', {})
            detection_data = json_data.get('detecting', {}).get('data', {})
            
            print(f"📝 OCR 텍스트 수: {len(ocr_data.get('images', [{}])[0].get('fields', []))}")
            print(f"🎯 검출 객체 수: {len(detection_data.get('boxes', []))}")
            
            return image, json_data
            
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            return None, None
    
    def assign_label_colors(self, boxes: List[Dict]) -> Dict[str, Tuple[int, int, int]]:
        """라벨별 색상 할당"""
        unique_labels = list(set([box['label'] for box in boxes]))
        unique_labels.sort()
        
        label_colors = {}
        for i, label in enumerate(unique_labels):
            label_colors[label] = self.colors[i % len(self.colors)]
        
        return label_colors
    
    def get_font(self, font_size: int):
        """폰트 로드 (시스템에 맞게)"""
        try:
            # macOS 기본 폰트
            return ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
        except:
            try:
                # Windows 기본 폰트
                return ImageFont.truetype("arial.ttf", font_size)
            except:
                # 기본 폰트
                return ImageFont.load_default()
    
    def draw_center_based_boxes(self, image: Image.Image, json_data: Dict) -> Image.Image:
        """중심점 좌표로 바운딩 박스 그리기"""
        
        # 이미지 복사 (원본 보존)
        result_image = image.copy()
        draw = ImageDraw.Draw(result_image)
        
        # Detection 데이터 가져오기
        detection_data = json_data.get('detecting', {}).get('data', {})
        boxes = detection_data.get('boxes', [])
        
        # 라벨별 색상 할당
        label_colors = self.assign_label_colors(boxes)
        font = self.get_font(self.font_size)
        
        print(f"\n🎨 중심점 기준으로 {len(boxes)}개 박스 그리기 시작")
        
        for i, box in enumerate(boxes):
            # 중심점 좌표
            center_x = float(box['x'])
            center_y = float(box['y'])
            width = float(box['width'])
            height = float(box['height'])
            
            # 좌상단 좌표 계산 (중심점에서 width/2, height/2 만큼 빼기)
            x = center_x - width/2
            y = center_y - height/2
            
            # 정수 좌표로 변환
            x1, y1 = int(x), int(y)
            x2, y2 = int(x + width), int(y + height)
            
            # 색상
            label = box['label']
            color = label_colors[label]
            
            # 두꺼운 바운딩 박스 그리기
            line_width = 4
            for offset in range(line_width):
                draw.rectangle([x1-offset, y1-offset, x2+offset, y2+offset], 
                             outline=color, fill=None)
            
            # 라벨 텍스트 (ID 포함)
            label_text = f"{box['id']}: {label}"
            
            # 텍스트 크기 계산
            bbox = draw.textbbox((0, 0), label_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # 텍스트 위치 계산
            text_x = x1
            text_y = y1 - text_height - 6
            
            # 위쪽 공간이 부족하면 박스 아래에 표시
            if text_y < 0:
                text_y = y2 + 6
            
            # 텍스트 배경 사각형
            bg_x1 = text_x - 4
            bg_y1 = text_y - 4
            bg_x2 = text_x + text_width + 4
            bg_y2 = text_y + text_height + 4
            
            # 배경 테두리
            draw.rectangle([bg_x1-1, bg_y1-1, bg_x2+1, bg_y2+1], 
                         fill=(255, 255, 255), outline=color, width=1)
            draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], 
                         fill=color, outline=None)
            
            # 텍스트 그리기 (흰색)
            draw.text((text_x, text_y), label_text, fill=(255, 255, 255), font=font)
            
            print(f"  ✅ 박스 {i+1}: {label} (ID:{box['id']}) center({center_x:.1f},{center_y:.1f}) → ({x1},{y1})-({x2},{y2})")
        
        return result_image
    
    def create_legend(self, json_data: Dict, label_colors: Dict[str, Tuple[int, int, int]], 
                     width: int = 350, height: int = None) -> Image.Image:
        """고품질 범례 이미지 생성"""
        unique_labels = sorted(label_colors.keys())
        
        if height is None:
            height = len(unique_labels) * 45 + 80
        
        # 범례 이미지 생성
        legend_img = Image.new('RGB', (width, height), color=(248, 248, 248))
        draw = ImageDraw.Draw(legend_img)
        
        # 테두리
        draw.rectangle([0, 0, width-1, height-1], outline=(200, 200, 200), width=2)
        
        # 제목
        title_font = self.get_font(22)
        draw.text((15, 15), "P&ID Objects (Dataset 1)", fill=(50, 50, 50), font=title_font)
        
        # 구분선
        draw.line([15, 50, width-15, 50], fill=(200, 200, 200), width=2)
        
        # 각 라벨별 색상과 텍스트
        item_font = self.get_font(16)
        for i, label in enumerate(unique_labels):
            y_pos = 70 + i * 40
            color = label_colors[label]
            
            # 색상 사각형
            draw.rectangle([20, y_pos, 45, y_pos + 22], fill=color, outline=(100, 100, 100), width=1)
            
            # 라벨 텍스트
            draw.text((55, y_pos + 2), label, fill=(50, 50, 50), font=item_font)
        
        return legend_img
    
    def combine_image_and_legend(self, main_image: Image.Image, legend: Image.Image) -> Image.Image:
        """메인 이미지와 범례 결합"""
        main_width, main_height = main_image.size
        legend_width, legend_height = legend.size
        
        # 결합된 이미지 크기
        padding = 25
        combined_width = main_width + legend_width + padding
        combined_height = max(main_height, legend_height)
        
        # 새 이미지 생성
        combined = Image.new('RGB', (combined_width, combined_height), color=(245, 245, 245))
        
        # 메인 이미지 붙이기
        combined.paste(main_image, (0, 0))
        
        # 범례 붙이기 (세로 중앙 정렬)
        legend_x = main_width + padding//2
        legend_y = (combined_height - legend_height) // 2
        combined.paste(legend, (legend_x, legend_y))
        
        return combined
    
    def visualize_dataset1(self, png_path: str, json_path: str, save_path: str = None, 
                          show_legend: bool = True) -> Image.Image:
        """첫 번째 데이터셋 고품질 시각화 실행"""
        print("🚀 첫 번째 데이터셋 중심점 기준 시각화 시작")
        print("=" * 70)
        
        # 1. 데이터 로드
        image, json_data = self.load_data(png_path, json_path)
        if image is None or json_data is None:
            return None
        
        # 2. 중심점 기준으로 박스 그리기
        result_image = self.draw_center_based_boxes(image, json_data)
        
        # 3. 범례 추가 (선택사항)
        if show_legend:
            label_colors = self.assign_label_colors(json_data['detecting']['data']['boxes'])
            legend = self.create_legend(json_data, label_colors)
            result_image = self.combine_image_and_legend(result_image, legend)
        
        # 4. 저장
        if save_path:
            result_image.save(save_path, quality=98, optimize=True)
            print(f"💾 첫 번째 데이터셋 이미지 저장됨: {save_path}")
        
        # 5. 통계 출력
        self.print_detailed_statistics(json_data)
        
        print("=" * 70)
        print("✅ 첫 번째 데이터셋 시각화 완료!")
        
        return result_image
    
    def print_detailed_statistics(self, json_data: Dict) -> None:
        """상세 통계 정보 출력"""
        # Detection 데이터 가져오기
        detection_data = json_data.get('detecting', {}).get('data', {})
        boxes = detection_data.get('boxes', [])
        
        # OCR 데이터 가져오기
        ocr_data = json_data.get('ocr', {})
        ocr_fields = ocr_data.get('images', [{}])[0].get('fields', [])
        
        print(f"\n📊 데이터셋 검출 통계:")
        print(f"   🎯 총 객체 수: {len(boxes)}개")
        print(f"   📝 총 OCR 텍스트 수: {len(ocr_fields)}개")
        print(f"   📐 이미지 크기: {json_data['width']} x {json_data['height']}")
        print(f"   🔧 좌표 해석: 중심점 기준")
        
        # Detection 객체 통계
        label_counts = {}
        for box in boxes:
            label = box['label']
            label_counts[label] = label_counts.get(label, 0) + 1
        
        print(f"\n   📋 객체별 검출 개수:")
        for label, count in sorted(label_counts.items()):
            print(f"     • {label}: {count}개")
        
        print(f"\n   🏷️ 총 객체 유형: {len(label_counts)}가지")
        
        # OCR 텍스트 통계
        print(f"\n   📝 OCR 텍스트 샘플:")
        for i, field in enumerate(ocr_fields[:5]):  # 처음 5개만 표시
            print(f"     • {field.get('inferText', '')}")
        if len(ocr_fields) > 5:
            print(f"     • ... 외 {len(ocr_fields)-5}개")

def main():
    """메인 실행 함수"""
    # 시각화 도구 초기화
    visualizer = FirstDatasetVisualizer()
    
    # 파일 경로 설정
    png_path = "/Users/kjh/Desktop/doyeonso/doyeonso/uploads/uploaded_images/stream_dose_ai_1.png"
    json_path = "/Users/kjh/Desktop/doyeonso/doyeonso/uploads/merged_results/stream_dose_ai_1.json"
    save_path = "/Users/kjh/Desktop/doyeonso/doyeonso/uploads/uploaded_images/visualization_result.png"
    # 출력 디렉터리 생성
    os.makedirs("output", exist_ok=True)
    
    # 첫 번째 데이터셋 시각화 실행
    result_image = visualizer.visualize_dataset1(png_path, json_path, save_path, show_legend=True)
    if result_image:
        result_image.show()

if __name__ == "__main__":
    main() 