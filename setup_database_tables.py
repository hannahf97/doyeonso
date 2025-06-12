#!/usr/bin/env python3
"""
PostgreSQL 데이터베이스 테이블 생성 스크립트
김민주(13조) 요청에 따른 domyun 테이블 생성
"""

import psycopg2
from config.database_config import get_db_connection
from config.user_config import USER_NAME

def create_domyun_table():
    """domyun 테이블 생성"""
    
    # 테이블 생성 SQL (김민주님 요청 스펙)
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS domyun (
        d_id SERIAL PRIMARY KEY,                         -- 자동 증가
        d_name VARCHAR(255) NOT NULL,                    -- 도면명
        "user" VARCHAR(100) DEFAULT '김민주',            -- 작성자명 (디폴트)
        create_date DATE DEFAULT CURRENT_DATE,           -- 생성일 (오늘)
        json_data JSONB,                                 -- JSON 데이터
        image_path VARCHAR(500)                          -- 도면 이미지 경로
    );
    """
    
    # 인덱스 생성 SQL (성능 최적화)
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_domyun_d_name ON domyun(d_name);",
        "CREATE INDEX IF NOT EXISTS idx_domyun_user ON domyun(\"user\");",
        "CREATE INDEX IF NOT EXISTS idx_domyun_create_date ON domyun(create_date);",
        "CREATE INDEX IF NOT EXISTS idx_domyun_json_data ON domyun USING GIN(json_data);"
    ]
    
    try:
        # 데이터베이스 연결
        conn = get_db_connection()
        if not conn:
            print("❌ 데이터베이스 연결 실패")
            return False
        
        cursor = conn.cursor()
        
        print("🔧 domyun 테이블 생성 중...")
        
        # 테이블 생성
        cursor.execute(create_table_sql)
        print("✅ domyun 테이블 생성 완료")
        
        # 인덱스 생성
        print("🔧 인덱스 생성 중...")
        for idx_sql in create_indexes_sql:
            cursor.execute(idx_sql)
        print("✅ 인덱스 생성 완료")
        
        # 변경사항 커밋
        conn.commit()
        
        # 테이블 정보 확인
        cursor.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'domyun'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        print("\n📋 생성된 테이블 구조:")
        print("=" * 80)
        print(f"{'컬럼명':<15} {'데이터타입':<20} {'기본값':<25} {'NULL허용'}")
        print("=" * 80)
        
        for col in columns:
            col_name, data_type, default_val, nullable = col
            default_display = str(default_val)[:22] if default_val else 'None'
            print(f"{col_name:<15} {data_type:<20} {default_display:<25} {nullable}")
        
        print("=" * 80)
        
        # 연결 종료
        cursor.close()
        conn.close()
        
        print(f"\n🎉 데이터베이스 설정 완료!")
        print(f"👤 기본 사용자명: '김민주' (코드에서 '{USER_NAME}'로 실제 저장됨)")
        
        return True
        
    except Exception as e:
        print(f"❌ 테이블 생성 오류: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_table_compatibility():
    """기존 코드와 테이블 호환성 확인"""
    
    print("\n🔍 기존 코드와의 호환성 검사...")
    
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ 데이터베이스 연결 실패")
            return False
        
        cursor = conn.cursor()
        
        # 테스트 데이터 삽입 (기존 코드에서 사용하는 방식)
        test_insert_sql = """
        INSERT INTO domyun (d_name, "user", json_data, image_path)
        VALUES (%s, %s, %s, %s)
        RETURNING d_id, create_date;
        """
        
        test_data = (
            "테스트 도면.pdf",
            USER_NAME,
            '{"test": "data", "ocr_result": "샘플 텍스트"}',
            "uploads/uploaded_images/test_image.png"
        )
        
        cursor.execute(test_insert_sql, test_data)
        result = cursor.fetchone()
        
        if result:
            d_id, create_date = result
            print(f"✅ 테스트 데이터 삽입 성공")
            print(f"   - 생성된 ID: {d_id}")
            print(f"   - 생성일: {create_date}")
            print(f"   - 사용자: {USER_NAME}")
            
            # 데이터 조회 테스트
            cursor.execute("SELECT * FROM domyun WHERE d_id = %s", (d_id,))
            row = cursor.fetchone()
            
            if row:
                print("✅ 데이터 조회 테스트 성공")
                
                # 테스트 데이터 삭제
                cursor.execute("DELETE FROM domyun WHERE d_id = %s", (d_id,))
                print("✅ 테스트 데이터 정리 완료")
            
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ 모든 호환성 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"❌ 호환성 테스트 실패: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def show_existing_code_examples():
    """기존 코드에서 사용하는 방법 예시"""
    
    print("\n📝 기존 코드 사용 예시:")
    print("=" * 60)
    
    example_code = '''
# 1. 데이터 삽입 (utils/auto_processor.py 에서 사용)
from config.database_config import get_db_connection
from config.user_config import USER_NAME

conn = get_db_connection()
cursor = conn.cursor()

insert_query = """
INSERT INTO domyun (d_name, "user", create_date, json_data, image_path)
VALUES (%s, %s, %s, %s, %s)
RETURNING d_id;
"""

cursor.execute(insert_query, (
    "도면파일.pdf",           # d_name
    USER_NAME,               # user (설정파일에서)
    datetime.now(),          # create_date
    json.dumps(data),        # json_data (JSONB)
    "path/to/image.png"      # image_path
))

# 2. 데이터 조회 (pages/database_view.py 에서 사용)
cursor.execute("SELECT * FROM domyun ORDER BY create_date DESC")
results = cursor.fetchall()
'''
    
    print(example_code)
    print("=" * 60)

if __name__ == "__main__":
    print("🐻 도연소 - PostgreSQL 데이터베이스 설정")
    print("👤 요청자: 김민주(13조)")
    print("=" * 50)
    
    # 1. 테이블 생성
    if create_domyun_table():
        # 2. 호환성 확인
        if verify_table_compatibility():
            # 3. 사용 예시 표시
            show_existing_code_examples()
            
            print("\n🎯 설정 완료!")
            print("이제 Streamlit 앱에서 데이터베이스를 사용할 수 있습니다.")
        else:
            print("\n⚠️ 호환성 문제가 발견되었습니다.")
    else:
        print("\n❌ 테이블 생성에 실패했습니다.")
        print("데이터베이스 연결 설정을 확인해주세요.") 