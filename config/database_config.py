import os
import psycopg2
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# PostgreSQL 설정 (각자 로컬 DB 사용)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'kimminju')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

def get_db_connection():
    """PostgreSQL 연결 반환"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def test_db_connection():
    """데이터베이스 연결 테스트"""
    conn = get_db_connection()
    if conn:
        conn.close()
        return True
    return False 