#!/usr/bin/env python3
"""
최적화된 임베딩 및 검색 시스템
"""

import torch
import numpy as np
import os
import pickle
from sentence_transformers import SentenceTransformer
from utils.rag_system_kiwi import RAGSystemWithKiwi

# 사용자 제공 코드 기반
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

STATE_PATH = "./state/"

def save_state(chunks, embeddings):
    """청크와 임베딩을 pickle로 저장"""
    os.makedirs(STATE_PATH, exist_ok=True)  # state 디렉토리 생성
    with open(os.path.join(STATE_PATH, "state.pkl"), "wb") as f:  # 'state.pkl' 파일을 쓰기 모드로 엽니다.
        pickle.dump({"chunks": chunks, "embeddings": embeddings}, f)  # 청크와 임베딩을 파일에 저장합니다.
    print(f"💾 상태 저장 완료: {STATE_PATH}state.pkl")

def load_state():
    """저장된 청크와 임베딩을 pickle로 로드"""
    state_file = os.path.join(STATE_PATH, "state.pkl")
    if os.path.exists(state_file):
        with open(state_file, "rb") as f:
            data = pickle.load(f)
            print(f"📂 상태 로드 완료: {len(data['chunks'])}개 청크, {data['embeddings'].shape} 임베딩")
            return data["chunks"], data["embeddings"]
    else:
        print(f"❌ 저장된 상태 파일이 없습니다: {state_file}")
        return None, None

def create_embeddings(chunks):
    """청크들을 임베딩하여 텐서로 변환합니다."""
    embeddings = embedder.encode(chunks, convert_to_tensor=True)  # 청크들을 임베딩하여 텐서로 변환합니다.
    return embeddings  # 임베딩된 벡터들을 반환합니다.

def create_normalized_embeddings(chunks):
    """정규화된 임베딩 생성 (코사인 유사도 최적화)"""
    embeddings = create_embeddings(chunks)
    # L2 정규화로 코사인 유사도 계산 최적화
    normalized_embeddings = embeddings / torch.norm(embeddings, dim=1, keepdim=True)
    return normalized_embeddings

def retrieve_relevant_chunks(query, chunks, embeddings, top_k=5):
    """
    사용자 요구사항에 따른 검색 함수
    """
    # 쿼리 임베딩 생성
    query_embedding = embedder.encode(query, convert_to_tensor=True)
    query_embedding = query_embedding / torch.norm(query_embedding)
    
    # 임베딩 정규화 (이미 정규화된 경우 생략 가능)
    embeddings = embeddings / torch.norm(embeddings, dim=1, keepdim=True)
    
    # 유사도 계산
    similarities = torch.matmul(embeddings, query_embedding.T).squeeze()
    
    # 상위 k개 추출
    top_k_indices = torch.topk(similarities, top_k).indices.tolist()
    
    # 관련 청크 반환
    relevant_chunks = [chunks[i] for i in top_k_indices]
    
    return '\n\n'.join(relevant_chunks)

def build_complete_vector_db():
    """완전한 벡터 데이터베이스 구축 (pickle 저장/로드 지원)"""
    
    print("🏗️ 완전한 벡터 데이터베이스 구축")
    print("=" * 60)
    
    # 기존 상태 확인 및 로드 시도
    chunks, embeddings = load_state()
    
    if chunks is not None and embeddings is not None:
        print("✅ 기존 저장된 상태를 사용합니다!")
        return chunks, embeddings, None
    
    # 새로 구축하는 경우
    print("🔄 새로운 벡터 데이터베이스를 구축합니다...")
    
    # PDF 로드
    pdf_path = "data/공정 Description_글.pdf"
    
    # Kiwi 시스템 사용 (더 나은 청킹)
    kiwi_rag = RAGSystemWithKiwi()
    documents = kiwi_rag.extract_text_from_pdf(pdf_path)
    
    if not documents:
        print("❌ PDF 문서 추출 실패")
        return None, None, None
    
    # 청킹
    chunks_metadata = kiwi_rag.chunk_documents_with_kiwi(documents)
    chunk_texts = [chunk['content'] for chunk in chunks_metadata]
    
    print(f"📄 청킹 완료: {len(chunk_texts)}개 청크")
    
    # 임베딩 생성
    print("🔢 임베딩 생성 중...")
    embeddings = create_normalized_embeddings(chunk_texts)
    
    # 상태 저장
    save_state(chunk_texts, embeddings)
    
    print(f"✅ 벡터 DB 구축 완료:")
    print(f"  - 청크 수: {len(chunk_texts)}")
    print(f"  - 임베딩 shape: {embeddings.shape}")
    print(f"  - 메모리 사용량: {embeddings.element_size() * embeddings.nelement() / 1024 / 1024:.2f} MB")
    
    return chunk_texts, embeddings, chunks_metadata

def interactive_search(chunks, embeddings):
    """대화형 검색 인터페이스"""
    
    print("\n🔍 대화형 P&ID 검색 시스템")
    print("=" * 60)
    print("질문을 입력하세요 (종료: 'quit' 또는 'exit')")
    
    while True:
        query = input("\n💬 질문: ").strip()
        
        if query.lower() in ['quit', 'exit', '종료']:
            print("👋 검색 시스템을 종료합니다.")
            break
        
        if not query:
            continue
        
        try:
            # 검색 수행
            result = retrieve_relevant_chunks(query, chunks, embeddings, top_k=3)
            
            print(f"\n📋 검색 결과:")
            print("-" * 40)
            print(result)
            
            # 유사도 점수도 표시
            query_embedding = embedder.encode(query, convert_to_tensor=True)
            query_embedding = query_embedding / torch.norm(query_embedding)
            similarities = torch.matmul(embeddings, query_embedding.T).squeeze()
            top_3_similarities = torch.topk(similarities, 3).values.tolist()
            
            print(f"\n📊 유사도 점수: {[f'{s:.3f}' for s in top_3_similarities]}")
            
        except Exception as e:
            print(f"❌ 검색 오류: {e}")

def benchmark_search_performance(chunks, embeddings):
    """검색 성능 벤치마크"""
    
    print("\n⚡ 검색 성능 벤치마크")
    print("=" * 60)
    
    import time
    
    test_queries = [
        "FT101은 무엇인가요?",
        "시약 주입 방법",
        "비상상황 대응절차",
        "유량 제어 시스템",
        "온도 측정 방법",
        "압력 제어 방식",
        "안전장치 작동원리",
        "배관 설계 특징",
        "제어루프 구성",
        "계측기기 종류"
    ]
    
    print(f"🔍 {len(test_queries)}개 쿼리로 성능 테스트")
    
    # 성능 측정
    start_time = time.time()
    
    for i, query in enumerate(test_queries, 1):
        result = retrieve_relevant_chunks(query, chunks, embeddings, top_k=3)
        print(f"  쿼리 {i:2d}: {len(result)}자 결과 반환")
    
    end_time = time.time()
    
    total_time = end_time - start_time
    avg_time = total_time / len(test_queries)
    
    print(f"\n📊 성능 결과:")
    print(f"  - 총 시간: {total_time:.2f}초")
    print(f"  - 평균 시간: {avg_time:.3f}초/쿼리")
    print(f"  - 처리량: {1/avg_time:.1f} 쿼리/초")

def clear_state():
    """저장된 상태 파일 삭제"""
    state_file = os.path.join(STATE_PATH, "state.pkl")
    if os.path.exists(state_file):
        os.remove(state_file)
        print(f"🗑️ 상태 파일 삭제 완료: {state_file}")
    else:
        print(f"❌ 삭제할 상태 파일이 없습니다: {state_file}")

def get_state_info():
    """저장된 상태 파일 정보 확인"""
    state_file = os.path.join(STATE_PATH, "state.pkl")
    if os.path.exists(state_file):
        file_size = os.path.getsize(state_file)
        file_size_mb = file_size / 1024 / 1024
        print(f"📊 상태 파일 정보:")
        print(f"  - 파일 경로: {state_file}")
        print(f"  - 파일 크기: {file_size_mb:.2f} MB")
        
        # 간단한 내용 확인
        try:
            with open(state_file, "rb") as f:
                data = pickle.load(f)
                print(f"  - 청크 수: {len(data['chunks'])}")
                print(f"  - 임베딩 shape: {data['embeddings'].shape}")
                print(f"  - 임베딩 타입: {type(data['embeddings'])}")
        except Exception as e:
            print(f"  - 파일 읽기 오류: {e}")
    else:
        print(f"❌ 상태 파일이 없습니다: {state_file}")

def main():
    """메인 실행 함수"""
    
    print("🚀 최적화된 P&ID 임베딩 및 검색 시스템")
    print("=" * 80)
    
    # 상태 정보 확인
    get_state_info()
    
    # 사용자 옵션
    print("\n🔧 옵션:")
    print("1. 벡터 DB 구축 및 검색 시작")
    print("2. 상태 파일 삭제 후 새로 구축")
    print("3. 종료")
    
    choice = input("\n선택하세요 (1-3): ").strip()
    
    if choice == "2":
        clear_state()
        print("새로운 벡터 DB를 구축합니다...")
    elif choice == "3":
        print("👋 프로그램을 종료합니다.")
        return
    elif choice != "1":
        print("기본값으로 벡터 DB 구축을 시작합니다...")
    
    try:
        # 벡터 데이터베이스 구축
        chunks, embeddings, metadata = build_complete_vector_db()
        
        if chunks is None:
            return
        
        # 성능 벤치마크
        benchmark_search_performance(chunks, embeddings)
        
        # 대화형 검색 시작
        interactive_search(chunks, embeddings)
        
    except KeyboardInterrupt:
        print("\n\n👋 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 