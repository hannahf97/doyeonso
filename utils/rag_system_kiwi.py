import os
import pickle
import faiss
import numpy as np
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
import streamlit as st
from loguru import logger
import re
from kiwipiepy import Kiwi
import torch

class RAGSystemWithKiwi:
    """Kiwi 형태소 분석기를 통합한 고급 RAG 시스템"""
    
    def __init__(self, model_name: str = "jhgan/ko-sroberta-multitask"):
        """
        RAG 시스템 초기화
        
        Args:
            model_name: 임베딩 모델명 (한국어 지원)
        """
        self.model_name = model_name
        self.embedding_model = None
        self.index = None
        self.texts = []
        self.metadata = []
        self.vector_db_path = "data/vector_db_kiwi"
        self.embedding_dim = 768
        
        # PyTorch 기반 임베딩 저장 (코사인 유사도용)
        self.torch_embeddings = None
        
        # Kiwi 형태소 분석기 초기화
        self.kiwi = Kiwi()
        
        # P&ID 전문 용어를 Kiwi 사용자 사전에 추가
        self._add_technical_terms_to_kiwi()
        
        # P&ID 전문 용어 사전
        self.technical_terms = {
            'FT': '유량 전송기 (Flow Transmitter)',
            'FC': '유량 조절기 (Flow Controller)', 
            'FV': '유량 조절 밸브 (Flow Control Valve)',
            'AT': '분석 전송기 (Analyzer Transmitter)',
            'AC': '분석 조절기 (Analyzer Controller)',
            'PT': '압력 전송기 (Pressure Transmitter)',
            'PC': '압력 조절기 (Pressure Controller)',
            'TT': '온도 전송기 (Temperature Transmitter)',
            'TC': '온도 조절기 (Temperature Controller)',
            'LT': '액위 전송기 (Level Transmitter)',
            'LC': '액위 조절기 (Level Controller)',
            'PID': '배관 및 계장 다이어그램 (Piping and Instrumentation Diagram)',
            'DCS': '분산 제어 시스템 (Distributed Control System)',
            'HMI': '휴먼 머신 인터페이스 (Human Machine Interface)',
            'SCADA': '감시 제어 및 데이터 취득 (Supervisory Control and Data Acquisition)'
        }
    
    def _add_technical_terms_to_kiwi(self):
        """P&ID 전문 용어를 Kiwi 사용자 사전에 추가"""
        try:
            # P&ID 계측기기 태그들
            pid_tags = [
                'FT', 'FC', 'FV', 'AT', 'AC', 'PT', 'PC', 'TT', 'TC', 'LT', 'LC',
                'FIC', 'PIC', 'TIC', 'LIC', 'AIC', 'FRC', 'PRC', 'TRC', 'LRC',
                'FSL', 'FSH', 'PSL', 'PSH', 'TSL', 'TSH', 'LSL', 'LSH',
                'PSHH', 'PSLL', 'TSHH', 'TSLL', 'LSHH', 'LSLL'
            ]
            
            # 기술 용어들
            technical_words = [
                '배관', '계장', '다이어그램', '전송기', '조절기', '밸브', '센서',
                '압력', '온도', '유량', '액위', '분석기', '제어', '시스템',
                '안전장치', '비상정지', '인터록', '알람', '트립', '셧다운',
                '공정', '플랜트', '설비', '운전', '정비', '점검', '교정'
            ]
            
            # 사용자 사전에 추가
            for tag in pid_tags:
                self.kiwi.add_user_word(tag, 'NNP', 10.0)  # 고유명사로 추가
            
            for word in technical_words:
                self.kiwi.add_user_word(word, 'NNG', 5.0)  # 일반명사로 추가
                
            logger.info("P&ID 전문 용어를 Kiwi 사용자 사전에 추가 완료")
            
        except Exception as e:
            logger.warning(f"Kiwi 사용자 사전 추가 실패: {e}")
    
    @st.cache_resource
    def load_embedding_model(_self):
        """임베딩 모델 로드 (캐싱)"""
        try:
            logger.info(f"임베딩 모델 로드 중: {_self.model_name}")
            return SentenceTransformer(_self.model_name)
        except Exception as e:
            logger.error(f"임베딩 모델 로드 실패: {e}")
            return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict]:
        """PDF에서 텍스트 추출"""
        try:
            logger.info(f"PDF 텍스트 추출 시작: {pdf_path}")
            reader = PdfReader(pdf_path)
            documents = []
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    # 기본 텍스트 정리만 수행 (형태소 분석 제외)
                    cleaned_text = self._basic_text_cleaning(text)
                    documents.append({
                        'content': cleaned_text,
                        'page': page_num + 1,
                        'source': os.path.basename(pdf_path),
                        'original_text': text  # 원본 텍스트도 보존
                    })
            
            logger.info(f"총 {len(documents)}개 페이지에서 텍스트 추출 완료")
            return documents
            
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패: {e}")
            return []
    
    def _basic_text_cleaning(self, text: str) -> str:
        """기본 텍스트 정리 (형태소 분석 없이)"""
        print(f"\n=== Kiwi 기본 정리 시작 ===")
        print(f"원본 텍스트 (처음 100자): {text[:100]}...")
        print(f"원본 텍스트 길이: {len(text)}")
        
        # 1. 기본 정리
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        print(f"기본 정리 후 길이: {len(text)}")
        
        # 2. 특수문자 정리 (문장부호 .!? 보존)
        cleaned_text = re.sub(r'[^\w\s가-힣.!?]', ' ', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        print(f"특수문자 제거 후 길이: {len(cleaned_text)}")
        print(f"처리된 텍스트 (처음 100자): {cleaned_text[:100]}...")
        print(f"압축 비율: {len(cleaned_text)/len(text) if len(text) > 0 else 0:.2f}")
        
        # P&ID 관련 태그 찾기
        pid_tags = re.findall(r'\b[A-Z]{1,3}-?\d*\b', cleaned_text)
        print(f"발견된 P&ID 태그들: {pid_tags}")
        print(f"=== Kiwi 기본 정리 완료 ===\n")
        
        return cleaned_text
    
    def _analyze_text_structure(self, text: str) -> Dict:
        """텍스트 구조 분석 (디버깅용)"""
        try:
            tokens = self.kiwi.tokenize(text)
            
            analysis = {
                'total_tokens': len(tokens),
                'pos_distribution': {},
                'technical_terms': [],
                'sentences': len(text.split('.')),
                'avg_token_length': sum(len(t.form) for t in tokens) / len(tokens) if tokens else 0
            }
            
            for token in tokens:
                pos = token.tag
                form = token.form
                
                # 품사 분포
                analysis['pos_distribution'][pos] = analysis['pos_distribution'].get(pos, 0) + 1
                
                # 기술 용어 감지
                if form.upper() in self.technical_terms or re.match(r'^[A-Z]+(-\d+)?$', form):
                    analysis['technical_terms'].append(form)
            
            return analysis
            
        except Exception as e:
            logger.error(f"텍스트 구조 분석 실패: {e}")
            return {}
    
    def clean_null_chars(self, text):
        """null 문자 제거"""
        return text.replace('\x00', ' ')

    def formatted_text(self, pdf_text):
        """텍스트 포맷팅"""
        raw_text = ""
        for line in pdf_text:
            text = re.sub(r'\s+', ' ', line)
            text = line.replace('-', '')
            text = self.clean_null_chars(text)  # 여기서 null 문자 제거
            raw_text += text + ''

        sentences = re.split(r'(?<=[.!?]) +', raw_text.strip())
        formatted_text = '\n'.join(sentences)
        return formatted_text

    def clean_text_for_sentence_split(self, text):
        """문장 분할을 위한 텍스트 정리"""
        # 1. 줄바꿈 제거 후 공백으로 치환
        text = text.replace('\n', ' ')
        # 2. 여러 개의 공백 → 하나로
        text = re.sub(r'\s+', ' ', text)
        # 3. 앞뒤 공백 제거
        text = text.strip()
        return text
    
    def chunk_documents_with_kiwi(self, documents: List[Dict], chunk_size: int = 3, overlap: int = 0) -> List[Dict]:
        """Kiwi 문장 분할 기반 청킹 (형태소 분석 제외)"""
        print(f"\n=== Kiwi 문장 분할 청킹 시작 ===")
        print(f"전체 문서 수: {len(documents)}")
        print(f"청크 크기: {chunk_size}줄, 오버랩: {overlap}줄")
        
        chunks = []
        
        for doc_idx, doc in enumerate(documents):
            text = doc['content']
            
            print(f"\n문서 {doc_idx + 1} (페이지 {doc['page']}): {len(text)}자")
            
            try:
                # Kiwi를 사용한 문장 분할만 수행
                cleaned_text = self.clean_text_for_sentence_split(text)
                sentence_objs = self.kiwi.split_into_sents(cleaned_text)
                sentences = [s.text for s in sentence_objs]
                
                print(f"  Kiwi 문장 분할: {len(sentences)}개 문장")
                
                # 의미 기반 청킹 (200-400자)
                doc_chunks = 0
                current_chunk = ""
                
                for sent in sentences:
                    if len(current_chunk + sent) < 400:
                        current_chunk += sent + " "
                    else:
                        if len(current_chunk) >= 200:
                            chunks.append({
                                'content': current_chunk.strip(),
                                'page': doc['page'],
                                'source': doc['source'],
                                'chunk_id': len(chunks),
                                'sentence_count': len(current_chunk.split('.')),
                                'kiwi_sentence_split': True
                            })
                            doc_chunks += 1
                            current_chunk = sent + " "
                        else:
                            current_chunk += sent + " "
                
                # 마지막 청크 처리
                if current_chunk and len(current_chunk) >= 100:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'page': doc['page'],
                        'source': doc['source'],
                        'chunk_id': len(chunks),
                        'sentence_count': len(current_chunk.split('.')),
                        'kiwi_sentence_split': True
                    })
                    doc_chunks += 1
                
                if doc_chunks <= 3:  # 처음 3개 청크만 상세 출력
                    for i, chunk in enumerate([c for c in chunks if c['page'] == doc['page']][:3], 1):
                        print(f"  → 청크 {i}: {len(chunk['content'])}자")
                        print(f"    내용: {chunk['content'][:80]}...")
                
                print(f"  → 총 {doc_chunks}개 Kiwi 문장분할 청크 생성")
                        
            except Exception as e:
                print(f"  Kiwi 문장 분할 실패: {e}, 기본 청킹 사용")
                logger.warning(f"Kiwi 문장 분할 실패, 기본 청킹 사용: {e}")
                
                # 기본 문장 분할로 폴백
                cleaned_text = self.clean_text_for_sentence_split(text)
                sentences = re.split(r'(?<=[.!?]) +', cleaned_text.strip())
                
                doc_chunks = 0
                current_chunk = ""
                
                for sent in sentences:
                    if len(current_chunk + sent) < 400:
                        current_chunk += sent + " "
                    else:
                        if len(current_chunk) >= 200:
                            chunks.append({
                                'content': current_chunk.strip(),
                                'page': doc['page'],
                                'source': doc['source'],
                                'chunk_id': len(chunks),
                                'sentence_count': len(current_chunk.split('.')),
                                'fallback': True
                            })
                            doc_chunks += 1
                            current_chunk = sent + " "
                        else:
                            current_chunk += sent + " "
                
                if current_chunk and len(current_chunk) >= 100:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'page': doc['page'],
                        'source': doc['source'],
                        'chunk_id': len(chunks),
                        'sentence_count': len(current_chunk.split('.')),
                        'fallback': True
                    })
                    doc_chunks += 1
                
                print(f"  → 폴백으로 {doc_chunks}개 청크 생성")
        
        print(f"\n총 {len(chunks)}개 Kiwi 문장분할 청크 생성 완료")
        print(f"=== Kiwi 문장 분할 청킹 완료 ===\n")
        return chunks
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """텍스트 임베딩 생성"""
        if self.embedding_model is None:
            self.embedding_model = self.load_embedding_model()
        
        logger.info(f"{len(texts)}개 텍스트 임베딩 생성 중...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return embeddings
    
    def retrieve_relevant_chunks(self, query: str, chunks: List[str] = None, embeddings: torch.Tensor = None, top_k: int = 5) -> str:
        """
        Kiwi 문장 분할 + 코사인 유사도를 사용해 검색하는 함수
        
        Args:
            query: 입력된 질문
            chunks: 텍스트 청크들 (None이면 self.texts 사용)
            embeddings: 청크 임베딩들 (None이면 self.torch_embeddings 사용)
            top_k: 가장 유사한 청크 N개
            
        Returns:
            청크들을 하나의 텍스트로 합쳐서 반환
        """
        # 기본값 설정
        if chunks is None:
            chunks = self.texts
        if embeddings is None:
            embeddings = self.torch_embeddings
            
        if not chunks or embeddings is None:
            return "관련 문서를 찾을 수 없습니다."
        
        try:
            # 임베딩 모델 로드
            if self.embedding_model is None:
                self.embedding_model = self.load_embedding_model()
            
            # 쿼리 기본 정리 (형태소 분석 제외)
            processed_query = self._basic_text_cleaning(query)
            
            # 입력된 질문을 임베딩합니다
            query_embedding = self.embedding_model.encode(processed_query, convert_to_tensor=True, device='cpu')
            
            # 쿼리 임베딩을 정규화합니다
            query_embedding = query_embedding / torch.norm(query_embedding)
            
            # 모든 청크 임베딩을 정규화합니다
            embeddings = embeddings.cpu() / torch.norm(embeddings.cpu(), dim=1, keepdim=True)
            
            # 각 청크 임베딩과 쿼리 임베딩 간의 유사도를 계산합니다
            similarities = torch.matmul(embeddings, query_embedding)
            
            # 가장 유사한 청크 N개의 인덱스를 추출합니다
            top_k_indices = torch.topk(similarities, min(top_k, len(similarities))).indices.tolist()
            
            # 해당 인덱스에 해당하는 청크들을 반환합니다
            relevant_chunks = [chunks[i] for i in top_k_indices]
            
            # 청크들을 하나의 텍스트로 합쳐서 반환합니다
            return '\n\n'.join(relevant_chunks)
            
        except Exception as e:
            logger.error(f"Kiwi 검색 실패: {e}")
            return "검색 중 오류가 발생했습니다."
    
    def build_vector_database(self, pdf_path: str) -> bool:
        """벡터 데이터베이스 구축 (Kiwi 통합 + PyTorch 임베딩)"""
        try:
            # PDF에서 텍스트 추출
            documents = self.extract_text_from_pdf(pdf_path)
            if not documents:
                return False
            
            # Kiwi 기반 스마트 문서 청킹
            chunks = self.chunk_documents_with_kiwi(documents)
            if not chunks:
                return False
            
            # 텍스트와 메타데이터 분리
            texts = [chunk['content'] for chunk in chunks]
            metadata = [{k: v for k, v in chunk.items() if k != 'content'} for chunk in chunks]
            
            # 임베딩 생성
            embeddings = self.create_embeddings(texts)
            
            # PyTorch 텐서로 변환 및 저장
            self.torch_embeddings = torch.tensor(embeddings, dtype=torch.float32)
            print(f"Kiwi PyTorch 임베딩 생성: {self.torch_embeddings.shape}")
            
            # FAISS 인덱스 생성 (기존 호환성 유지)
            self.index = faiss.IndexFlatIP(embeddings.shape[1])
            
            # 임베딩 정규화
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            self.index.add(embeddings.astype('float32'))
            
            # 데이터 저장
            self.texts = texts
            self.metadata = metadata
            
            # 디스크에 저장
            self._save_vector_db()
            
            logger.info("Kiwi 기반 벡터 데이터베이스 구축 완료 (PyTorch 포함)")
            return True
            
        except Exception as e:
            logger.error(f"벡터 데이터베이스 구축 실패: {e}")
            return False
    
    def _save_vector_db(self):
        """벡터 데이터베이스를 디스크에 저장 (PyTorch 임베딩 포함)"""
        os.makedirs(self.vector_db_path, exist_ok=True)
        
        # FAISS 인덱스 저장
        faiss.write_index(self.index, f"{self.vector_db_path}/index.faiss")
        
        # PyTorch 임베딩 저장
        if self.torch_embeddings is not None:
            torch.save(self.torch_embeddings, f"{self.vector_db_path}/torch_embeddings.pt")
        
        # 메타데이터 저장
        with open(f"{self.vector_db_path}/metadata.pkl", 'wb') as f:
            pickle.dump({'texts': self.texts, 'metadata': self.metadata}, f)
    
    def load_vector_database(self) -> bool:
        """저장된 벡터 데이터베이스 로드 (PyTorch 임베딩 포함)"""
        try:
            if not os.path.exists(f"{self.vector_db_path}/index.faiss"):
                return False
            
            # FAISS 인덱스 로드
            self.index = faiss.read_index(f"{self.vector_db_path}/index.faiss")
            
            # PyTorch 임베딩 로드
            torch_path = f"{self.vector_db_path}/torch_embeddings.pt"
            if os.path.exists(torch_path):
                self.torch_embeddings = torch.load(torch_path)
                print(f"Kiwi PyTorch 임베딩 로드: {self.torch_embeddings.shape}")
            
            # 메타데이터 로드
            with open(f"{self.vector_db_path}/metadata.pkl", 'rb') as f:
                data = pickle.load(f)
                self.texts = data['texts']
                self.metadata = data['metadata']
            
            logger.info("Kiwi 기반 벡터 데이터베이스 로드 완료 (PyTorch 포함)")
            return True
            
        except Exception as e:
            logger.error(f"벡터 데이터베이스 로드 실패: {e}")
            return False
    
    def enhance_query_with_kiwi(self, query: str) -> str:
        """Kiwi를 사용한 쿼리 강화"""
        enhanced_query = query
        
        try:
            # Kiwi로 형태소 분석
            tokens = self.kiwi.tokenize(query)
            
            # 기술 용어 확장
            for token in tokens:
                term = token.form.upper()
                if term in self.technical_terms:
                    enhanced_query += f" {self.technical_terms[term]}"
            
            # 키워드 감지 및 확장
            change_keywords = ['변경', '차이', '비교', '수정', '개선']
            safety_keywords = ['안전', '위험', '비상', '정지', '보호']
            
            for token in tokens:
                if token.form in change_keywords:
                    enhanced_query += " 공정 변경사항 분석 도면 비교"
                elif token.form in safety_keywords:
                    enhanced_query += " 안전장치 비상정지 보호시스템"
            
            return enhanced_query
            
        except Exception as e:
            logger.warning(f"Kiwi 쿼리 강화 실패, 기본 방식 사용: {e}")
            return enhanced_query
    
    def get_context_for_query(self, query: str, max_context_length: int = 2000) -> str:
        """Kiwi 기반 쿼리 컨텍스트 생성"""
        # retrieve_relevant_chunks 함수를 사용하여 컨텍스트 생성
        return self.retrieve_relevant_chunks(query, top_k=3)
    
    def get_preprocessing_stats(self, text: str) -> Dict:
        """전처리 통계 정보 (디버깅/분석용)"""
        try:
            original_analysis = self._analyze_text_structure(text)
            processed_text = self._preprocess_text_with_kiwi(text)
            processed_analysis = self._analyze_text_structure(processed_text)
            
            return {
                'original': original_analysis,
                'processed': processed_analysis,
                'compression_ratio': len(processed_text) / len(text) if len(text) > 0 else 0,
                'technical_terms_found': len(original_analysis.get('technical_terms', [])),
                'processing_method': 'Kiwi'
            }
        except Exception as e:
            logger.error(f"전처리 통계 생성 실패: {e}")
            return {} 