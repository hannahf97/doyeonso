# 🔑 OpenAI API 키 설정 가이드

## 1. OpenAI API 키 발급

1. **OpenAI 홈페이지 방문**: https://platform.openai.com
2. **계정 생성/로그인**
3. **API Keys 페이지로 이동**: https://platform.openai.com/api-keys
4. **"Create new secret key" 클릭**
5. **키 이름 입력** (예: "RAG-PID-Chatbot")
6. **생성된 키 복사** (한 번만 표시되므로 안전하게 보관)

## 2. 환경변수 설정

### macOS/Linux (터미널)
```bash
# 임시 설정 (현재 세션만)
export OPENAI_API_KEY="your-api-key-here"

# 영구 설정 (~/.zshrc 또는 ~/.bashrc에 추가)
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Windows (Command Prompt)
```cmd
# 임시 설정
set OPENAI_API_KEY=your-api-key-here

# 영구 설정 (시스템 환경변수)
setx OPENAI_API_KEY "your-api-key-here"
```

## 3. 설정 확인

```bash
# 환경변수 확인
echo $OPENAI_API_KEY

# Python에서 확인
python3 -c "import os; print('API Key 설정됨' if os.getenv('OPENAI_API_KEY') else 'API Key 없음')"
```

## 4. RAG + OpenAI 챗봇 실행

```bash
# 환경변수 설정 후 실행
python3 rag_openai_chatbot.py
```

## 5. 비용 관리

- **GPT-4o-mini 사용**: 저렴한 모델 (기본 설정)
- **토큰 제한**: 1500 토큰으로 제한 설정
- **사용량 모니터링**: https://platform.openai.com/usage

## 6. 문제 해결

### API 키 오류
```
❌ OpenAI API 오류: Incorrect API key provided
```
→ API 키 재확인 및 환경변수 설정 점검

### 권한 오류  
```
❌ OpenAI API 오류: You exceeded your current quota
```
→ OpenAI 계정에 결제 정보 추가 필요

### 네트워크 오류
```
❌ OpenAI API 오류: Connection error
```
→ 인터넷 연결 확인

## 7. 안전 수칙

- ✅ API 키를 코드에 직접 입력하지 마세요
- ✅ 환경변수를 사용하여 안전하게 관리
- ✅ 사용량을 정기적으로 모니터링
- ✅ 불필요한 API 호출 방지

## 예시: 터미널에서 설정

```bash
# 1. API 키 설정
export OPENAI_API_KEY="sk-..."

# 2. 설정 확인
echo $OPENAI_API_KEY

# 3. 챗봇 실행
python3 rag_openai_chatbot.py
```

설정 완료 후 다음과 같은 대화가 가능합니다:

```
💬 질문: FT101은 무엇인가요?

🔍 관련 문서 검색 중...
📊 검색 결과: 3개 관련 문서 발견

🤖 P&ID 전문가 답변:
================================================================================
FT101은 Feed 유량 전송기(Flow Transmitter)입니다.

**핵심 역할:**
- 원료(Feed) 유량을 실시간으로 측정
- 측정값을 FC101 유량 제어기에 전달
- 전체 공정의 기준점 역할

**기술적 세부사항:**
- FC101과 함께 PI 제어 루프 구성
- FV101 제어밸브를 통해 유량 조절
- AC103, AC104 등 다른 제어기의 기준값으로 활용

**안전 고려사항:**
- 유량 급감 시 FC101에서 자동 경보 발생
- FV101 자동 차단으로 시약 과주입 방지

이는 전체 공정의 핵심 계측기기로, 정확한 보정과 정기 점검이 필요합니다.
================================================================================
``` 