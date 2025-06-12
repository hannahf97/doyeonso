#!/usr/bin/env python3
"""
데이터베이스 저장 데이터 확인 스크립트
"""

import json
from config.database_config import get_db_connection
from config.user_config import USER_NAME

def check_database_connection():
    """데이터베이스 연결 확인"""
    print("🔌 데이터베이스 연결 확인 중...")
    
    try:
        conn = get_db_connection()
        if conn:
            print("✅ 데이터베이스 연결 성공!")
            conn.close()
            return True
        else:
            print("❌ 데이터베이스 연결 실패!")
            return False
    except Exception as e:
        print(f"❌ 연결 오류: {e}")
        return False

def check_table_exists():
    """domyun 테이블 존재 확인"""
    print("\n📋 테이블 존재 확인 중...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'domyun'
            );
        """)
        
        exists = cursor.fetchone()[0]
        
        if exists:
            print("✅ domyun 테이블이 존재합니다!")
        else:
            print("❌ domyun 테이블이 존재하지 않습니다!")
            print("   setup_database.py를 실행해서 테이블을 생성하세요.")
        
        cursor.close()
        conn.close()
        
        return exists
        
    except Exception as e:
        print(f"❌ 테이블 확인 오류: {e}")
        return False

def show_all_records():
    """모든 저장된 레코드 조회"""
    print("\n📊 저장된 데이터 조회 중...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 전체 레코드 수 확인
        cursor.execute("SELECT COUNT(*) FROM domyun;")
        total_count = cursor.fetchone()[0]
        
        print(f"📈 총 저장된 레코드 수: {total_count}개")
        
        if total_count == 0:
            print("📭 저장된 데이터가 없습니다.")
            cursor.close()
            conn.close()
            return
        
        # 최근 10개 레코드 조회
        cursor.execute("""
            SELECT d_id, d_name, "user", create_date, image_path 
            FROM domyun 
            ORDER BY d_id DESC 
            LIMIT 10;
        """)
        
        records = cursor.fetchall()
        
        print("\n📋 최근 저장된 데이터 (최대 10개):")
        print("-" * 100)
        print(f"{'ID':<5} {'파일명':<25} {'사용자':<10} {'생성일시':<20} {'이미지경로':<30}")
        print("-" * 100)
        
        for record in records:
            d_id, d_name, user, create_date, image_path = record
            create_date_str = create_date.strftime("%Y-%m-%d %H:%M:%S") if create_date else "N/A"
            image_path_short = (image_path[:27] + "...") if image_path and len(image_path) > 30 else (image_path or "N/A")
            
            print(f"{d_id:<5} {d_name:<25} {user:<10} {create_date_str:<20} {image_path_short:<30}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 데이터 조회 오류: {e}")

def show_specific_record(record_id):
    """특정 레코드의 상세 정보 조회"""
    print(f"\n🔍 ID {record_id} 레코드 상세 조회...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT d_id, d_name, "user", create_date, json_data, image_path 
            FROM domyun 
            WHERE d_id = %s;
        """, (record_id,))
        
        record = cursor.fetchone()
        
        if not record:
            print(f"❌ ID {record_id}인 레코드를 찾을 수 없습니다.")
            cursor.close()
            conn.close()
            return
        
        d_id, d_name, user, create_date, json_data, image_path = record
        
        print("=" * 80)
        print(f"📌 레코드 ID: {d_id}")
        print(f"📁 파일명: {d_name}")
        print(f"👤 사용자: {user}")
        print(f"📅 생성일시: {create_date}")
        print(f"🖼️ 이미지 경로: {image_path}")
        
        if json_data:
            print(f"\n📊 JSON 데이터:")
            print("-" * 40)
            # JSON을 예쁘게 출력
            print(json.dumps(json_data, ensure_ascii=False, indent=2))
        else:
            print(f"\n📊 JSON 데이터: 없음")
        
        print("=" * 80)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 레코드 조회 오류: {e}")

def show_user_records():
    """현재 설정된 사용자의 레코드만 조회"""
    print(f"\n👤 사용자 '{USER_NAME}'의 레코드 조회...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM domyun WHERE "user" = %s;
        """, (USER_NAME,))
        
        user_count = cursor.fetchone()[0]
        print(f"📈 '{USER_NAME}' 사용자의 레코드 수: {user_count}개")
        
        if user_count == 0:
            print(f"📭 '{USER_NAME}' 사용자의 데이터가 없습니다.")
            cursor.close()
            conn.close()
            return
        
        cursor.execute("""
            SELECT d_id, d_name, create_date, image_path 
            FROM domyun 
            WHERE "user" = %s 
            ORDER BY d_id DESC;
        """, (USER_NAME,))
        
        records = cursor.fetchall()
        
        print(f"\n📋 '{USER_NAME}' 사용자의 모든 레코드:")
        print("-" * 80)
        print(f"{'ID':<5} {'파일명':<25} {'생성일시':<20} {'이미지경로':<25}")
        print("-" * 80)
        
        for record in records:
            d_id, d_name, create_date, image_path = record
            create_date_str = create_date.strftime("%Y-%m-%d %H:%M:%S") if create_date else "N/A"
            image_path_short = (image_path[:22] + "...") if image_path and len(image_path) > 25 else (image_path or "N/A")
            
            print(f"{d_id:<5} {d_name:<25} {create_date_str:<20} {image_path_short:<25}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 사용자 데이터 조회 오류: {e}")

def main():
    """메인 함수"""
    print("🔍 데이터베이스 저장 상태 확인")
    print("=" * 50)
    
    # 1. 데이터베이스 연결 확인
    if not check_database_connection():
        print("\n❌ 데이터베이스에 연결할 수 없습니다.")
        print("   .env 파일의 데이터베이스 설정을 확인하세요.")
        return
    
    # 2. 테이블 존재 확인
    if not check_table_exists():
        return
    
    # 3. 전체 데이터 조회
    show_all_records()
    
    # 4. 현재 사용자 데이터 조회
    show_user_records()
    
    # 5. 상세 조회 옵션
    print("\n" + "=" * 50)
    print("💡 특정 레코드의 상세 정보를 보려면:")
    print("   python check_database.py --detail [레코드ID]")
    print("   예: python check_database.py --detail 1")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 2 and sys.argv[1] == "--detail":
        try:
            record_id = int(sys.argv[2])
            
            if check_database_connection() and check_table_exists():
                show_specific_record(record_id)
        except ValueError:
            print("❌ 올바른 레코드 ID를 입력하세요.")
    else:
        main() 