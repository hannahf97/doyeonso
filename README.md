# 🐻 도연소 (DoyeonSo) - P&ID 전문가 도면 관리 시스템

통합 도면 관리 및 P&ID 전문가 AI 챗봇 시스템입니다.

## 🚀 빠른 시작

### 1. 환경 설정
```bash
pip install -r requirements.txt
```

### 2. 데이터베이스 설정 (PostgreSQL)
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

### 3. OpenAI API 키 설정
`.env` 파일 생성:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. 실행
```bash
streamlit run app.py
```

### 5. 초기 설정
- 첫 실행 시 RAG 시스템이 자동으로 초기화됩니다 (30-60초 소요)
- `state/state.pkl` 파일이 자동 생성되어 이후 실행 시 빠른 로딩이 가능합니다

## 📁 주요 파일 구조

```
doyeonso/
├── app.py                    # 메인 Streamlit 앱
├── pages/
│   ├── chat_bot.py          # P&ID 전문가 챗봇
│   ├── file_upload.py       # 파일 업로드 관리
│   ├── database_view.py     # 데이터베이스 뷰
│   └── preprocessing_analysis.py  # 전처리 분석
├── models/
│   └── chatbotModel.py      # 챗봇 모델 (RAG + OpenAI)
├── utils/
│   ├── rag_system_kiwi.py   # Kiwi 기반 RAG 시스템
│   ├── auto_processor.py    # 자동 처리
│   ├── file_upload_utils.py # 파일 업로드 유틸
│   └── naver_ocr.py        # OCR 처리
├── config/
│   ├── database_config.py   # 데이터베이스 설정
│   └── user_config.py       # 사용자 설정
├── data/
│   └── 공정 Description_글.pdf  # P&ID 문서
└── state/                   # 자동 생성 (캐시 파일)
    └── state.pkl           # RAG 임베딩 캐시
```

## 🔧 주요 기능

### 1. P&ID 전문가 챗봇
- **계측기기 분석**: FT, FC, FV, PT, PC, TT, TC, LT, LC, AT, AC 등
- **공정 안전 분석**: 비상정지, 인터록, 안전밸브 등
- **변경 분석 모드**: 도면 변경사항 영향도 분석
- **실시간 대화**: OpenAI GPT-4o-mini 기반 전문가 응답

### 2. 도면 관리 시스템
- **파일 업로드**: 도면 이미지 및 문서 업로드
- **OCR 처리**: Naver OCR API를 통한 텍스트 추출
- **데이터베이스 연동**: PostgreSQL 기반 도면 정보 관리
- **자동 처리**: 업로드된 파일 자동 분석 및 처리

### 3. RAG 시스템
- **한국어 최적화**: Kiwi 형태소 분석기 기반
- **의미적 청킹**: 200-400자 단위 지능형 분할
- **벡터 검색**: SentenceTransformer + 코사인 유사도
- **캐시 시스템**: pickle 기반 빠른 로딩

## 🎯 사용법

### 기본 질문 (챗봇)
```
"FT-101의 역할은 무엇인가요?"
"압력 조절 시스템에 대해 설명해주세요"
"이 공정의 안전장치는 어떻게 구성되어 있나요?"
```

### 변경 분석 (자동 감지)
```
"FT101과 FT102의 차이점은 무엇인가요?"
"기존 제어 방식 vs 새로운 제어 방식 비교"
"온도 센서를 교체할 때 고려사항은?"
```

### 도면 관리
1. 파일 업로드 페이지에서 도면 이미지 업로드
2. 자동 OCR 처리 및 텍스트 추출
3. 데이터베이스에 도면 정보 저장
4. 데이터베이스 뷰에서 등록된 도면 조회 및 관리

## 🔧 기술 스택

- **Frontend**: Streamlit
- **AI**: OpenAI GPT-4o-mini
- **RAG**: SentenceTransformer, FAISS
- **한국어 처리**: Kiwi 형태소 분석기
- **데이터베이스**: PostgreSQL
- **OCR**: Naver OCR API
- **벡터 DB**: Pickle 기반 캐시

## 📊 성능

- **첫 실행**: 30-60초 (RAG 시스템 구축)
- **이후 실행**: 1-2초 (캐시 로딩)
- **응답 시간**: 2-5초 (OpenAI API 호출)
- **정확도**: Kiwi 기반 한국어 P&ID 최적화

## ⚠️ 주의사항

- 이 시스템은 보조 도구이며, 중요한 안전 결정은 반드시 전문가와 상의하시기 바랍니다
- `state/` 디렉토리는 자동 생성되므로 Git에 포함되지 않습니다
- OpenAI API 키와 PostgreSQL 데이터베이스 설정이 필요합니다

## 🚀 배포

시스템은 자동으로 캐시를 생성하므로 별도의 벡터 데이터베이스 설정이 불필요합니다.
