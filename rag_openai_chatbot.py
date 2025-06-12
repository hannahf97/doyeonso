#!/usr/bin/env python3
"""
RAG + OpenAI P&ID 전문가 챗봇
"""

import os
import pickle
import torch
from sentence_transformers import SentenceTransformer
from utils.rag_system_kiwi import RAGSystemWithKiwi
from openai import OpenAI
import json
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 임베딩 모델 초기화
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

STATE_PATH = "./state/"

def save_state(chunks, embeddings):
    """청크와 임베딩을 pickle로 저장"""
    os.makedirs(STATE_PATH, exist_ok=True)
    with open(os.path.join(STATE_PATH, "state.pkl"), "wb") as f:
        pickle.dump({"chunks": chunks, "embeddings": embeddings}, f)

def load_state():
    """저장된 청크와 임베딩을 pickle로 로드"""
    state_file = os.path.join(STATE_PATH, "state.pkl")
    if os.path.exists(state_file):
        with open(state_file, "rb") as f:
            data = pickle.load(f)
            return data["chunks"], data["embeddings"]
    return None, None

def create_embeddings(chunks):
    """청크들을 임베딩하여 텐서로 변환"""
    embeddings = embedder.encode(chunks, convert_to_tensor=True)
    return embeddings

def retrieve_relevant_chunks(query, chunks, embeddings, top_k=3):
    """RAG 검색 - 관련 청크 추출"""
    # 쿼리 임베딩 생성
    query_embedding = embedder.encode(query, convert_to_tensor=True)
    query_embedding = query_embedding / torch.norm(query_embedding)
    
    # 임베딩 정규화
    embeddings_norm = embeddings / torch.norm(embeddings, dim=1, keepdim=True)
    
    # 유사도 계산
    similarities = torch.matmul(embeddings_norm, query_embedding)
    
    # 상위 k개 추출
    top_k_indices = torch.topk(similarities, min(top_k, len(similarities))).indices.tolist()
    top_k_scores = torch.topk(similarities, min(top_k, len(similarities))).values.tolist()
    
    # 관련 청크와 점수 반환
    relevant_chunks = []
    for i, (idx, score) in enumerate(zip(top_k_indices, top_k_scores)):
        relevant_chunks.append({
            'content': chunks[idx],
            'score': score,
            'rank': i + 1
        })
    
    return relevant_chunks

def build_rag_context(relevant_chunks):
    """RAG 검색 결과를 컨텍스트로 구성"""
    context = ""
    for chunk in relevant_chunks:
        context += f"[참고자료 {chunk['rank']}] (유사도: {chunk['score']:.3f})\n"
        context += f"{chunk['content']}\n\n"
    return context.strip()

def create_pid_expert_prompt(user_question, rag_context):
    """P&ID 전문가 페르소나 프롬프트 생성"""
    
    persona = """당신은 20년 경력의 P&ID(Piping and Instrumentation Diagram) 전문 엔지니어입니다.

**전문 분야:**
- 화학공정 설계 및 제어시스템
- 계측기기 및 제어루프 분석
- 공정 안전 및 이상상황 대응
- P&ID 도면 해석 및 검토

**응답 스타일:**
- 기술적으로 정확하고 실무적인 조언 제공
- 안전을 최우선으로 고려
- 구체적인 계측기기 태그(FT, FC, PT 등) 언급
- 필요시 추가 검토사항 제안

**응답 구조:**
1. 핵심 답변 (간결하고 명확하게)
2. 기술적 세부사항 (관련 계측기기, 제어로직 등)
3. 안전 고려사항 (해당되는 경우)
4. 추가 권장사항 (필요한 경우)"""

    system_prompt = f"""{persona}

**참고 문서 정보:**
{rag_context}

위 참고 문서를 바탕으로 사용자의 질문에 전문적이고 실용적인 답변을 제공해주세요.
참고 문서에 없는 내용은 일반적인 P&ID 지식을 활용하되, 추측이 아닌 확실한 정보만 제공하세요."""

    return system_prompt

def ask_openai_with_rag(user_question, rag_context, model="gpt-4o-mini", temperature=0.3):
    """OpenAI API를 통해 RAG 기반 답변 생성"""
    
    try:
        system_prompt = create_pid_expert_prompt(user_question, rag_context)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            temperature=temperature,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"❌ OpenAI API 오류: {e}"

def setup_rag_system():
    """RAG 시스템 초기화"""
    print("🔧 RAG 시스템 초기화 중...")
    
    # 기존 상태 로드 시도
    chunks, embeddings = load_state()
    
    if chunks is None or embeddings is None:
        print("📄 새로운 벡터 데이터베이스 구축 중...")
        
        # PDF 로드 및 청킹
        pdf_path = "data/공정 Description_글.pdf"
        kiwi_rag = RAGSystemWithKiwi()
        documents = kiwi_rag.extract_text_from_pdf(pdf_path)
        
        if not documents:
            print("❌ PDF 문서 추출 실패")
            return None, None
        
        # 청킹
        chunks_metadata = kiwi_rag.chunk_documents_with_kiwi(documents)
        chunks = [chunk['content'] for chunk in chunks_metadata]
        
        # 임베딩 생성
        print("🔢 임베딩 생성 중...")
        embeddings = create_embeddings(chunks)
        
        # 상태 저장
        save_state(chunks, embeddings)
        print("💾 벡터 데이터베이스 저장 완료")
    else:
        print("📂 기존 벡터 데이터베이스 로드 완료")
    
    print(f"✅ RAG 시스템 준비 완료: {len(chunks)}개 청크, {embeddings.shape} 임베딩")
    return chunks, embeddings

def interactive_pid_chatbot():
    """P&ID 전문가 챗봇 인터페이스"""
    
    print("\n🤖 P&ID 전문가 챗봇 시작")
    print("=" * 80)
    print("안녕하세요! 저는 P&ID 전문가 AI입니다.")
    print("공정도면, 계측기기, 제어시스템에 대해 무엇이든 물어보세요!")
    print("종료하려면 'quit', 'exit', '종료'를 입력하세요.")
    print("-" * 80)
    
    # RAG 시스템 초기화
    chunks, embeddings = setup_rag_system()
    
    if chunks is None:
        print("❌ RAG 시스템 초기화 실패")
        return
    
    # 대화 기록
    conversation_history = []
    
    while True:
        try:
            # 사용자 입력
            user_question = input("\n💬 질문: ").strip()
            
            if user_question.lower() in ['quit', 'exit', '종료']:
                print("👋 P&ID 전문가 챗봇을 종료합니다. 안전한 하루 되세요!")
                break
            
            if not user_question:
                continue
            
            print("\n🔍 관련 문서 검색 중...")
            
            # RAG 검색
            relevant_chunks = retrieve_relevant_chunks(user_question, chunks, embeddings, top_k=3)
            rag_context = build_rag_context(relevant_chunks)
            
            # 검색 결과 미리보기
            print(f"📊 검색 결과: {len(relevant_chunks)}개 관련 문서 발견")
            for chunk in relevant_chunks:
                print(f"  • 유사도 {chunk['score']:.3f}: {chunk['content'][:50]}...")
            
            print("\n🤖 P&ID 전문가가 답변 생성 중...")
            
            # OpenAI 답변 생성
            ai_response = ask_openai_with_rag(user_question, rag_context)
            
            # 답변 출력
            print("\n" + "="*80)
            print("🔧 P&ID 전문가 답변:")
            print("-" * 80)
            print(ai_response)
            print("="*80)
            
            # 대화 기록 저장
            conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'question': user_question,
                'rag_chunks': len(relevant_chunks),
                'rag_scores': [chunk['score'] for chunk in relevant_chunks],
                'response': ai_response
            })
            
        except KeyboardInterrupt:
            print("\n\n👋 사용자에 의해 중단되었습니다.")
            break
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            continue
    
    # 대화 기록 저장
    if conversation_history:
        save_conversation_history(conversation_history)

def save_conversation_history(conversation_history):
    """대화 기록 저장"""
    try:
        os.makedirs("./logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"./logs/conversation_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(conversation_history, f, ensure_ascii=False, indent=2)
        
        print(f"\n📝 대화 기록 저장: {filename}")
        print(f"총 {len(conversation_history)}개의 질문-답변 저장됨")
    except Exception as e:
        print(f"❌ 대화 기록 저장 실패: {e}")

def test_rag_openai_integration():
    """RAG + OpenAI 통합 테스트"""
    
    print("🧪 RAG + OpenAI 통합 테스트")
    print("=" * 60)
    
    # RAG 시스템 초기화
    chunks, embeddings = setup_rag_system()
    
    if chunks is None:
        print("❌ RAG 시스템 초기화 실패")
        return
    
    # 테스트 질문들
    test_questions = [
        "FT101은 무엇이고 어떤 역할을 하나요?",
        "시약 주입 시스템의 제어 방식을 설명해주세요",
        "비상상황에서 어떤 안전장치가 작동하나요?",
        "온도 제어는 어떻게 이루어지나요?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 테스트 질문 {i}: {question}")
        print("-" * 40)
        
        # RAG 검색
        relevant_chunks = retrieve_relevant_chunks(question, chunks, embeddings, top_k=2)
        rag_context = build_rag_context(relevant_chunks)
        
        print(f"🔍 RAG 검색: {len(relevant_chunks)}개 관련 문서")
        
        # OpenAI 답변
        ai_response = ask_openai_with_rag(question, rag_context)
        
        print(f"🤖 AI 답변:\n{ai_response}")
        print("\n" + "="*60)

def main():
    """메인 함수"""
    
    print("🚀 RAG + OpenAI P&ID 전문가 챗봇")
    print("=" * 80)
    
    # OpenAI API 키 확인
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("다음 명령으로 설정하세요:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # 사용자 선택
    print("\n🔧 옵션:")
    print("1. 대화형 P&ID 챗봇 시작")
    print("2. RAG + OpenAI 통합 테스트")
    print("3. 종료")
    
    choice = input("\n선택하세요 (1-3): ").strip()
    
    try:
        if choice == "1":
            interactive_pid_chatbot()
        elif choice == "2":
            test_rag_openai_integration()
        elif choice == "3":
            print("👋 프로그램을 종료합니다.")
        else:
            print("❌ 잘못된 선택입니다. 대화형 챗봇을 시작합니다.")
            interactive_pid_chatbot()
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 