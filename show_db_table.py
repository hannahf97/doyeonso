#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
from datetime import datetime
import pandas as pd

def show_database_table():
    """데이터베이스 내용을 표 형식으로 출력"""
    
    # 데이터베이스 연결
    conn = sqlite3.connect('domyun.db')
    cursor = conn.cursor()
    
    try:
        # 모든 레코드 조회
        cursor.execute("""
            SELECT id, filename, username, created_at, image_path, 
                   ocr_data, detection_data, file_mapping
            FROM domyun 
            ORDER BY id DESC
        """)
        
        records = cursor.fetchall()
        
        if not records:
            print("📋 데이터베이스에 저장된 데이터가 없습니다.")
            return
        
        print(f"📊 데이터베이스 테이블 현황 (총 {len(records)}개 레코드)")
        print("=" * 120)
        
        # 기본 정보 테이블
        basic_data = []
        for record in records:
            id_val, filename, username, created_at, image_path, ocr_data, detection_data, file_mapping = record
            
            # OCR 데이터 요약
            ocr_summary = "❌ 없음"
            if ocr_data:
                try:
                    ocr_json = json.loads(ocr_data)
                    if ocr_json.get('images') and len(ocr_json['images']) > 0:
                        fields_count = len(ocr_json['images'][0].get('fields', []))
                        ocr_summary = f"✅ {fields_count}개 필드"
                except:
                    ocr_summary = "⚠️ 파싱 오류"
            
            # Detection 데이터 요약
            detection_summary = "❌ 없음"
            if detection_data:
                try:
                    detection_json = json.loads(detection_data)
                    if detection_json.get('data', {}).get('boxes'):
                        boxes_count = len(detection_json['data']['boxes'])
                        detection_summary = f"✅ {boxes_count}개 객체"
                except:
                    detection_summary = "⚠️ 파싱 오류"
            
            # 파일 매핑 정보
            mapping_summary = "❌ 없음"
            if file_mapping:
                try:
                    mapping_json = json.loads(file_mapping)
                    matched_files = mapping_json.get('matched_detection_files', 0)
                    mapping_summary = f"✅ {matched_files}개 매칭"
                except:
                    mapping_summary = "⚠️ 파싱 오류"
            
            basic_data.append({
                'ID': id_val,
                '파일명': filename[:30] + '...' if len(filename) > 30 else filename,
                '사용자': username,
                '생성일시': created_at[:19] if created_at else 'N/A',
                'OCR': ocr_summary,
                'Detection': detection_summary,
                '매핑': mapping_summary
            })
        
        # pandas DataFrame으로 표 출력
        df = pd.DataFrame(basic_data)
        print(df.to_string(index=False))
        
        print("\n" + "=" * 120)
        
        # 상세 통계
        print("📈 상세 통계:")
        print(f"   • 총 레코드 수: {len(records)}")
        
        # OCR 성공률
        ocr_success = sum(1 for record in records if record[5] and '✅' in str(record[5]))
        print(f"   • OCR 처리 성공: {ocr_success}/{len(records)} ({ocr_success/len(records)*100:.1f}%)")
        
        # Detection 성공률  
        detection_success = sum(1 for record in records if record[6] and 'boxes' in str(record[6]))
        print(f"   • Detection 처리 성공: {detection_success}/{len(records)} ({detection_success/len(records)*100:.1f}%)")
        
        # 파일 형식별 통계
        file_extensions = {}
        for record in records:
            filename = record[1]
            if filename:
                ext = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
                file_extensions[ext] = file_extensions.get(ext, 0) + 1
        
        print(f"   • 파일 형식별:")
        for ext, count in file_extensions.items():
            print(f"     - {ext.upper()}: {count}개")
        
        print("\n💡 특정 레코드의 상세 정보를 보려면:")
        print("   python show_db_table.py --detail [ID]")
        
    except sqlite3.Error as e:
        print(f"❌ 데이터베이스 오류: {e}")
    
    finally:
        conn.close()

def show_record_detail(record_id):
    """특정 레코드의 상세 정보 출력"""
    
    conn = sqlite3.connect('domyun.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM domyun WHERE id = ?
        """, (record_id,))
        
        record = cursor.fetchone()
        
        if not record:
            print(f"❌ ID {record_id}에 해당하는 레코드를 찾을 수 없습니다.")
            return
        
        print(f"📋 레코드 ID {record_id} 상세 정보")
        print("=" * 80)
        
        # 기본 정보
        print(f"📄 파일명: {record[1]}")
        print(f"👤 사용자: {record[2]}")
        print(f"📅 생성일시: {record[3]}")
        print(f"📁 이미지 경로: {record[4]}")
        
        # OCR 데이터 상세
        print(f"\n🔍 OCR 데이터:")
        if record[5]:
            try:
                ocr_data = json.loads(record[5])
                if ocr_data.get('images') and len(ocr_data['images']) > 0:
                    fields = ocr_data['images'][0].get('fields', [])
                    print(f"   • 추출된 텍스트 필드: {len(fields)}개")
                    
                    # 처음 5개 필드만 표시
                    for i, field in enumerate(fields[:5]):
                        text = field.get('inferText', 'N/A')
                        confidence = field.get('inferConfidence', 0)
                        print(f"     - {text} (신뢰도: {confidence:.3f})")
                    
                    if len(fields) > 5:
                        print(f"     ... 외 {len(fields) - 5}개 더")
                else:
                    print("   • OCR 결과 없음")
            except:
                print("   • OCR 데이터 파싱 오류")
        else:
            print("   • OCR 데이터 없음")
        
        # Detection 데이터 상세
        print(f"\n🎯 Detection 데이터:")
        if record[6]:
            try:
                detection_data = json.loads(record[6])
                boxes = detection_data.get('data', {}).get('boxes', [])
                print(f"   • 감지된 객체: {len(boxes)}개")
                
                # 객체별 통계
                label_counts = {}
                for box in boxes:
                    label = box.get('label', 'unknown')
                    label_counts[label] = label_counts.get(label, 0) + 1
                
                for label, count in sorted(label_counts.items()):
                    print(f"     - {label}: {count}개")
                    
            except:
                print("   • Detection 데이터 파싱 오류")
        else:
            print("   • Detection 데이터 없음")
        
        # 파일 매핑 정보
        print(f"\n🔗 파일 매핑:")
        if record[7]:
            try:
                mapping_data = json.loads(record[7])
                print(f"   • 매칭된 Detection 파일: {mapping_data.get('matched_detection_files', 0)}개")
                sources = mapping_data.get('detection_sources', [])
                if sources:
                    print(f"   • Detection 소스 파일:")
                    for source in sources:
                        print(f"     - {source}")
            except:
                print("   • 매핑 데이터 파싱 오류")
        else:
            print("   • 매핑 데이터 없음")
            
    except sqlite3.Error as e:
        print(f"❌ 데이터베이스 오류: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--detail' and len(sys.argv) > 2:
        try:
            record_id = int(sys.argv[2])
            show_record_detail(record_id)
        except ValueError:
            print("❌ 올바른 레코드 ID를 입력해주세요.")
    else:
        show_database_table() 