#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P&ID 객체 검출 변경사항 비교 도구
stream_dose_detect_1.json (AS-IS) vs stream_dose_detect_3.json (TO-BE)
중심점 좌표계 기반으로 객체 검출 결과 비교
실제 변경사항만 표시 (같은 라벨이 같은 위치에 있는 경우 제외)
"""

import json
from PIL import Image, ImageDraw, ImageFont
import os
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
import math

@dataclass
class DetectedObject:
    """검출된 객체 데이터 클래스"""
    id: str
    label: str
    center_x: float
    center_y: float
    width: float
    height: float
    confidence: float = None
    
    @property
    def x1(self) -> int:
        """좌상단 x 좌표 (중심점에서 계산)"""
        return int(self.center_x - self.width/2)
    
    @property
    def y1(self) -> int:
        """좌상단 y 좌표 (중심점에서 계산)"""
        return int(self.center_y - self.height/2)
    
    @property
    def x2(self) -> int:
        """우하단 x 좌표"""
        return int(self.center_x + self.width/2)
    
    @property
    def y2(self) -> int:
        """우하단 y 좌표"""
        return int(self.center_y + self.height/2)

@dataclass
class ObjectChange:
    """객체 변경사항 데이터 클래스"""
    change_type: str  # 'added', 'removed', 'modified', 'moved'
    object_id: str
    old_object: DetectedObject = None
    new_object: DetectedObject = None
    
class ObjectDetectionChangeDetector:
    """객체 검출 변경사항 검출 클래스"""
    
    def __init__(self):
        """초기화"""
        self.change_color = (255, 0, 0)  # 빨간색
        self.font_size_title = 32
        self.font_size_label = 18
        self.position_threshold = 10  # 위치 변경 임계값 (픽셀) - 같은 위치로 간주할 오차범위
        self.size_threshold = 10      # 크기 변경 임계값 (픽셀)
    
    def load_detected_objects(self, json_path: str) -> Tuple[List[DetectedObject], int, int]:
        """검출된 객체들과 이미지 크기 로드"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            objects = []
            for box_data in data['boxes']:
                obj = DetectedObject(
                    id=box_data['id'],
                    label=box_data['label'],
                    center_x=float(box_data['x']),
                    center_y=float(box_data['y']),
                    width=float(box_data['width']),
                    height=float(box_data['height']),
                    confidence=box_data.get('confidence')
                )
                objects.append(obj)
            
            image_width = data['width']
            image_height = data['height']
            
            print(f"✅ 객체 로드 완료: {len(objects)}개 (이미지: {image_width}x{image_height}) - {json_path}")
            return objects, image_width, image_height
            
        except Exception as e:
            print(f"❌ 객체 로드 실패: {e}")
            return [], 0, 0
    
    def normalize_coordinates(self, obj: DetectedObject, image_width: int, image_height: int) -> Tuple[float, float]:
        """좌표를 0-1 범위로 정규화"""
        norm_x = obj.center_x / image_width
        norm_y = obj.center_y / image_height
        return norm_x, norm_y
    
    def calculate_pixel_distance(self, obj1: DetectedObject, obj1_w: int, obj1_h: int,
                                obj2: DetectedObject, obj2_w: int, obj2_h: int) -> float:
        """두 객체 간의 실제 픽셀 거리 계산 (이미지 크기 차이 고려)"""
        # 첫 번째 이미지 좌표를 두 번째 이미지 크기로 스케일링
        scaled_x1 = obj1.center_x * (obj2_w / obj1_w)
        scaled_y1 = obj1.center_y * (obj2_h / obj1_h)
        
        # 실제 픽셀 거리 계산
        dx = scaled_x1 - obj2.center_x
        dy = scaled_y1 - obj2.center_y
        return math.sqrt(dx*dx + dy*dy)

    def find_matching_objects(self, old_objects: List[DetectedObject], old_w: int, old_h: int,
                            new_objects: List[DetectedObject], new_w: int, new_h: int) -> Tuple[Dict[int, int], Set[int], Set[int]]:
        """좌표와 라벨을 기준으로 같은 객체들을 매칭 (픽셀 거리 기준)"""
        matches = {}
        used_old_indices = set()
        used_new_indices = set()
        
        # 픽셀 거리 임계값
        pixel_threshold = 30.0
        
        print(f"   🎯 픽셀 거리 임계값: {pixel_threshold}px")
        print(f"   🔍 AS-IS에서 TO-BE로 매칭 시도 중...")
        
        # 좌표와 라벨을 기준으로 매칭 (ID 완전 무시)
        for old_idx, old_obj in enumerate(old_objects):
            if old_idx in used_old_indices:
                continue
                
            best_match_idx = None
            best_distance = float('inf')
            closest_same_label_distance = float('inf')
            closest_same_label_obj = None
            
            print(f"\n   📍 AS-IS 객체 {old_idx}: {old_obj.label} 중심({old_obj.center_x:.1f},{old_obj.center_y:.1f})")
            
            for new_idx, new_obj in enumerate(new_objects):
                if new_idx in used_new_indices:
                    continue
                
                # 같은 라벨인 경우에만 거리 계산
                if old_obj.label == new_obj.label:
                    distance = self.calculate_pixel_distance(
                        old_obj, old_w, old_h, new_obj, new_w, new_h
                    )
                    
                    print(f"      → TO-BE 객체 {new_idx}: {new_obj.label} 중심({new_obj.center_x:.1f},{new_obj.center_y:.1f}) 거리:{distance:.1f}px")
                    
                    # 가장 가까운 같은 라벨 객체 추적
                    if distance < closest_same_label_distance:
                        closest_same_label_distance = distance
                        closest_same_label_obj = new_obj
                    
                    if distance <= pixel_threshold and distance < best_distance:
                        best_match_idx = new_idx
                        best_distance = distance
            
            if best_match_idx is not None:
                matches[old_idx] = best_match_idx
                used_old_indices.add(old_idx)
                used_new_indices.add(best_match_idx)
                
                best_match = new_objects[best_match_idx]
                print(f"   ✅ 매칭 성공: {old_obj.label} AS-IS({old_obj.center_x:.1f},{old_obj.center_y:.1f}) ↔ TO-BE({best_match.center_x:.1f},{best_match.center_y:.1f}) 거리:{best_distance:.1f}px")
            else:
                if closest_same_label_obj:
                    print(f"   ❌ 매칭 실패: {old_obj.label} - 가장 가까운 같은 라벨과의 거리: {closest_same_label_distance:.1f}px (임계값 {pixel_threshold}px 초과)")
                else:
                    print(f"   ❌ 매칭 실패: {old_obj.label} - 같은 라벨의 객체 없음")
        
        # 매칭되지 않은 객체들의 인덱스
        unmatched_old_indices = set(range(len(old_objects))) - used_old_indices
        unmatched_new_indices = set(range(len(new_objects))) - used_new_indices
        
        return matches, unmatched_old_indices, unmatched_new_indices

    def detect_changes(self, old_objects: List[DetectedObject], old_w: int, old_h: int,
                      new_objects: List[DetectedObject], new_w: int, new_h: int) -> List[ObjectChange]:
        """변경사항 검출 - 픽셀 거리 기준 비교 (ID 무시)"""
        changes = []
        
        print(f"🔍 변경사항 검출 중... (픽셀 거리 기준 비교, ID 무시)")
        print(f"   📏 AS-IS 이미지: {old_w}x{old_h}")
        print(f"   📏 TO-BE 이미지: {new_w}x{new_h}")
        
        # 좌표 기준으로 매칭되는 객체들과 매칭되지 않은 객체들 찾기
        matches, unmatched_old_indices, unmatched_new_indices = self.find_matching_objects(
            old_objects, old_w, old_h, new_objects, new_w, new_h
        )
        
        print(f"\n   📝 매칭된 객체: {len(matches)}개 (같은 위치의 같은 라벨)")
        print(f"   📝 매칭되지 않은 AS-IS 객체: {len(unmatched_old_indices)}개")
        print(f"   📝 매칭되지 않은 TO-BE 객체: {len(unmatched_new_indices)}개")
        
        # 매칭된 객체들은 실제로는 변경사항이 없는 것으로 간주
        # (같은 라벨이 같은 위치에 있음)
        
        # 제거된 객체들 (매칭되지 않은 AS-IS 객체들)
        for old_idx in unmatched_old_indices:
            old_obj = old_objects[old_idx]
            changes.append(ObjectChange(
                change_type='removed',
                object_id=old_obj.id,
                old_object=old_obj
            ))
        
        # 추가된 객체들 (매칭되지 않은 TO-BE 객체들)
        for new_idx in unmatched_new_indices:
            new_obj = new_objects[new_idx]
            changes.append(ObjectChange(
                change_type='added',
                object_id=new_obj.id,
                new_object=new_obj
            ))
        
        print(f"\n🔍 실제 변경사항 결과:")
        print(f"   • 추가됨: {len([c for c in changes if c.change_type == 'added'])}개")
        print(f"   • 제거됨: {len([c for c in changes if c.change_type == 'removed'])}개")
        print(f"   • 매칭됨: {len(matches)}개 (표시 안 함)")
        print(f"   📊 총 변경사항: {len(changes)}개")
        
        return changes
    
    def get_font(self, font_size: int):
        """폰트 로드"""
        try:
            return ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
        except:
            try:
                return ImageFont.truetype("arial.ttf", font_size)
            except:
                return ImageFont.load_default()
    
    def highlight_changes_on_image(self, image: Image.Image, changes: List[ObjectChange], 
                                  title: str, is_old_version: bool = True) -> Image.Image:
        """이미지에 변경사항 하이라이트 표시"""
        
        result_image = image.copy()
        draw = ImageDraw.Draw(result_image)
        
        font_label = self.get_font(self.font_size_label)
        
        # 변경사항 표시
        for change in changes:
            if is_old_version:
                # AS-IS 버전: 제거된 것과 수정된 것의 원래 버전
                if change.change_type == 'removed':
                    obj = change.old_object
                    self._draw_change_highlight(draw, obj, "REMOVED", font_label)
                elif change.change_type in ['modified', 'moved']:
                    obj = change.old_object
                    label = "MOVED" if change.change_type == 'moved' else "MODIFIED"
                    self._draw_change_highlight(draw, obj, label, font_label)
            else:
                # TO-BE 버전: 추가된 것과 수정된 것의 새 버전
                if change.change_type == 'added':
                    obj = change.new_object
                    self._draw_change_highlight(draw, obj, "ADDED", font_label)
                elif change.change_type in ['modified', 'moved']:
                    obj = change.new_object
                    label = "MOVED" if change.change_type == 'moved' else "MODIFIED"
                    self._draw_change_highlight(draw, obj, label, font_label)
        
        # 제목 추가
        title_font = self.get_font(self.font_size_title)
        
        # 제목 배경
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        
        title_x = 20
        title_y = 20
        
        # 제목 배경 사각형
        draw.rectangle([title_x-10, title_y-5, title_x+title_width+10, title_y+title_height+5], 
                      fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        
        # 제목 텍스트
        draw.text((title_x, title_y), title, fill=(0, 0, 0), font=title_font)
        
        return result_image
    
    def _draw_change_highlight(self, draw: ImageDraw.Draw, obj: DetectedObject, 
                              change_label: str, font):
        """객체에 변경사항 하이라이트 그리기"""
        
        # 객체 바운딩 박스 (중심점 기준으로 계산)
        x1, y1 = obj.x1, obj.y1
        x2, y2 = obj.x2, obj.y2
        
        # 두꺼운 빨간색 테두리
        for width in range(6):
            draw.rectangle([x1-width, y1-width, x2+width, y2+width], 
                          outline=self.change_color, fill=None)
        
        # 변경 라벨
        label_text = f"{change_label}: {obj.label} (ID:{obj.id})"
        
        # 라벨 위치 계산
        label_bbox = draw.textbbox((0, 0), label_text, font=font)
        label_width = label_bbox[2] - label_bbox[0]
        label_height = label_bbox[3] - label_bbox[1]
        
        label_x = x1
        label_y = y1 - label_height - 12
        
        # 아래쪽에 표시 (위쪽 공간 부족시)
        if label_y < 0:
            label_y = y2 + 8
        
        # 라벨 배경
        draw.rectangle([label_x-4, label_y-2, label_x+label_width+4, label_y+label_height+2], 
                      fill=self.change_color, outline=None)
        
        # 라벨 텍스트 (흰색)
        draw.text((label_x, label_y), label_text, fill=(255, 255, 255), font=font)
    
    def create_side_by_side_comparison(self, as_is_image: Image.Image, to_be_image: Image.Image, 
                                     changes: List[ObjectChange]) -> Image.Image:
        """좌우 비교 이미지 생성"""
        
        # AS-IS 이미지에 변경사항 표시
        as_is_highlighted = self.highlight_changes_on_image(
            as_is_image, changes, "AS-IS (stream_does_ai_1)", is_old_version=True
        )
        
        # TO-BE 이미지에 변경사항 표시
        to_be_highlighted = self.highlight_changes_on_image(
            to_be_image, changes, "TO-BE (stream_does_ai_3)", is_old_version=False
        )
        
        # 이미지 크기
        as_is_width, as_is_height = as_is_highlighted.size
        to_be_width, to_be_height = to_be_highlighted.size
        
        # 결합된 이미지 크기
        padding = 50
        combined_width = as_is_width + to_be_width + padding
        combined_height = max(as_is_height, to_be_height) + 100  # 상단 여백
        
        # 새 이미지 생성
        combined = Image.new('RGB', (combined_width, combined_height), color=(245, 245, 245))
        
        # 이미지 붙이기
        y_offset = 80
        combined.paste(as_is_highlighted, (0, y_offset))
        combined.paste(to_be_highlighted, (as_is_width + padding, y_offset))
        
        # 메인 제목 추가
        draw = ImageDraw.Draw(combined)
        main_title = "P&ID Object Detection Change Analysis (Coordinate-based)"
        main_font = self.get_font(36)
        
        main_bbox = draw.textbbox((0, 0), main_title, font=main_font)
        main_width = main_bbox[2] - main_bbox[0]
        main_x = (combined_width - main_width) // 2
        
        draw.text((main_x, 20), main_title, fill=(0, 0, 0), font=main_font)
        
        # 변경사항 통계
        stats_text = f"Coordinate-based Changes: {len([c for c in changes if c.change_type == 'added'])} Added, " \
                    f"{len([c for c in changes if c.change_type == 'removed'])} Removed"
        
        stats_font = self.get_font(22)
        stats_bbox = draw.textbbox((0, 0), stats_text, font=stats_font)
        stats_width = stats_bbox[2] - stats_bbox[0]
        stats_x = (combined_width - stats_width) // 2
        
        draw.text((stats_x, 60), stats_text, fill=(255, 0, 0), font=stats_font)
        
        return combined
    
    def compare_object_detections(self, as_is_json: str, to_be_json: str, 
                                as_is_image: str, to_be_image: str, 
                                output_path: str = "output/object_detection_comparison.png"):
        """객체 검출 결과 비교 메인 실행 함수"""
        
        print("🚀 P&ID 객체 검출 변경사항 분석 시작 (좌표 기준 비교)")
        print("=" * 70)
        
        # 1. 검출된 객체들 로드
        print("📁 검출 객체 로드 중...")
        as_is_objects, as_is_w, as_is_h = self.load_detected_objects(as_is_json)
        to_be_objects, to_be_w, to_be_h = self.load_detected_objects(to_be_json)
        
        if not as_is_objects or not to_be_objects:
            print("❌ 객체 로드 실패")
            return
        
        # 2. 변경사항 검출 (이미지 크기 정보 전달)
        print("\n🔍 변경사항 검출 중...")
        changes = self.detect_changes(as_is_objects, as_is_w, as_is_h, 
                                    to_be_objects, to_be_w, to_be_h)
        
        # 3. 이미지 로드
        print("\n📷 이미지 로드 중...")
        as_is_img = Image.open(as_is_image)
        to_be_img = Image.open(to_be_image)
        
        print(f"   AS-IS 이미지: {as_is_img.size} (JSON: {as_is_w}x{as_is_h})")
        print(f"   TO-BE 이미지: {to_be_img.size} (JSON: {to_be_w}x{to_be_h})")
        
        # 4. 비교 이미지 생성
        print("\n🎨 비교 이미지 생성 중...")
        comparison_image = self.create_side_by_side_comparison(as_is_img, to_be_img, changes)
        
        # 5. 저장
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        comparison_image.save(output_path, quality=98, optimize=True)
        
        print(f"💾 비교 이미지 저장 완료: {output_path}")
        
        # 6. 화면에 표시
        comparison_image.show()
        
        # 7. 상세 변경사항 출력
        self.print_detailed_changes(changes)
        
        print("=" * 70)
        print("✅ P&ID 객체 검출 변경사항 분석 완료!")
    
    def print_detailed_changes(self, changes: List[ObjectChange]):
        """상세 변경사항 출력"""
        print(f"\n📋 상세 변경사항 (좌표 기준 비교):")
        
        if not changes:
            print("   실제 변경사항이 없습니다. (모든 객체가 같은 위치에 유지됨)")
            return
        
        # 추가된 객체들
        added_changes = [c for c in changes if c.change_type == 'added']
        if added_changes:
            print(f"\n   ➕ 추가된 객체들 ({len(added_changes)}개):")
            for change in added_changes:
                obj = change.new_object
                print(f"     • ID {obj.id}: {obj.label} "
                      f"중심({obj.center_x:.1f},{obj.center_y:.1f}) 크기({obj.width:.1f}x{obj.height:.1f})")
        
        # 제거된 객체들
        removed_changes = [c for c in changes if c.change_type == 'removed']
        if removed_changes:
            print(f"\n   ➖ 제거된 객체들 ({len(removed_changes)}개):")
            for change in removed_changes:
                obj = change.old_object
                print(f"     • ID {obj.id}: {obj.label} "
                      f"중심({obj.center_x:.1f},{obj.center_y:.1f}) 크기({obj.width:.1f}x{obj.height:.1f})")

def get_change_analysis_result(as_is_json: str = "data/stream_dose_detect_1.json", 
                              to_be_json: str = "data/stream_dose_detect_3.json", 
                              as_is_image: str = "data/uploaded_files/stream_does_ai_1_page_1.png", 
                              to_be_image: str = "data/uploaded_files/stream_does_ai_3.pdf_page_1.png",
                              output_path: str = "output/object_detection_comparison.png"):
    """변경사항 분석 결과를 반환하는 함수 (챗봇용)"""
    
    detector = ObjectDetectionChangeDetector()
    
    try:
        # 검출된 객체들 로드
        as_is_objects, as_is_w, as_is_h = detector.load_detected_objects(as_is_json)
        to_be_objects, to_be_w, to_be_h = detector.load_detected_objects(to_be_json)
        
        if not as_is_objects or not to_be_objects:
            return None, "객체 로드 실패"
        
        # 변경사항 검출 (이미지 크기 정보 전달)
        changes = detector.detect_changes(as_is_objects, as_is_w, as_is_h, 
                                        to_be_objects, to_be_w, to_be_h)
        
        # 이미지 로드
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
        
        summary = {
            "comparison_image_path": output_path,
            "total_changes": len(changes),
            "added_objects": added_count,
            "removed_objects": removed_count,
            "matched_objects": matched_count,
            "changes_detail": changes,
            "as_is_total": len(as_is_objects),
            "to_be_total": len(to_be_objects)
        }
        
        return summary, None
        
    except Exception as e:
        return None, f"변경사항 분석 실패: {str(e)}"

def main():
    """메인 실행 함수"""
    detector = ObjectDetectionChangeDetector()
    
    # 파일 경로 설정
    as_is_json = "data/stream_dose_detect_1.json"
    to_be_json = "data/stream_dose_detect_3.json"
    as_is_image = "data/uploaded_files/stream_does_ai_1_page_1.png"
    to_be_image = "data/uploaded_files/stream_does_ai_3.pdf_page_1.png"
    output_path = "output/object_detection_comparison.png"
    
    # 비교 실행
    detector.compare_object_detections(as_is_json, to_be_json, as_is_image, to_be_image, output_path)

if __name__ == "__main__":
    main() 