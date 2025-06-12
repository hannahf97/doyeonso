#!/usr/bin/env python3
"""
P&ID 전문가 챗봇 모델 - Streamlit 연동용
"""

import os
import pickle
import torch
from sentence_transformers import SentenceTransformer
from utils.rag_system_kiwi import RAGSystemWithKiwi
from openai import OpenAI
from loguru import logger
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class PIDExpertChatbot:
    """P&ID 도면 분석 전문가 챗봇"""
    
    def __init__(self):
        """챗봇 초기화"""
        
        # OpenAI 클라이언트 초기화
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)
        else:
            self.client = None
            logger.warning("OpenAI API 키가 설정되지 않았습니다.")
        
        # 임베딩 모델 초기화
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # RAG 시스템 초기화
        self.kiwi_rag = RAGSystemWithKiwi()
        
        # 벡터 데이터베이스 상태
        self.chunks = None
        self.embeddings = None
        
        # 대화 기록
        self.conversation_history = []
        
        # 상태 저장 경로
        self.STATE_PATH = "./state/"
        
        # 전문가 페르소나 정의
        self.expert_persona = """당신은 20년 경력의 P&ID(Piping and Instrumentation Diagram) 전문 엔지니어입니다.

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

    def save_state(self, chunks, embeddings):
        """청크와 임베딩을 pickle로 저장"""
        os.makedirs(self.STATE_PATH, exist_ok=True)
        try:
            with open(os.path.join(self.STATE_PATH, "state.pkl"), "wb") as f:
                pickle.dump({"chunks": chunks, "embeddings": embeddings}, f)
            logger.info("벡터 데이터베이스 저장 완료")
        except Exception as e:
            logger.error(f"상태 저장 실패: {e}")

    def load_state(self):
        """저장된 청크와 임베딩을 pickle로 로드"""
        state_file = os.path.join(self.STATE_PATH, "state.pkl")
        if os.path.exists(state_file):
            try:
                with open(state_file, "rb") as f:
                    data = pickle.load(f)
                    return data["chunks"], data["embeddings"]
            except Exception as e:
                logger.error(f"상태 로드 실패: {e}")
        return None, None

    def create_embeddings(self, chunks):
        """청크들을 임베딩하여 텐서로 변환"""
        embeddings = self.embedder.encode(chunks, convert_to_tensor=True)
        return embeddings

    def initialize_rag_system(self, pdf_path: str) -> bool:
        """RAG 시스템 초기화"""
        try:
            logger.info("RAG 시스템 초기화 중...")
            
            # 기존 상태 로드 시도
            chunks, embeddings = self.load_state()
            
            if chunks is None or embeddings is None:
                logger.info("새로운 벡터 데이터베이스 구축 중...")
                
                # PDF 로드 및 청킹
                if not os.path.exists(pdf_path):
                    logger.error(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
                    return False
                
                documents = self.kiwi_rag.extract_text_from_pdf(pdf_path)
                
                if not documents:
                    logger.error("PDF 문서 추출 실패")
                    return False
                
                # 청킹
                chunks_metadata = self.kiwi_rag.chunk_documents_with_kiwi(documents)
                chunks = [chunk['content'] for chunk in chunks_metadata]
                
                # 임베딩 생성
                logger.info("임베딩 생성 중...")
                embeddings = self.create_embeddings(chunks)
                
                # 상태 저장
                self.save_state(chunks, embeddings)
            else:
                logger.info("기존 벡터 데이터베이스 로드 완료")
            
            self.chunks = chunks
            self.embeddings = embeddings
            
            logger.info(f"RAG 시스템 준비 완료: {len(chunks)}개 청크, {embeddings.shape} 임베딩")
            return True
            
        except Exception as e:
            logger.error(f"RAG 시스템 초기화 실패: {e}")
            return False

    def retrieve_relevant_chunks(self, query, top_k=3):
        """RAG 검색 - 관련 청크 추출"""
        if self.chunks is None or self.embeddings is None:
            return []
        
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.embedder.encode(query, convert_to_tensor=True)
            query_embedding = query_embedding / torch.norm(query_embedding)
            
            # 임베딩 정규화
            embeddings_norm = self.embeddings / torch.norm(self.embeddings, dim=1, keepdim=True)
            
            # 유사도 계산
            similarities = torch.matmul(embeddings_norm, query_embedding)
            
            # 상위 k개 추출
            top_k_indices = torch.topk(similarities, min(top_k, len(similarities))).indices.tolist()
            top_k_scores = torch.topk(similarities, min(top_k, len(similarities))).values.tolist()
            
            # 관련 청크와 점수 반환
            relevant_chunks = []
            for i, (idx, score) in enumerate(zip(top_k_indices, top_k_scores)):
                relevant_chunks.append({
                    'content': self.chunks[idx],
                    'score': score,
                    'rank': i + 1,
                    'page': i + 1  # Streamlit 호환성을 위해 페이지 번호 추가
                })
            
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"RAG 검색 실패: {e}")
            return []

    def build_rag_context(self, relevant_chunks):
        """RAG 검색 결과를 컨텍스트로 구성"""
        context = ""
        for chunk in relevant_chunks:
            context += f"[참고자료 {chunk['rank']}] (유사도: {chunk['score']:.3f})\n"
            context += f"{chunk['content']}\n\n"
        return context.strip()

    def create_pid_expert_prompt(self, user_question, rag_context):
        """P&ID 전문가 페르소나 프롬프트 생성"""
        
        system_prompt = f"""{self.expert_persona}

**참고 문서 정보:**
{rag_context}

위 참고 문서를 바탕으로 사용자의 질문에 전문적이고 실용적인 답변을 제공해주세요.
참고 문서에 없는 내용은 일반적인 P&ID 지식을 활용하되, 추측이 아닌 확실한 정보만 제공하세요."""

        return system_prompt

    def _detect_query_type(self, query: str) -> str:
        """쿼리 유형 감지 - 변경 분석 강화"""
        
        # 변경/비교 관련 키워드 (더 정확한 감지)
        change_keywords = [
            '변경', '차이', '비교', '수정', '개선', '업데이트', '바뀐', '달라진',
            '이전', '기존', '원래', '새로운', '변화', '다른점', '차이점',
            '개정', '수정사항', '변경사항', '업그레이드', '교체', '교환',
            '전후', '변동', '조정', '개량', '개선사항'
        ]
        
        # 비교 표현 패턴
        comparison_patterns = [
            r'vs|versus',  # A vs B
            r'와\s*비교',  # A와 비교
            r'과\s*비교',  # A과 비교
            r'대비',       # A 대비 B
            r'에서\s*.*로',  # A에서 B로
            r'기존.*새로운',  # 기존 A 새로운 B
            r'이전.*현재',   # 이전 A 현재 B
        ]
        
        safety_keywords = ['안전', '위험', '비상', '정지', '보호', '알람', 'ESD', 'SIS', '인터록']
        instrument_keywords = ['FT', 'FC', 'FV', 'PT', 'PC', 'TT', 'TC', 'LT', 'LC', 'AT', 'AC', '계측기', '트랜스미터', '조절기']
        
        query_lower = query.lower()
        
        # 변경/비교 키워드 우선 확인
        if any(keyword in query for keyword in change_keywords):
            return "change_analysis"
        
        # 비교 패턴 확인
        import re
        for pattern in comparison_patterns:
            if re.search(pattern, query):
                return "change_analysis"
        
        # 기타 분류
        if any(keyword in query for keyword in safety_keywords):
            return "safety_analysis"
        elif any(keyword in query for keyword in instrument_keywords):
            return "instrument_explanation"
        else:
            return "general"

    def create_change_analysis_prompt(self, user_question, rag_context):
        """변경 분석 전용 프롬프트 생성"""
        
        change_expert_persona = """당신은 20년 경력의 P&ID 변경 관리 전문가입니다.

**전문 분야:**
- P&ID 도면 변경사항 분석 및 검토
- 공정 개선 및 설비 교체 영향 분석
- 변경 전후 비교 분석
- 변경사항의 안전성 및 운전성 평가

**변경 분석 접근법:**
1. **변경 사항 식별**: 정확히 무엇이 변경되었는지 파악
2. **영향도 분석**: 변경이 주변 시스템에 미치는 영향
3. **안전성 검토**: 변경으로 인한 안전 리스크 평가
4. **운전성 검토**: 운전 절차 및 유지보수에 미치는 영향
5. **권장사항**: 변경 시 고려해야 할 추가 사항

**답변 구조:**
1. **변경사항 요약** (무엇이 어떻게 바뀌었는지)
2. **기술적 영향 분석** (시스템에 미치는 영향)
3. **안전성 검토** (안전 관련 고려사항)
4. **운전 및 유지보수 영향** (실무적 고려사항)
5. **권장사항 및 주의사항** (추가 검토 필요 사항)"""

        system_prompt = f"""{change_expert_persona}

**참고 문서 정보:**
{rag_context}

사용자가 P&ID 변경 또는 비교에 대해 질문했습니다. 변경 관리 전문가로서 다음 사항을 중점적으로 분석해주세요:

- 변경사항의 구체적 내용과 범위
- 연관 시스템에 미치는 영향
- 안전성 및 운전성 관점에서의 검토
- 변경 시 추가 고려해야 할 사항

위 참고 문서를 바탕으로 전문적이고 체계적인 변경 분석을 제공해주세요."""

        return system_prompt

    def retrieve_change_analysis_chunks(self, query, top_k=5):
        """변경 분석을 위한 확장된 검색"""
        if self.chunks is None or self.embeddings is None:
            return []
        
        try:
            # 기본 검색
            basic_chunks = self.retrieve_relevant_chunks(query, top_k=3)
            
            # 변경 관련 키워드로 추가 검색
            change_terms = ['변경', '수정', '개선', '교체', '업그레이드', '조정']
            additional_chunks = []
            
            for term in change_terms:
                if term not in query:  # 이미 포함된 용어는 제외
                    expanded_query = f"{query} {term}"
                    extra_chunks = self.retrieve_relevant_chunks(expanded_query, top_k=2)
                    additional_chunks.extend(extra_chunks)
            
            # 중복 제거 및 통합
            all_chunks = basic_chunks + additional_chunks
            seen_contents = set()
            unique_chunks = []
            
            for chunk in all_chunks:
                if chunk['content'] not in seen_contents:
                    seen_contents.add(chunk['content'])
                    unique_chunks.append(chunk)
            
            # 상위 top_k개 반환
            return unique_chunks[:top_k]
            
        except Exception as e:
            logger.error(f"변경 분석 검색 실패: {e}")
            return self.retrieve_relevant_chunks(query, top_k)

    def generate_response(self, user_query: str, use_web_search: bool = False) -> Dict:
        """챗봇 응답 생성 - 변경 분석 분기 처리"""
        try:
            # 쿼리 유형 감지
            query_type = self._detect_query_type(user_query)
            
            # 변경 분석인 경우 특별 처리
            if query_type == "change_analysis":
                logger.info(f"🔄 변경 분석 모드로 처리: {user_query}")
                
                # 확장된 검색 수행
                relevant_chunks = self.retrieve_change_analysis_chunks(user_query, top_k=5)
                rag_context = self.build_rag_context(relevant_chunks)
                
                # 변경 분석 전용 프롬프트 사용
                system_prompt = self.create_change_analysis_prompt(user_query, rag_context)
                
                # 더 긴 응답을 위해 max_tokens 증가
                max_tokens = 2000
                temperature = 0.2  # 더 일관된 분석을 위해 낮은 temperature
                
            else:
                # 기존 방식으로 처리
                relevant_chunks = self.retrieve_relevant_chunks(user_query, top_k=3)
                rag_context = self.build_rag_context(relevant_chunks)
                system_prompt = self.create_pid_expert_prompt(user_query, rag_context)
                max_tokens = 1500
                temperature = 0.3
            
            # 컨텍스트 품질 확인
            context_quality = "high" if len(rag_context) > 100 else "low"
            
            # OpenAI API 호출
            if not self.client:
                return {
                    'response': "OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.",
                    'sources': [],
                    'query_type': query_type,
                    'context_quality': context_quality,
                    'web_search_used': False
                }
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_query}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                ai_response = response.choices[0].message.content
                
                # 변경 분석인 경우 응답에 특별 표시 추가
                if query_type == "change_analysis":
                    ai_response = "🔄 **변경 분석 모드**\n\n" + ai_response
                
            except Exception as e:
                logger.error(f"OpenAI API 호출 실패: {e}")
                ai_response = f"OpenAI API 오류: {e}"
            
            # 소스 정보 생성 (Streamlit 호환)
            sources = []
            for chunk in relevant_chunks:
                sources.append({
                    'page': chunk['page'],
                    'score': chunk['score'],
                    'content_preview': chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content']
                })
            
            # 대화 기록 저장
            self.conversation_history.append({
                'timestamp': datetime.now(),
                'user_query': user_query,
                'response': ai_response,
                'query_type': query_type,
                'context_quality': context_quality,
                'sources_count': len(sources)
            })
            
            return {
                'response': ai_response,
                'sources': sources,
                'query_type': query_type,
                'context_quality': context_quality,
                'web_search_used': use_web_search
            }
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {e}")
            return {
                'response': f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}",
                'sources': [],
                'query_type': 'error',
                'context_quality': 'none',
                'web_search_used': False
            }

    def get_conversation_summary(self) -> Dict:
        """대화 요약 통계"""
        if not self.conversation_history:
            return {}
        
        total_queries = len(self.conversation_history)
        query_types = {}
        context_qualities = {}
        
        for conv in self.conversation_history:
            query_type = conv.get('query_type', 'unknown')
            context_quality = conv.get('context_quality', 'unknown')
            
            query_types[query_type] = query_types.get(query_type, 0) + 1
            context_qualities[context_quality] = context_qualities.get(context_quality, 0) + 1
        
        return {
            'total_queries': total_queries,
            'query_types': query_types,
            'context_qualities': context_qualities,
            'average_sources_per_query': sum(conv.get('sources_count', 0) for conv in self.conversation_history) / total_queries
        }

    def clear_conversation_history(self):
        """대화 기록 삭제"""
        self.conversation_history = []
        logger.info("대화 기록이 삭제되었습니다.")

    def export_conversation_history(self) -> str:
        """대화 기록 내보내기"""
        if not self.conversation_history:
            return "대화 기록이 없습니다."
        
        export_text = "P&ID 전문가 챗봇 대화 기록\n"
        export_text += "=" * 50 + "\n\n"
        
        for i, conv in enumerate(self.conversation_history, 1):
            export_text += f"대화 {i}\n"
            export_text += f"시간: {conv['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            export_text += f"질문: {conv['user_query']}\n"
            export_text += f"답변: {conv['response']}\n"
            export_text += f"쿼리 유형: {conv['query_type']}\n"
            export_text += f"컨텍스트 품질: {conv['context_quality']}\n"
            export_text += "-" * 30 + "\n\n"
        
        return export_text 