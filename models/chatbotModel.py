#!/usr/bin/env python3
"""
P&ID 전문가 챗봇 모델 - Streamlit 연동용
"""

import os
import pickle
import torch
import json
from sentence_transformers import SentenceTransformer
from utils.rag_system_kiwi import RAGSystemWithKiwi
from openai import OpenAI
from loguru import logger
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
from config.database_config import get_db_connection
# 이미지 처리를 위한 import 추가
from PIL import Image, ImageDraw, ImageFont
import io
import base64

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
        """쿼리 유형 감지 - 도면 검색 기능 추가"""
        
        # 도면 시각화 관련 키워드 확인
        visualization_keywords = [
            '분석해줘', '시각화', '그려줘', '보여줘', '표시해줘', 
            'ocr', 'detection', '바운딩', '박스', '네모'
        ]
        
        # 도면 검색 관련 키워드 확인
        drawing_search_keywords = [
            '도면', '파일', '그림', 'pdf', 'stream', 'does', 'ai',
            '찾아', '검색', '보여', '알려', '어디', '있나', '무엇'
        ]
        
        # 내부/기밀 데이터 관련 키워드 (웹 검색 금지)
        internal_keywords = [
            '공정', '시스템', '요약', '분석', '도면', '설계', '운전', '제어',
            '프로세스', '설비',
            '절차', '매뉴얼', '사양', '규격'
        ]
        
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
        
        # 도면 시각화 키워드 우선 확인 (도면명과 함께 사용된 경우)
        has_drawing_ref = any(keyword in query for keyword in drawing_search_keywords)
        has_viz_request = any(keyword in query for keyword in visualization_keywords)
        
        if has_drawing_ref and has_viz_request:
            # 도면 이름 후보가 있는지 확인
            drawing_candidates = self.extract_drawing_names_from_query(query)
            if drawing_candidates:
                return "drawing_visualization"
        
        # 도면 검색 키워드 확인
        if any(keyword in query for keyword in drawing_search_keywords):
            # 도면 이름 후보가 있는지 확인
            drawing_candidates = self.extract_drawing_names_from_query(query)
            if drawing_candidates:
                return "drawing_search"
        
        # 내부 데이터 키워드 확인 (웹 검색 금지)
        if any(keyword in query for keyword in internal_keywords):
            return "internal_data"
        
        # 변경/비교 키워드 확인
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
        """변경 분석 전용 프롬프트 생성 - 데이터베이스 도면 데이터 포함"""
        
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

        # 사용자 질문에서 파일명 추출 시도
        drawing_context = ""
        
        try:
            # 질문에서 파일명 패턴 찾기
            import re
            
            # 파일명 패턴들 (확장자 포함)
            file_patterns = [
                r'([a-zA-Z0-9가-힣_\-\.]+\.(?:pdf|png|jpg|jpeg))',  # 확장자 포함
                r'([a-zA-Z0-9가-힣_\-\.]+)\s*(?:파일|도면|문서)',    # 파일/도면/문서 키워드
                r'"([^"]+)"',  # 따옴표로 감싼 파일명
                r"'([^']+)'"   # 작은따옴표로 감싼 파일명
            ]
            
            detected_filename = None
            for pattern in file_patterns:
                matches = re.findall(pattern, user_question, re.IGNORECASE)
                if matches:
                    detected_filename = matches[0]
                    break
            
            if detected_filename:
                logger.info(f"질문에서 파일명 감지: {detected_filename}")
                
                # 변경 관련 키워드 확인
                change_keywords = ['변경', '수정', '개선', '교체', '업그레이드', '조정', '비교', '차이', '전후']
                version_keywords = {
                    'latest': ['최신', '새로운', '현재', '업데이트된', '신규'],
                    'previous': ['이전', '과거', '원래', '기존', '옛날']
                }
                
                is_change_analysis = any(keyword in user_question for keyword in change_keywords)
                
                if is_change_analysis:
                    # 최신 버전과 이전 버전 모두 조회
                    latest_data = self.get_drawing_data_from_db(detected_filename, "latest")
                    previous_data = self.get_drawing_data_from_db(detected_filename, "previous")
                    
                    if latest_data or previous_data:
                        drawing_context = "\n\n=== 데이터베이스에서 조회된 도면 정보 ===\n"
                        
                        if latest_data:
                            drawing_context += self.build_drawing_context(latest_data, "최신")
                            drawing_context += "\n\n"
                        
                        if previous_data:
                            drawing_context += self.build_drawing_context(previous_data, "이전")
                            drawing_context += "\n\n"
                        
                        # 비교 분석을 위한 추가 정보
                        if latest_data and previous_data:
                            drawing_context += "=== 버전 비교 정보 ===\n"
                            drawing_context += f"최신 버전 등록일: {latest_data.get('create_date')}\n"
                            drawing_context += f"이전 버전 등록일: {previous_data.get('create_date')}\n"
                            
                            # 텍스트 변경 분석
                            latest_text = self.extract_text_from_drawing_data(latest_data)
                            previous_text = self.extract_text_from_drawing_data(previous_data)
                            
                            if latest_text != previous_text:
                                drawing_context += "⚠️ 도면 텍스트 내용에 변경사항이 감지되었습니다.\n"
                            else:
                                drawing_context += "ℹ️ 도면 텍스트 내용에는 변경사항이 없습니다.\n"
                    else:
                        drawing_context += f"\n\n⚠️ '{detected_filename}' 파일을 데이터베이스에서 찾을 수 없습니다.\n"
                
                else:
                    # 변경 분석이 아닌 경우 특정 버전 요청 확인
                    requested_version = "latest"  # 기본값
                    
                    for version, keywords in version_keywords.items():
                        if any(keyword in user_question for keyword in keywords):
                            requested_version = version
                            break
                    
                    drawing_data = self.get_drawing_data_from_db(detected_filename, requested_version)
                    
                    if drawing_data:
                        version_label = "최신" if requested_version == "latest" else "이전"
                        drawing_context = "\n\n=== 데이터베이스에서 조회된 도면 정보 ===\n"
                        drawing_context += self.build_drawing_context(drawing_data, version_label)
                    else:
                        drawing_context += f"\n\n⚠️ '{detected_filename}' ({requested_version})을 데이터베이스에서 찾을 수 없습니다.\n"
            
        except Exception as e:
            logger.error(f"데이터베이스 조회 중 오류: {e}")
            drawing_context = "\n\n⚠️ 데이터베이스 조회 중 오류가 발생했습니다.\n"

        # 전체 프롬프트 구성
        system_prompt = f"""{change_expert_persona}

**참고 문서 정보:**
{rag_context}

**도면 데이터베이스 정보:**
{drawing_context}

사용자가 P&ID 변경 또는 비교에 대해 질문했습니다. 변경 관리 전문가로서 다음 사항을 중점적으로 분석해주세요:

- 변경사항의 구체적 내용과 범위
- 연관 시스템에 미치는 영향
- 안전성 및 운전성 관점에서의 검토
- 변경 시 추가 고려해야 할 사항

위 참고 문서와 데이터베이스에서 조회된 도면 정보를 바탕으로 전문적이고 체계적인 변경 분석을 제공해주세요.

파일명이 감지되었다면 해당 도면의 실제 데이터를 우선적으로 참고하여 답변하세요."""

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

    def get_drawing_data_from_db(self, d_name: str, version: str = "latest") -> Optional[Dict]:
        """
        데이터베이스에서 도면 데이터를 조회
        
        Args:
            d_name: 도면 파일명
            version: "latest" (최신) 또는 "previous" (이전)
        
        Returns:
            도면 데이터 또는 None
        """
        try:
            conn = get_db_connection()
            if not conn:
                logger.error("데이터베이스 연결 실패")
                return None
            
            cursor = conn.cursor()
            
            if version == "latest":
                # 최신 파일 (create_date가 가장 늦은 것)
                query = """
                SELECT d_id, d_name, "user", create_date, json_data, image_path
                FROM domyun 
                WHERE d_name = %s 
                ORDER BY create_date DESC 
                LIMIT 1
                """
            else:  # previous
                # 이전 파일 (create_date가 두 번째로 늦은 것)
                query = """
                SELECT d_id, d_name, "user", create_date, json_data, image_path
                FROM domyun 
                WHERE d_name = %s 
                ORDER BY create_date DESC 
                LIMIT 1 OFFSET 1
                """
            
            cursor.execute(query, (d_name,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                d_id, d_name, user, create_date, json_data, image_path = result
                return {
                    'd_id': d_id,
                    'd_name': d_name,
                    'user': user,
                    'create_date': create_date,
                    'json_data': json_data,
                    'image_path': image_path
                }
            else:
                logger.warning(f"도면 '{d_name}' ({version})을 찾을 수 없습니다")
                return None
                
        except Exception as e:
            logger.error(f"데이터베이스 조회 실패: {e}")
            return None

    def get_all_versions_of_drawing(self, d_name: str) -> List[Dict]:
        """
        특정 도면의 모든 버전을 조회
        
        Args:
            d_name: 도면 파일명
        
        Returns:
            모든 버전의 도면 데이터 리스트 (최신순)
        """
        try:
            conn = get_db_connection()
            if not conn:
                logger.error("데이터베이스 연결 실패")
                return []
            
            cursor = conn.cursor()
            
            query = """
            SELECT d_id, d_name, "user", create_date, json_data, image_path
            FROM domyun 
            WHERE d_name = %s 
            ORDER BY create_date DESC
            """
            
            cursor.execute(query, (d_name,))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            versions = []
            for result in results:
                d_id, d_name, user, create_date, json_data, image_path = result
                versions.append({
                    'd_id': d_id,
                    'd_name': d_name,
                    'user': user,
                    'create_date': create_date,
                    'json_data': json_data,
                    'image_path': image_path
                })
            
            return versions
                
        except Exception as e:
            logger.error(f"데이터베이스 조회 실패: {e}")
            return []

    def extract_text_from_drawing_data(self, drawing_data: Dict) -> str:
        """
        도면 데이터에서 텍스트를 추출
        
        Args:
            drawing_data: 데이터베이스에서 가져온 도면 데이터
        
        Returns:
            추출된 텍스트
        """
        if not drawing_data or not drawing_data.get('json_data'):
            return ""
        
        try:
            json_data = drawing_data['json_data']
            extracted_texts = []
            
            # OCR 데이터에서 텍스트 추출
            if 'ocr_data' in json_data and json_data['ocr_data']:
                ocr_data = json_data['ocr_data']
                if 'images' in ocr_data:
                    for image in ocr_data['images']:
                        if 'fields' in image:
                            for field in image['fields']:
                                if 'inferText' in field:
                                    extracted_texts.append(field['inferText'])
            
            # Detection 데이터에서 텍스트 추출 (있다면)
            if 'detection_data' in json_data and json_data['detection_data']:
                detection_data = json_data['detection_data']
                if 'detections' in detection_data:
                    for detection in detection_data['detections']:
                        if 'text' in detection:
                            extracted_texts.append(detection['text'])
            
            return '\n'.join(extracted_texts)
            
        except Exception as e:
            logger.error(f"텍스트 추출 실패: {e}")
            return ""

    def build_drawing_context(self, drawing_data: Dict, version_label: str = "") -> str:
        """
        도면 데이터를 컨텍스트 문자열로 구성
        
        Args:
            drawing_data: 도면 데이터
            version_label: 버전 라벨 (예: "최신", "이전")
        
        Returns:
            구성된 컨텍스트 문자열
        """
        if not drawing_data:
            return ""
        
        context_parts = []
        
        # 도면 기본 정보
        context_parts.append(f"=== {version_label} 도면 정보 ===")
        context_parts.append(f"파일명: {drawing_data.get('d_name', 'N/A')}")
        context_parts.append(f"등록일: {drawing_data.get('create_date', 'N/A')}")
        context_parts.append(f"등록자: {drawing_data.get('user', 'N/A')}")
        
        # 추출된 텍스트
        extracted_text = self.extract_text_from_drawing_data(drawing_data)
        if extracted_text:
            context_parts.append(f"\n--- {version_label} 도면에서 추출된 텍스트 ---")
            context_parts.append(extracted_text)
        
        # JSON 데이터 요약
        json_data = drawing_data.get('json_data')
        if json_data:
            context_parts.append(f"\n--- {version_label} 도면 메타데이터 ---")
            
            # 이미지 크기 정보
            if 'width' in json_data and 'height' in json_data:
                context_parts.append(f"이미지 크기: {json_data['width']} x {json_data['height']}")
            
            # OCR 통계
            if 'ocr_data' in json_data and json_data['ocr_data']:
                ocr_data = json_data['ocr_data']
                if 'images' in ocr_data:
                    text_count = 0
                    for image in ocr_data['images']:
                        if 'fields' in image:
                            text_count += len(image['fields'])
                    context_parts.append(f"OCR 추출 텍스트 개수: {text_count}개")
            
            # Detection 통계
            if 'detection_data' in json_data and json_data['detection_data']:
                detection_data = json_data['detection_data']
                if 'detections' in detection_data:
                    detection_count = len(detection_data['detections'])
                    context_parts.append(f"감지된 객체 개수: {detection_count}개")
        
        return '\n'.join(context_parts)

    def generate_response(self, user_query: str, use_web_search: bool = False, selected_drawing: str = None) -> Dict:
        """챗봇 응답 생성 - 지능적 소스 선택 시스템"""
        try:
            # 쿼리 유형 감지
            query_type = self._detect_query_type(user_query)
            
            # 도면 검색 처리
            search_results = []
            auto_selected_drawing = None
            
            if query_type == "drawing_search":
                logger.info(f"🔍 도면 검색 모드로 처리: {user_query}")
                
                # 질문에서 도면 이름 후보 추출
                drawing_candidates = self.extract_drawing_names_from_query(user_query)
                
                for candidate in drawing_candidates:
                    results = self.search_drawings_by_name(candidate)
                    search_results.extend(results)
                
                # 중복 제거
                unique_results = {}
                for result in search_results:
                    unique_results[result['d_name']] = result
                search_results = list(unique_results.values())
                
                # 검색 결과가 1개인 경우 자동 선택
                if len(search_results) == 1:
                    auto_selected_drawing = search_results[0]['d_name']
                    logger.info(f"🎯 자동 도면 선택: {auto_selected_drawing}")
                elif len(search_results) > 1:
                    # 가장 최근 수정된 도면 우선 선택
                    latest_drawing = max(search_results, key=lambda x: x['latest_date'])
                    auto_selected_drawing = latest_drawing['d_name']
                    logger.info(f"🎯 최신 도면 자동 선택: {auto_selected_drawing}")
            
            elif query_type == "drawing_visualization":
                logger.info(f"🎨 도면 시각화 모드로 처리: {user_query}")
                
                # 질문에서 도면 이름 후보 추출
                drawing_candidates = self.extract_drawing_names_from_query(user_query)
                
                if drawing_candidates:
                    # 첫 번째 후보로 시각화 시도
                    candidate = drawing_candidates[0]
                    
                    # 도면 검색하여 존재 확인
                    candidate_results = self.search_drawings_by_name(candidate)
                    
                    if candidate_results:
                        # 최신 버전으로 시각화 수행
                        auto_selected_drawing = candidate_results[0]['d_name']
                        logger.info(f"🎨 시각화 대상 도면: {auto_selected_drawing}")
                        
                        # 직접 시각화 분석 수행
                        viz_result = self.analyze_drawing_with_visualization(auto_selected_drawing, user_query)
                        
                        # 시각화가 성공한 경우 바로 반환
                        if viz_result and viz_result.get('visualization'):
                            return viz_result
                        else:
                            # 시각화 실패 시 일반 검색으로 폴백
                            search_results = candidate_results
                    else:
                        logger.warning(f"⚠️ 시각화 요청된 도면 '{candidate}'를 찾을 수 없습니다")
            
            # 선택된 도면 우선순위: 자동 검색 > 사용자 선택
            final_selected_drawing = auto_selected_drawing or selected_drawing
            
            # RAG 검색 수행
            if query_type == "change_analysis":
                logger.info(f"🔄 변경 분석 모드로 처리: {user_query}")
                relevant_chunks = self.retrieve_change_analysis_chunks(user_query, top_k=5)
            else:
                relevant_chunks = self.retrieve_relevant_chunks(user_query, top_k=3)
            
            # 유사도 기반 소스 선택 로직
            SIMILARITY_THRESHOLD = 0.4
            high_quality_chunks = []
            low_quality_chunks = []
            
            for chunk in relevant_chunks:
                if chunk['score'] >= SIMILARITY_THRESHOLD:
                    high_quality_chunks.append(chunk)
                else:
                    low_quality_chunks.append(chunk)
            
            # 소스 정보 구성
            sources = []
            rag_context = ""
            web_search_used = False
            web_search_results = ""
            
            # 도면 검색 결과 소스 추가
            if search_results:
                for result in search_results:
                    sources.append({
                        'type': 'drawing_search',
                        'icon': '🔍',
                        'source': f'도면 검색 결과 - {result["d_name"]}',
                        'score': None,
                        'page': None,
                        'content_preview': f"버전: {result['version_count']}개, 최종수정: {result['latest_date']}, 등록자: {result['users']}",
                        'quality': 'high'
                    })
            
            # 선택된 도면 정보 추가
            drawing_context = ""
            if final_selected_drawing and final_selected_drawing != "선택하지 않음":
                logger.info(f"📄 선택된 도면 정보 활용: {final_selected_drawing}")
                
                try:
                    # 최신 버전의 도면 데이터 조회
                    drawing_data = self.get_drawing_data_from_db(final_selected_drawing, "latest")
                    
                    if drawing_data:
                        drawing_context = self.build_drawing_context(drawing_data, "선택된 도면")
                        
                        # 도면 소스 정보 추가 (중복 체크)
                        existing_drawing_sources = [s for s in sources if s.get('type') == 'database' and final_selected_drawing in s.get('source', '')]
                        
                        if not existing_drawing_sources:
                            sources.append({
                                'type': 'database',
                                'icon': '🗄️',
                                'source': f'선택된 도면 - {final_selected_drawing}',
                                'score': None,
                                'page': None,
                                'content_preview': f"등록일: {drawing_data.get('create_date')}, 등록자: {drawing_data.get('user')}",
                                'quality': 'high'
                            })
                        
                        logger.info(f"✅ 선택된 도면 데이터 조회 성공: {final_selected_drawing}")
                    else:
                        logger.warning(f"⚠️ 선택된 도면 데이터 조회 실패: {final_selected_drawing}")
                        drawing_context = f"\n\n⚠️ 선택된 도면 '{final_selected_drawing}'의 데이터를 찾을 수 없습니다.\n"
                        
                except Exception as e:
                    logger.error(f"선택된 도면 조회 중 오류: {e}")
                    drawing_context = f"\n\n⚠️ 선택된 도면 조회 중 오류가 발생했습니다: {str(e)}\n"
            
            # 고품질 RAG 데이터가 있는 경우
            if high_quality_chunks:
                logger.info(f"📖 고품질 RAG 데이터 {len(high_quality_chunks)}개 발견 (유사도 ≥ {SIMILARITY_THRESHOLD})")
                
                rag_context = self.build_rag_context(high_quality_chunks)
                
                # RAG 소스 정보 추가
                for chunk in high_quality_chunks:
                    sources.append({
                        'type': 'rag',
                        'icon': '📖',
                        'source': 'RAG 데이터베이스',
                        'score': chunk['score'],
                        'page': chunk['page'],
                        'content_preview': chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content'],
                        'quality': 'high'
                    })
                
                # 저품질 데이터도 있다면 추가 (참고용)
                if low_quality_chunks:
                    for chunk in low_quality_chunks:
                        sources.append({
                            'type': 'rag',
                            'icon': '📖',
                            'source': 'RAG 데이터베이스 (참고)',
                            'score': chunk['score'],
                            'page': chunk['page'],
                            'content_preview': chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content'],
                            'quality': 'low'
                        })
            
            # 고품질 RAG 데이터가 없거나 부족한 경우 웹 검색 시도
            # 단, internal_data 타입은 웹 검색 금지
            if (not high_quality_chunks or len(high_quality_chunks) < 2) and query_type not in ["internal_data", "drawing_search"]:
                logger.info(f"🌐 RAG 데이터 부족 (고품질: {len(high_quality_chunks)}개) - 웹 검색 시도")
                
                try:
                    # GPT에게 인터넷 검색 요청
                    web_search_prompt = f"""다음 질문에 대해 최신 정보를 제공해주세요. P&ID 및 공정 제어 관련 기술 정보를 포함해 주세요:

질문: {user_query}

답변 시 다음을 포함해 주세요:
1. 최신 기술 동향
2. 관련 표준 및 규격
3. 실무적 적용 사례
4. 안전 고려사항

답변 출처를 명시하지 말고, 전문적이고 종합적인 정보를 제공해 주세요."""

                    web_response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "당신은 P&ID 및 공정제어 전문가입니다. 최신 기술 정보와 실무 지식을 바탕으로 정확한 답변을 제공하세요."},
                            {"role": "user", "content": web_search_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1000
                    )
                    
                    web_search_results = web_response.choices[0].message.content
                    web_search_used = True
                    
                    # 웹 검색 소스 정보 추가
                    sources.append({
                        'type': 'web',
                        'icon': '🌐',
                        'source': '인터넷 검색 (GPT-4 기반)',
                        'score': None,
                        'page': None,
                        'content_preview': web_search_results[:200] + "..." if len(web_search_results) > 200 else web_search_results,
                        'quality': 'web'
                    })
                    
                    logger.info("✅ 웹 검색 완료")
                    
                except Exception as e:
                    logger.error(f"웹 검색 실패: {e}")
                    web_search_results = ""
            elif query_type == "internal_data":
                logger.info(f"🔒 내부 데이터 질문 - 웹 검색 스킵 (RAG 전용)")
            elif query_type == "drawing_search":
                logger.info(f"🔍 도면 검색 질문 - 웹 검색 스킵 (데이터베이스 전용)")
            else:
                logger.info(f"📖 RAG 데이터 충분 (고품질: {len(high_quality_chunks)}개) - 웹 검색 불필요")
            
            # 프롬프트 생성
            if query_type == "drawing_search":
                system_prompt = self.create_drawing_search_prompt(user_query, search_results, rag_context)
                max_tokens = 1800
                temperature = 0.2
            elif query_type == "change_analysis":
                system_prompt = self.create_change_analysis_prompt(user_query, rag_context)
                max_tokens = 2000
                temperature = 0.2
            elif query_type == "internal_data":
                system_prompt = self.create_internal_data_prompt(user_query, rag_context)
                max_tokens = 1800
                temperature = 0.1  # 더 일관된 답변을 위해 낮은 temperature
            else:
                system_prompt = self.create_pid_expert_prompt(user_query, rag_context)
                max_tokens = 1500
                temperature = 0.3
            
            # 선택된 도면 정보가 있으면 시스템 프롬프트에 추가
            if drawing_context and query_type != "drawing_search":
                system_prompt += f"""

**선택된 도면 정보:**
{drawing_context}

위 선택된 도면 정보를 우선적으로 참고하여 답변해주세요. 특히 사용자의 질문이 이 도면과 관련된 내용이라면 도면의 구체적인 데이터를 활용해주세요."""
            
            # 웹 검색 결과가 있으면 프롬프트에 추가
            if web_search_results:
                system_prompt += f"""

**추가 최신 정보 (웹 검색 결과):**
{web_search_results}

위 웹 검색 정보도 참고하여 최신 동향과 실무 정보를 포함한 종합적인 답변을 제공해주세요."""

            # 컨텍스트 품질 평가
            if drawing_context or high_quality_chunks or search_results:
                context_quality = "high"
            elif low_quality_chunks or web_search_results:
                context_quality = "medium"
            else:
                context_quality = "low"
            
            # OpenAI API 호출
            if not self.client:
                return {
                    'response': "OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.",
                    'sources': sources,
                    'query_type': query_type,
                    'context_quality': context_quality,
                    'web_search_used': web_search_used,
                    'similarity_threshold': SIMILARITY_THRESHOLD,
                    'selected_drawing': final_selected_drawing,
                    'search_results': search_results
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
                
                # 응답에 소스 정보 표시 추가
                source_info = self._build_source_summary(sources, SIMILARITY_THRESHOLD)
                if source_info:
                    ai_response += f"\n\n{source_info}"
                
                # 특별 모드 표시
                if query_type == "drawing_search":
                    ai_response = f"🔍 **도면 검색 모드** (발견: {len(search_results)}개)\n\n" + ai_response
                elif query_type == "change_analysis":
                    ai_response = "🔄 **변경 분석 모드**\n\n" + ai_response
                
                # 자동 선택된 도면이 있는 경우 표시
                if auto_selected_drawing:
                    ai_response = f"🎯 **자동 선택된 도면: {auto_selected_drawing}**\n\n" + ai_response
                elif final_selected_drawing and final_selected_drawing != "선택하지 않음":
                    ai_response = f"📄 **분석 기준 도면: {final_selected_drawing}**\n\n" + ai_response
                
            except Exception as e:
                logger.error(f"OpenAI API 호출 실패: {e}")
                ai_response = f"OpenAI API 오류: {e}"
            
            # 대화 기록 저장
            self.conversation_history.append({
                'timestamp': datetime.now(),
                'user_query': user_query,
                'response': ai_response,
                'query_type': query_type,
                'context_quality': context_quality,
                'sources_count': len(sources),
                'web_search_used': web_search_used,
                'similarity_threshold': SIMILARITY_THRESHOLD,
                'selected_drawing': final_selected_drawing,
                'search_results_count': len(search_results)
            })
            
            return {
                'response': ai_response,
                'sources': sources,
                'query_type': query_type,
                'context_quality': context_quality,
                'web_search_used': web_search_used,
                'similarity_threshold': SIMILARITY_THRESHOLD,
                'high_quality_sources': len(high_quality_chunks),
                'low_quality_sources': len(low_quality_chunks),
                'selected_drawing': final_selected_drawing,
                'drawing_context_used': bool(drawing_context),
                'search_results': search_results,
                'auto_selected_drawing': auto_selected_drawing
            }
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {e}")
            return {
                'response': f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}",
                'sources': [],
                'query_type': 'error',
                'context_quality': 'none',
                'web_search_used': False,
                'similarity_threshold': 0.4,
                'selected_drawing': selected_drawing,
                'search_results': []
            }

    def _build_source_summary(self, sources: List[Dict], threshold: float) -> str:
        """소스 요약 정보 생성"""
        if not sources:
            return ""
        
        summary_parts = []
        summary_parts.append("---")
        summary_parts.append("**📋 정보 출처:**")
        
        rag_sources = [s for s in sources if s['type'] == 'rag']
        web_sources = [s for s in sources if s['type'] == 'web']
        
        if rag_sources:
            high_quality = [s for s in rag_sources if s.get('quality') == 'high']
            low_quality = [s for s in rag_sources if s.get('quality') == 'low']
            
            if high_quality:
                summary_parts.append(f"📖 **RAG 데이터베이스** (고품질, 유사도 ≥ {threshold}): {len(high_quality)}개")
                for source in high_quality:
                    summary_parts.append(f"  • 페이지 {source['page']}, 유사도: {source['score']:.3f}")
            
            if low_quality:
                summary_parts.append(f"📖 **RAG 데이터베이스** (참고용, 유사도 < {threshold}): {len(low_quality)}개")
                for source in low_quality:
                    summary_parts.append(f"  • 페이지 {source['page']}, 유사도: {source['score']:.3f}")
        
        if web_sources:
            summary_parts.append(f"🌐 **인터넷 검색**: {len(web_sources)}개")
            summary_parts.append("  • GPT-4 기반 최신 정보 검색")
        
        return "\n".join(summary_parts)

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

    def create_internal_data_prompt(self, user_question, rag_context):
        """내부 데이터 전용 프롬프트 생성 - 웹 검색 없이 RAG만 사용"""
        
        internal_expert_persona = """당신은 20년 경력의 P&ID 및 공정 제어 시스템 전문가입니다.

**전문 분야:**
- P&ID 도면 해석 및 분석
- 공정 시스템 설계 및 운전
- 계측 및 제어 시스템 분석
- 공정 안전 관리
- 설비 및 장치 운전

**중요 원칙:**
⚠️ **기밀성 준수**: 제공된 내부 문서만을 기반으로 답변하며, 외부 정보는 절대 사용하지 않습니다.
📋 **정확성 우선**: 문서에 명시되지 않은 내용은 추측하지 않으며, 불확실한 부분은 명확히 표시합니다.
🔍 **상세 분석**: 제공된 문서의 내용을 체계적이고 상세하게 분석합니다.

**답변 구조:**
1. **핵심 요약** (문서 기반 주요 내용)
2. **상세 분석** (기술적 세부사항)
3. **운전 관련 사항** (실무적 고려사항)
4. **주의사항** (안전 및 제약 조건)
5. **문서 기반 제한사항** (확인이 필요한 부분)

**답변 스타일:**
- 문서에 근거한 정확한 정보만 제공
- "문서에 따르면...", "제공된 자료에서..." 등의 표현 사용
- 불확실한 내용은 "문서에서 확인되지 않음" 명시"""

        # 내부 데이터 전용 시스템 프롬프트
        system_prompt = f"""{internal_expert_persona}

**제공된 내부 문서:**
{rag_context if rag_context else "관련 내부 문서가 없습니다."}

**중요 지침:**
1. 오직 위에 제공된 내부 문서만을 기반으로 답변하세요
2. 외부 지식이나 일반적인 정보는 사용하지 마세요
3. 문서에 없는 내용은 "제공된 문서에서 확인할 수 없습니다"라고 명시하세요
4. 모든 답변은 문서의 구체적 내용을 인용하여 근거를 제시하세요

위 지침을 엄격히 준수하여 사용자의 질문에 답변해주세요."""

        return system_prompt

    def get_all_drawing_names(self) -> List[str]:
        """
        데이터베이스에서 모든 도면 파일명을 조회
        
        Returns:
            도면 파일명 리스트 (중복 제거)
        """
        try:
            conn = get_db_connection()
            if not conn:
                logger.error("데이터베이스 연결 실패")
                return []
            
            cursor = conn.cursor()
            
            query = """
            SELECT DISTINCT d_name
            FROM domyun 
            ORDER BY d_name
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # 파일명만 추출
            drawing_names = [result[0] for result in results if result[0]]
            
            logger.info(f"데이터베이스에서 {len(drawing_names)}개의 도면 파일명 조회됨")
            return drawing_names
                
        except Exception as e:
            logger.error(f"도면 파일명 조회 실패: {e}")
            return []

    def get_drawing_versions_info(self, d_name: str) -> List[Dict]:
        """
        특정 도면의 모든 버전 정보를 조회 (메타데이터만)
        
        Args:
            d_name: 도면 파일명
        
        Returns:
            버전 정보 리스트 (최신순)
        """
        try:
            conn = get_db_connection()
            if not conn:
                logger.error("데이터베이스 연결 실패")
                return []
            
            cursor = conn.cursor()
            
            query = """
            SELECT d_id, "user", create_date
            FROM domyun 
            WHERE d_name = %s 
            ORDER BY create_date DESC
            """
            
            cursor.execute(query, (d_name,))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            versions = []
            for i, result in enumerate(results):
                d_id, user, create_date = result
                versions.append({
                    'd_id': d_id,
                    'user': user,
                    'create_date': create_date,
                    'version_label': f"버전 {i+1}" if i > 0 else "최신",
                    'is_latest': i == 0
                })
            
            return versions
                
        except Exception as e:
            logger.error(f"도면 버전 정보 조회 실패: {e}")
            return []

    def generate_drawing_summary(self, d_name: str, version: str = "latest") -> Dict:
        """
        특정 도면의 요약 정보를 생성
        
        Args:
            d_name: 도면 파일명
            version: "latest" (최신) 또는 "previous" (이전) 또는 d_id
        
        Returns:
            요약 정보가 포함된 응답 딕셔너리
        """
        try:
            # 도면 데이터 조회
            if version.isdigit():
                # d_id로 직접 조회
                drawing_data = self.get_drawing_data_by_id(int(version))
            else:
                drawing_data = self.get_drawing_data_from_db(d_name, version)
            
            if not drawing_data:
                return {
                    'response': f"❌ '{d_name}' ({version}) 도면을 데이터베이스에서 찾을 수 없습니다.",
                    'sources': [],
                    'query_type': 'drawing_summary',
                    'context_quality': 'none',
                    'web_search_used': False,
                    'drawing_data': None
                }
            
            # 도면에서 텍스트 추출
            extracted_text = self.extract_text_from_drawing_data(drawing_data)
            
            # 요약 생성을 위한 프롬프트
            summary_prompt = f"""당신은 P&ID 도면 분석 전문가입니다. 다음 도면 정보를 바탕으로 전문적이고 구조화된 요약을 작성해주세요.

**도면 정보:**
- 파일명: {drawing_data.get('d_name')}
- 등록일: {drawing_data.get('create_date')}
- 등록자: {drawing_data.get('user')}

**추출된 텍스트:**
{extracted_text if extracted_text else '텍스트 정보 없음'}

**요약 구조:**
1. **도면 개요** (도면의 목적과 주요 기능)
2. **주요 구성 요소** (계측기기, 밸브, 펌프 등)
3. **제어 시스템** (제어 루프 및 안전장치)
4. **운전 특성** (주요 운전 조건 및 절차)
5. **안전 고려사항** (안전장치 및 비상대응)

각 섹션을 명확히 구분하여 작성하고, 가능한 한 구체적인 태그 번호나 설비명을 포함해주세요.
추출된 텍스트가 부족하다면 일반적인 P&ID 분석 원칙에 따라 보완 설명을 제공하되, 
"추출된 정보 기반" vs "일반적 설명" 을 명확히 구분해주세요."""

            # OpenAI API 호출
            if not self.client:
                return {
                    'response': "OpenAI API 키가 설정되지 않았습니다.",
                    'sources': [],
                    'query_type': 'drawing_summary',
                    'context_quality': 'none',
                    'web_search_used': False,
                    'drawing_data': drawing_data
                }
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "당신은 20년 경력의 P&ID 전문가입니다. 정확하고 실용적인 도면 분석을 제공합니다."},
                        {"role": "user", "content": summary_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=2000
                )
                
                summary_response = response.choices[0].message.content
                
                # 도면 정보 추가
                final_response = f"""📋 **도면 요약 분석**

**📄 도면 정보:**
- **파일명:** {drawing_data.get('d_name')}
- **등록일:** {drawing_data.get('create_date')}
- **등록자:** {drawing_data.get('user')}
- **버전:** {version}

---

{summary_response}

---

**📊 추출 통계:**
- **텍스트 길이:** {len(extracted_text)} 문자
- **JSON 데이터:** {'있음' if drawing_data.get('json_data') else '없음'}
"""
                
                # 소스 정보 구성
                sources = [{
                    'type': 'database',
                    'icon': '🗄️',
                    'source': f'도면 데이터베이스 - {d_name}',
                    'score': None,
                    'page': None,
                    'content_preview': f"등록일: {drawing_data.get('create_date')}, 등록자: {drawing_data.get('user')}",
                    'quality': 'high'
                }]
                
                return {
                    'response': final_response,
                    'sources': sources,
                    'query_type': 'drawing_summary',
                    'context_quality': 'high',
                    'web_search_used': False,
                    'drawing_data': drawing_data,
                    'extracted_text_length': len(extracted_text)
                }
                
            except Exception as e:
                logger.error(f"OpenAI API 호출 실패: {e}")
                return {
                    'response': f"요약 생성 중 오류가 발생했습니다: {str(e)}",
                    'sources': [],
                    'query_type': 'drawing_summary',
                    'context_quality': 'none',
                    'web_search_used': False,
                    'drawing_data': drawing_data
                }
                
        except Exception as e:
            logger.error(f"도면 요약 생성 실패: {e}")
            return {
                'response': f"도면 요약 생성 중 오류가 발생했습니다: {str(e)}",
                'sources': [],
                'query_type': 'drawing_summary',
                'context_quality': 'none',
                'web_search_used': False,
                'drawing_data': None
            }

    def get_drawing_data_by_id(self, d_id: int) -> Optional[Dict]:
        """
        d_id로 특정 도면 데이터를 조회
        
        Args:
            d_id: 도면 ID
        
        Returns:
            도면 데이터 또는 None
        """
        try:
            conn = get_db_connection()
            if not conn:
                logger.error("데이터베이스 연결 실패")
                return None
            
            cursor = conn.cursor()
            
            query = """
            SELECT d_id, d_name, "user", create_date, json_data, image_path
            FROM domyun 
            WHERE d_id = %s
            """
            
            cursor.execute(query, (d_id,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                d_id, d_name, user, create_date, json_data, image_path = result
                return {
                    'd_id': d_id,
                    'd_name': d_name,
                    'user': user,
                    'create_date': create_date,
                    'json_data': json_data,
                    'image_path': image_path
                }
            else:
                logger.warning(f"도면 ID '{d_id}'를 찾을 수 없습니다")
                return None
                
        except Exception as e:
            logger.error(f"데이터베이스 조회 실패: {e}")
            return None

    def search_drawings_by_name(self, search_term: str) -> List[Dict]:
        """
        도면 이름으로 LIKE 검색을 수행
        
        Args:
            search_term: 검색할 도면 이름 (부분 검색 가능)
        
        Returns:
            검색된 도면 정보 리스트 (최신순)
        """
        try:
            conn = get_db_connection()
            if not conn:
                logger.error("데이터베이스 연결 실패")
                return []
            
            cursor = conn.cursor()
            
            # LIKE 검색 쿼리 (대소문자 구분 없이)
            query = """
            SELECT DISTINCT d_name,
                   COUNT(*) as version_count,
                   MAX(create_date) as latest_date,
                   STRING_AGG(DISTINCT "user", ', ') as users
            FROM domyun 
            WHERE LOWER(d_name) LIKE LOWER(%s)
            GROUP BY d_name
            ORDER BY latest_date DESC
            """
            
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (search_pattern,))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # 결과를 딕셔너리 리스트로 변환
            drawings = []
            for d_name, version_count, latest_date, users in results:
                drawings.append({
                    'd_name': d_name,
                    'version_count': version_count,
                    'latest_date': latest_date,
                    'users': users
                })
            
            logger.info(f"도면 검색 '{search_term}': {len(drawings)}개 결과")
            return drawings
                
        except Exception as e:
            logger.error(f"도면 검색 실패: {e}")
            return []

    def extract_drawing_names_from_query(self, query: str) -> List[str]:
        """
        사용자 질문에서 도면 이름 후보를 추출
        
        Args:
            query: 사용자 질문
        
        Returns:
            추출된 도면 이름 후보 리스트
        """
        import re
        
        # 도면 이름 패턴들
        drawing_patterns = [
            r'([a-zA-Z0-9_\-]+\.(?:pdf|png|jpg|jpeg))',  # 확장자 포함 파일명
            r'([a-zA-Z0-9_\-]{3,})',  # 3자리 이상 영숫자+언더스코어
            r'([가-힣]{2,})',  # 2자리 이상 한글
        ]
        
        # 도면 관련 키워드가 포함된 경우만 처리
        drawing_keywords = ['도면', '파일', '그림', 'pdf', 'stream', 'does', 'ai']
        has_drawing_keyword = any(keyword.lower() in query.lower() for keyword in drawing_keywords)
        
        if not has_drawing_keyword:
            return []
        
        candidates = set()
        
        # 각 패턴으로 후보 추출
        for pattern in drawing_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            candidates.update(matches)
        
        # 따옴표나 괄호로 감싼 텍스트 추출
        quoted_patterns = [
            r'"([^"]+)"',  # 큰따옴표
            r"'([^']+)'",  # 작은따옴표
            r'\(([^)]+)\)',  # 괄호
        ]
        
        for pattern in quoted_patterns:
            matches = re.findall(pattern, query)
            candidates.update(matches)
        
        # 너무 짧거나 긴 후보 필터링
        filtered_candidates = []
        for candidate in candidates:
            candidate = candidate.strip()
            if 2 <= len(candidate) <= 50 and candidate not in ['도면', '파일', '그림']:
                filtered_candidates.append(candidate)
        
        return list(filtered_candidates)

    def create_drawing_search_prompt(self, user_question, search_results, rag_context):
        """도면 검색 전용 프롬프트 생성"""
        
        drawing_search_persona = """당신은 20년 경력의 P&ID 도면 관리 전문가입니다.

**전문 분야:**
- P&ID 도면 데이터베이스 검색 및 관리
- 도면 정보 분석 및 추천
- 사용자 요구사항에 맞는 도면 식별
- 도면 버전 관리 및 이력 추적

**검색 분석 접근법:**
1. **검색 결과 평가**: 찾은 도면들의 관련성 및 적합성 분석
2. **도면 정보 제공**: 각 도면의 특징과 버전 정보 설명
3. **추천 및 안내**: 사용자 질문에 가장 적합한 도면 추천
4. **추가 정보**: 필요한 경우 관련 도면이나 추가 검색 제안

**답변 구조:**
1. **검색 결과 요약** (찾은 도면 수와 주요 결과)
2. **도면별 상세 정보** (이름, 버전, 등록자, 날짜)
3. **추천 도면** (질문에 가장 적합한 도면)
4. **추가 안내** (관련 정보나 다음 단계 제안)"""

        # 검색 결과 정보 구성
        search_info = ""
        if search_results:
            search_info = f"**검색 결과 ({len(search_results)}개 도면 발견):**\n\n"
            for i, result in enumerate(search_results, 1):
                search_info += f"{i}. **{result['d_name']}**\n"
                search_info += f"   - 버전 수: {result['version_count']}개\n"
                search_info += f"   - 최종 수정: {result['latest_date']}\n"
                search_info += f"   - 등록자: {result['users']}\n\n"
        else:
            search_info = "**검색 결과:** 조건에 맞는 도면을 찾을 수 없습니다.\n\n"

        # 전체 프롬프트 구성
        system_prompt = f"""{drawing_search_persona}

**사용자 질문:**
{user_question}

**도면 검색 결과:**
{search_info}

**참고 문서 정보:**
{rag_context}

사용자가 도면에 대해 질문했습니다. 도면 검색 전문가로서 다음 사항을 중점적으로 분석해주세요:

- 검색된 도면들의 특징과 차이점
- 사용자 질문에 가장 적합한 도면 추천
- 각 도면의 버전 및 이력 정보
- 필요한 경우 추가 검색이나 관련 도면 제안

검색 결과를 바탕으로 전문적이고 실용적인 도면 정보를 제공해주세요."""

        return system_prompt

    def get_drawing_data_by_id(self, d_id: int) -> Optional[Dict]:
        """
        d_id로 특정 도면 데이터를 조회
        
        Args:
            d_id: 도면 ID
        
        Returns:
            도면 데이터 또는 None
        """
        try:
            conn = get_db_connection()
            if not conn:
                logger.error("데이터베이스 연결 실패")
                return None
            
            cursor = conn.cursor()
            
            query = """
            SELECT d_id, d_name, "user", create_date, json_data, image_path
            FROM domyun 
            WHERE d_id = %s
            """
            
            cursor.execute(query, (d_id,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                d_id, d_name, user, create_date, json_data, image_path = result
                return {
                    'd_id': d_id,
                    'd_name': d_name,
                    'user': user,
                    'create_date': create_date,
                    'json_data': json_data,
                    'image_path': image_path
                }
            else:
                logger.warning(f"도면 ID '{d_id}'를 찾을 수 없습니다")
                return None
                
        except Exception as e:
            logger.error(f"데이터베이스 조회 실패: {e}")
            return None

    def search_drawings_by_name(self, search_term: str) -> List[Dict]:
        """
        도면 이름으로 LIKE 검색을 수행
        
        Args:
            search_term: 검색할 도면 이름 (부분 검색 가능)
        
        Returns:
            검색된 도면 정보 리스트 (최신순)
        """
        try:
            conn = get_db_connection()
            if not conn:
                logger.error("데이터베이스 연결 실패")
                return []
            
            cursor = conn.cursor()
            
            # LIKE 검색 쿼리 (대소문자 구분 없이)
            query = """
            SELECT DISTINCT d_name,
                   COUNT(*) as version_count,
                   MAX(create_date) as latest_date,
                   STRING_AGG(DISTINCT "user", ', ') as users
            FROM domyun 
            WHERE LOWER(d_name) LIKE LOWER(%s)
            GROUP BY d_name
            ORDER BY latest_date DESC
            """
            
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (search_pattern,))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # 결과를 딕셔너리 리스트로 변환
            drawings = []
            for d_name, version_count, latest_date, users in results:
                drawings.append({
                    'd_name': d_name,
                    'version_count': version_count,
                    'latest_date': latest_date,
                    'users': users
                })
            
            logger.info(f"도면 검색 '{search_term}': {len(drawings)}개 결과")
            return drawings
                
        except Exception as e:
            logger.error(f"도면 검색 실패: {e}")
            return []

    def visualize_drawing_analysis(self, d_name: str, version: str = "latest") -> Optional[Dict]:
        """
        도면 시각화 분석 - OCR과 Detection 결과를 이미지에 그려서 반환
        
        Args:
            d_name: 도면 파일명
            version: "latest" (최신) 또는 "previous" (이전) 또는 d_id
        
        Returns:
            시각화된 이미지 정보와 분석 결과
        """
        try:
            # 도면 데이터 조회
            if version.isdigit():
                drawing_data = self.get_drawing_data_by_id(int(version))
            else:
                drawing_data = self.get_drawing_data_from_db(d_name, version)
            
            if not drawing_data:
                logger.error(f"도면 '{d_name}' ({version})을 찾을 수 없습니다")
                return None
            
            # 이미지 경로 확인
            image_path = drawing_data.get('image_path')
            if not image_path or not os.path.exists(image_path):
                logger.error(f"이미지 파일을 찾을 수 없습니다: {image_path}")
                return None
            
            # JSON 데이터 확인
            json_data = drawing_data.get('json_data')
            if not json_data:
                logger.error("JSON 데이터가 없습니다")
                return None
            
            # 이미지 로드
            original_image = Image.open(image_path)
            
            # JSON에서 예상 크기 가져오기
            expected_width = json_data.get('width', original_image.width)
            expected_height = json_data.get('height', original_image.height)
            
            # 이미지 크기 조정
            if original_image.size != (expected_width, expected_height):
                logger.info(f"이미지 크기 조정: {original_image.size} -> ({expected_width}, {expected_height})")
                image = original_image.resize((expected_width, expected_height), Image.Resampling.LANCZOS)
            else:
                image = original_image.copy()
            
            # 그리기 객체 생성
            draw = ImageDraw.Draw(image)
            
            # 폰트 설정 (기본 폰트 사용)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
                small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 10)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # OCR 결과 그리기
            ocr_count = 0
            if 'ocr_data' in json_data and json_data['ocr_data']:
                ocr_count = self._draw_ocr_results(draw, json_data['ocr_data'], font, small_font)
            
            # Detection 결과 그리기
            detection_count = 0
            if 'detection_data' in json_data and json_data['detection_data']:
                detection_count = self._draw_detection_results(draw, json_data['detection_data'], font)
            
            # 이미지를 Base64로 인코딩
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG', quality=95)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            # 분석 결과 반환
            result = {
                'drawing_name': d_name,
                'version': version,
                'image_base64': img_base64,
                'original_size': original_image.size,
                'resized_size': (expected_width, expected_height),
                'ocr_count': ocr_count,
                'detection_count': detection_count,
                'drawing_data': drawing_data,
                'analysis_summary': f"OCR 텍스트 {ocr_count}개, Detection 객체 {detection_count}개 시각화 완료"
            }
            
            logger.info(f"도면 시각화 완료: {d_name} - OCR {ocr_count}개, Detection {detection_count}개")
            return result
            
        except Exception as e:
            logger.error(f"도면 시각화 실패: {e}")
            return None

    def _draw_ocr_results(self, draw: ImageDraw.Draw, ocr_data: Dict, font, small_font) -> int:
        """
        OCR 결과를 이미지에 그리기
        
        Args:
            draw: PIL ImageDraw 객체
            ocr_data: OCR 데이터
            font: 큰 폰트
            small_font: 작은 폰트
        
        Returns:
            그려진 OCR 텍스트 개수
        """
        count = 0
        
        if 'images' not in ocr_data:
            return count
        
        for image_data in ocr_data['images']:
            if 'fields' not in image_data:
                continue
                
            for field in image_data['fields']:
                try:
                    # 텍스트 가져오기
                    infer_text = field.get('inferText', '')
                    if not infer_text:
                        continue
                    
                    # 바운딩 박스 정보 가져오기
                    bounding_poly = field.get('boundingPoly')
                    if not bounding_poly or 'vertices' not in bounding_poly:
                        continue
                    
                    vertices = bounding_poly['vertices']
                    if len(vertices) < 4:
                        continue
                    
                    # 좌표 추출 (왼쪽 위, 오른쪽 아래)
                    x_coords = [v.get('x', 0) for v in vertices]
                    y_coords = [v.get('y', 0) for v in vertices]
                    
                    x1, y1 = min(x_coords), min(y_coords)
                    x2, y2 = max(x_coords), max(y_coords)
                    
                    # 바운딩 박스 그리기 (파란색)
                    draw.rectangle([x1, y1, x2, y2], outline='blue', width=2)
                    
                    # 텍스트 레이블 그리기
                    # 텍스트가 너무 길면 자르기
                    display_text = infer_text[:20] + "..." if len(infer_text) > 20 else infer_text
                    
                    # 텍스트 배경 그리기
                    text_bbox = draw.textbbox((x1, y1-15), display_text, font=small_font)
                    draw.rectangle(text_bbox, fill='blue')
                    draw.text((x1, y1-15), display_text, fill='white', font=small_font)
                    
                    count += 1
                    
                except Exception as e:
                    logger.warning(f"OCR 필드 그리기 실패: {e}")
                    continue
        
        return count

    def _draw_detection_results(self, draw: ImageDraw.Draw, detection_data: Dict, font) -> int:
        """
        Detection 결과를 이미지에 그리기
        
        Args:
            draw: PIL ImageDraw 객체
            detection_data: Detection 데이터
            font: 폰트
        
        Returns:
            그려진 Detection 객체 개수
        """
        count = 0
        
        if 'detections' not in detection_data:
            return count
        
        for detection in detection_data['detections']:
            try:
                # 라벨 정보
                label = detection.get('label', 'Unknown')
                confidence = detection.get('confidence', 0.0)
                
                # 바운딩 박스 정보 (중심점 기반)
                bbox = detection.get('boundingBox')
                if not bbox:
                    continue
                
                center_x = bbox.get('x', 0)
                center_y = bbox.get('y', 0)
                width = bbox.get('width', 0)
                height = bbox.get('height', 0)
                
                # 실제 좌표 계산 (중심점에서 좌상단, 우하단 좌표로)
                x1 = center_x - width / 2
                y1 = center_y - height / 2
                x2 = center_x + width / 2
                y2 = center_y + height / 2
                
                # 바운딩 박스 그리기 (빨간색)
                draw.rectangle([x1, y1, x2, y2], outline='red', width=3)
                
                # 레이블과 신뢰도 표시
                label_text = f"{label} ({confidence:.2f})"
                
                # 텍스트 배경 그리기
                text_bbox = draw.textbbox((x1, y1-20), label_text, font=font)
                draw.rectangle(text_bbox, fill='red')
                draw.text((x1, y1-20), label_text, fill='white', font=font)
                
                count += 1
                
            except Exception as e:
                logger.warning(f"Detection 객체 그리기 실패: {e}")
                continue
        
        return count

    def analyze_drawing_with_visualization(self, d_name: str, user_question: str = None) -> Dict:
        """
        도면 분석과 시각화를 통합하여 수행
        
        Args:
            d_name: 도면 파일명
            user_question: 사용자 질문 (선택사항)
        
        Returns:
            분석 결과와 시각화 이미지가 포함된 응답
        """
        try:
            # 도면 시각화 수행
            viz_result = self.visualize_drawing_analysis(d_name)
            
            if not viz_result:
                return {
                    'response': f"❌ '{d_name}' 도면의 시각화에 실패했습니다.",
                    'sources': [],
                    'query_type': 'drawing_visualization',
                    'context_quality': 'none',
                    'web_search_used': False,
                    'visualization': None
                }
            
            # 도면 데이터로부터 텍스트 분석
            drawing_data = viz_result['drawing_data']
            extracted_text = self.extract_text_from_drawing_data(drawing_data)
            
            # AI 분석 프롬프트 생성
            analysis_prompt = f"""당신은 P&ID 도면 분석 전문가입니다. 다음 도면을 분석하고 시각화 결과를 설명해주세요.

**도면 정보:**
- 파일명: {d_name}
- 등록일: {drawing_data.get('create_date')}
- 이미지 크기: {viz_result['original_size']} → {viz_result['resized_size']}
- OCR 텍스트: {viz_result['ocr_count']}개
- Detection 객체: {viz_result['detection_count']}개

**추출된 텍스트:**
{extracted_text if extracted_text else '텍스트 정보 없음'}

**시각화 결과:**
{viz_result['analysis_summary']}

{"**사용자 질문:** " + user_question if user_question else ""}

**분석 요청:**
1. **도면 개요**: 이 도면의 주요 목적과 특징
2. **OCR 분석**: 추출된 텍스트에서 발견된 주요 정보 (계측기 태그, 설비명 등)
3. **Detection 분석**: 감지된 객체들의 특징과 배치
4. **시각화 설명**: 파란색 박스(OCR)와 빨간색 박스(Detection)로 표시된 내용
5. **종합 평가**: 도면의 완성도와 주요 특징점

시각화된 이미지에서 파란색 박스는 OCR로 추출된 텍스트 영역이고, 빨간색 박스는 객체 인식 결과입니다."""

            # OpenAI API 호출
            if not self.client:
                ai_response = "OpenAI API 키가 설정되지 않았습니다."
            else:
                try:
                    response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "당신은 20년 경력의 P&ID 전문가입니다. 도면 분석과 시각화 결과를 전문적으로 해석합니다."},
                            {"role": "user", "content": analysis_prompt}
                        ],
                        temperature=0.2,
                        max_tokens=2000
                    )
                    
                    ai_response = response.choices[0].message.content
                    
                except Exception as e:
                    logger.error(f"OpenAI API 호출 실패: {e}")
                    ai_response = f"AI 분석 중 오류가 발생했습니다: {str(e)}"
            
            # 최종 응답 구성
            final_response = f"""📊 **도면 시각화 분석 결과**

**📄 도면 정보:**
- **파일명:** {d_name}
- **등록일:** {drawing_data.get('create_date')}
- **등록자:** {drawing_data.get('user')}

**🖼️ 시각화 정보:**
- **원본 크기:** {viz_result['original_size'][0]} × {viz_result['original_size'][1]}
- **분석 크기:** {viz_result['resized_size'][0]} × {viz_result['resized_size'][1]}
- **OCR 텍스트:** {viz_result['ocr_count']}개 (파란색 박스)
- **Detection 객체:** {viz_result['detection_count']}개 (빨간색 박스)

---

{ai_response}

---

**📌 시각화 범례:**
- 🔵 **파란색 박스**: OCR로 추출된 텍스트 영역
- 🔴 **빨간색 박스**: AI가 감지한 객체 (계측기, 밸브, 배관 등)
"""
            
            # 소스 정보 구성
            sources = [{
                'type': 'visualization',
                'icon': '🎨',
                'source': f'도면 시각화 - {d_name}',
                'score': None,
                'page': None,
                'content_preview': f"OCR {viz_result['ocr_count']}개, Detection {viz_result['detection_count']}개 시각화",
                'quality': 'high'
            }]
            
            return {
                'response': final_response,
                'sources': sources,
                'query_type': 'drawing_visualization',
                'context_quality': 'high',
                'web_search_used': False,
                'visualization': viz_result,
                'extracted_text_length': len(extracted_text)
            }
            
        except Exception as e:
            logger.error(f"도면 시각화 분석 실패: {e}")
            return {
                'response': f"도면 시각화 분석 중 오류가 발생했습니다: {str(e)}",
                'sources': [],
                'query_type': 'drawing_visualization',
                'context_quality': 'none',
                'web_search_used': False,
                'visualization': None
            }