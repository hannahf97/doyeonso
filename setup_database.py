#!/usr/bin/env python3
"""
PostgreSQL 데이터베이스 테이블 생성 스크립트
domyun 테이블을 생성합니다.
"""

import psycopg2
from config.database_config import get_db_connection
from config.user_config import USER_NAME

def create_domyun_table():
    """domyun 테이블 생성"""
    
    create_table_query = """
    CREATE TABLE IF NOT EXISTS domyun (
        d_id SERIAL PRIMARY KEY,              -- 자동증가, PK, NOT NULL
        d_name VARCHAR(255) NOT NULL,         -- 업로드한 파일명, NOT NULL
        "user" VARCHAR(100) DEFAULT '제로',    -- 고정값 (user는 예약어이므로 따옴표 필요)
        create_date TIMESTAMP DEFAULT NOW(),   -- 시분초까지 자동 저장
        json_data JSONB,                      -- 통합 JSON 전체 내용
        image_path VARCHAR(500)               -- 저장된 이미지 경로
    );
    """
    
    # 인덱스 생성 (검색 성능 향상)
    create_indexes_queries = [
        "CREATE INDEX IF NOT EXISTS idx_domyun_d_name ON domyun(d_name);",
        "CREATE INDEX IF NOT EXISTS idx_domyun_user ON domyun(\"user\");",
        "CREATE INDEX IF NOT EXISTS idx_domyun_create_date ON domyun(create_date);",
        "CREATE INDEX IF NOT EXISTS idx_domyun_json_data ON domyun USING GIN (json_data);"
    ]
    
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ 데이터베이스 연결 실패")
            return False
        
        cursor = conn.cursor()
        
        # 테이블 생성
        print("🔧 domyun 테이블 생성 중...")
        cursor.execute(create_table_query)
        
        # 인덱스 생성
        print("📊 인덱스 생성 중...")
        for index_query in create_indexes_queries:
            cursor.execute(index_query)
        
        conn.commit()
        print("✅ domyun 테이블과 인덱스가 성공적으로 생성되었습니다!")
        
        # 테이블 정보 확인
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'domyun'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\n📋 생성된 테이블 구조:")
        print("-" * 80)
        print(f"{'컬럼명':<15} {'데이터타입':<20} {'NULL허용':<10} {'기본값':<30}")
        print("-" * 80)
        
        for col in columns:
            column_name, data_type, is_nullable, column_default = col
            nullable = "YES" if is_nullable == "YES" else "NO"
            default_val = column_default or ""
            print(f"{column_name:<15} {data_type:<20} {nullable:<10} {default_val:<30}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def check_table_exists():
    """테이블 존재 여부 확인"""
    
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ 데이터베이스 연결 실패")
            return False
        
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'domyun'
            );
        """)
        
        exists = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return exists
        
    except Exception as e:
        print(f"❌ 테이블 확인 실패: {str(e)}")
        return False

def insert_test_data():
    """테스트 데이터 삽입"""
    
    test_data = {
        "source_filename": "test_sample.png",
        "created_at": "2025-01-11T10:00:00.000000",
        "width": 1684,
        "height": 1190,
        "ocr_data": {
            "label": "ocr",
            "version": "1.0",
            "extracted_text": "테스트 OCR 결과"
        },
        "detection_data": {
            "label": "detecting",
            "version": "1.0",
            "detections": []
        }
    }
    
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ 데이터베이스 연결 실패")
            return False
        
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO domyun (d_name, "user", json_data, image_path)
        VALUES (%s, %s, %s, %s)
        RETURNING d_id;
        """
        
        cursor.execute(insert_query, (
            "test_sample.png",
            USER_NAME,  # config/user_config.py 에서 설정한 사용자 이름 사용
            test_data,
            "uploads/uploaded_images/test_sample.png"
        ))
        
        d_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"✅ 테스트 데이터 삽입 완료 (ID: {d_id})")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 데이터 삽입 실패: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """메인 함수"""
    
    print("🚀 PostgreSQL 데이터베이스 설정 시작")
    print("=" * 50)
    
    # 1. 테이블 존재 여부 확인
    if check_table_exists():
        print("ℹ️  domyun 테이블이 이미 존재합니다.")
        
        response = input("기존 테이블을 유지하시겠습니까? (y/n): ")
        if response.lower() != 'y':
            print("작업을 취소합니다.")
            return
    else:
        # 2. 테이블 생성
        if not create_domyun_table():
            print("❌ 테이블 생성에 실패했습니다.")
            return
    
    # 3. 테스트 데이터 삽입 여부 확인
    response = input("테스트 데이터를 삽입하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        insert_test_data()
    
    print("\n🎉 데이터베이스 설정이 완료되었습니다!")
    print("이제 파일 업로드 시스템을 사용할 수 있습니다.")

if __name__ == "__main__":
    main() 