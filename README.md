# 🐻 Doyeonso - 도면 관리 시스템

## PostgreSQL 테이블 생성

각자 로컬 PostgreSQL에 다음 테이블을 생성하세요:

```sql
CREATE TABLE domyun (
    d_id SERIAL PRIMARY KEY,                         -- 자동 증가
    d_name VARCHAR(255) NOT NULL,                    -- 도면명
    "user" VARCHAR(100) DEFAULT '김민주',            -- 작성자명 (디폴트)
    create_date DATE DEFAULT CURRENT_DATE,           -- 생성일 (오늘)
    json_data JSONB,                                 -- JSON 데이터
    image_path VARCHAR(500)                          -- 도면 이미지 경로
);
```

## 사용법

1. 로컬에 PostgreSQL 설치
2. PostgreSQL에 접속하여 위 테이블 생성
3. Python에서 psycopg2로 연결하여 사용
