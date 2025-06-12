import streamlit as st
import pandas as pd
from typing import Dict, List
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from utils.rag_system_kiwi import RAGSystemWithKiwi
import re
import plotly.express as px
import plotly.graph_objects as go
from loguru import logger
import os

# 한글 폰트 설정
plt.rcParams['font.family'] = ['AppleGothic', 'Malgun Gothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def show_preprocessing_analysis():
    """전처리 과정 분석 페이지"""
    
    st.title("🔍 전처리 과정 분석 & 비교")
    st.markdown("---")
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 분석 설정")
        
        analysis_type = st.selectbox(
            "분석 유형 선택",
            ["텍스트 샘플 분석", "PDF 문서 전체 분석", "실시간 쿼리 분석"]
        )
        
        if analysis_type == "텍스트 샘플 분석":
            sample_text = st.text_area(
                "분석할 텍스트 입력",
                value="FT-101 유량 전송기를 통해 공정 라인의 유량을 측정하고, FC-101 유량 조절기가 설정값에 따라 자동으로 밸브를 제어합니다. 압력 전송기 PT-201에서 압력이 비정상적으로 상승하면 비상정지 시스템이 작동됩니다.",
                height=150
            )
        
        enable_comparison = st.checkbox("기존 방식과 Kiwi 방식 비교", value=True)
    
    # 메인 콘텐츠
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📊 전처리 과정 상세 분석")
        
        if analysis_type == "텍스트 샘플 분석" and sample_text:
            analyze_text_sample(sample_text, enable_comparison)
        
        elif analysis_type == "PDF 문서 전체 분석":
            analyze_pdf_document(enable_comparison)
        
        elif analysis_type == "실시간 쿼리 분석":
            analyze_realtime_query(enable_comparison)
    
    with col2:
        st.header("📋 분석 가이드")
        
        with st.expander("🔍 현재 기본 전처리 과정", expanded=True):
            st.markdown("""
            **기본 전처리 방식:**
            1. 공백 정규화 (`\\s+` → 단일 공백)
            2. 특수문자 제거 (`[^\\w\\s가-힣]`)
            3. 단순 공백 기준 단어 분할
            4. 고정 크기 청킹 (500단어)
            
            **한계점:**
            - 한국어 형태소 구조 무시
            - 기술 용어 분리 오류
            - 의미 단위 파괴
            """)
        
        with st.expander("🚀 Kiwi 개선 방식", expanded=True):
            st.markdown("""
            **Kiwi 전처리 방식:**
            1. 형태소 단위 분석
            2. 품사 기반 토큰 필터링
            3. P&ID 용어 사전 통합
            4. 의미 기반 문장 분할
            5. 스마트 청킹
            
            **장점:**
            - 정확한 한국어 처리
            - 기술 용어 보존
            - 문맥 보존 청킹
            """)
        
        with st.expander("📈 성능 지표", expanded=True):
            st.markdown("""
            **비교 지표:**
            - 압축 비율 (전처리 후 텍스트 크기)
            - 기술 용어 보존율
            - 형태소 분포
            - 청킹 품질
            - 검색 정확도
            """)

def analyze_text_sample(text: str, enable_comparison: bool):
    """텍스트 샘플 분석"""
    
    # Kiwi RAG 시스템만 사용
    kiwi_rag = RAGSystemWithKiwi()
    
    # 탭 생성 (비교 기능 제거)
    tab1, tab2 = st.tabs(["🔍 Kiwi 전처리", "📊 상세 분석"])
    
    with tab1:
        st.subheader("Kiwi 전처리 결과")
        kiwi_processed = kiwi_rag._basic_text_cleaning(text)
        st.code(kiwi_processed, language="text")
        
        st.metric("처리된 텍스트 길이", len(kiwi_processed))
    
    with tab2:
        st.subheader("Kiwi 분석 결과")
        kiwi_stats = kiwi_rag.get_preprocessing_stats(text)
        
        if kiwi_stats:
            # 메트릭 표시
            col1, col2 = st.columns(2)
            
            with col1:
                st.json(kiwi_stats.get('original', {}))
            
            with col2:
                st.json(kiwi_stats.get('processed', {}))

def analyze_pdf_document(enable_comparison: bool):
    """PDF 문서 전체 분석"""
    
    st.subheader("📄 PDF 문서 분석")
    
    pdf_path = "data/공정 Description_글.pdf"
    
    if not os.path.exists(pdf_path):
        st.error(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return
    
    # Kiwi RAG 시스템만 사용
    kiwi_rag = RAGSystemWithKiwi()
    
    with st.spinner("PDF 문서 분석 중..."):
        try:
            # 문서 추출
            documents = kiwi_rag.extract_text_from_pdf(pdf_path)
            
            if not documents:
                st.error("PDF 텍스트 추출 실패")
                return
            
            st.success(f"✅ {len(documents)}개 페이지 추출 완료")
            
            # 페이지별 통계
            st.subheader("📊 페이지별 통계")
            
            page_stats = []
            for doc in documents:
                stats = kiwi_rag.get_preprocessing_stats(doc['content'])
                if stats:
                    page_stats.append({
                        '페이지': doc['page'],
                        '원본길이': len(doc['content']),
                        '처리후길이': stats.get('processed_length', 0),
                        '압축비율': stats.get('compression_ratio', 0),
                        '기술용어': stats.get('technical_terms_found', 0)
                    })
            
            if page_stats:
                df_pages = pd.DataFrame(page_stats)
                st.dataframe(df_pages, use_container_width=True)
                
                # 시각화
                fig = px.bar(df_pages, x='페이지', y=['원본길이', '처리후길이'], 
                           title="페이지별 텍스트 길이 비교")
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"분석 실패: {e}")

def analyze_realtime_query(enable_comparison: bool):
    """실시간 쿼리 분석"""
    
    st.subheader("🔍 실시간 쿼리 분석")
    
    # 쿼리 입력
    query = st.text_input("분석할 쿼리 입력", value="FT101은 무엇인가요?")
    
    if query:
        # Kiwi RAG 시스템만 사용
        kiwi_rag = RAGSystemWithKiwi()
        
        try:
            # 쿼리 분석
            st.subheader("쿼리 분석 결과")
            
            query_stats = kiwi_rag.get_preprocessing_stats(query)
            if query_stats:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("원본 길이", len(query))
                
                with col2:
                    processed_length = query_stats.get('processed_length', 0)
                    st.metric("처리 후 길이", processed_length)
                
                with col3:
                    tech_terms = query_stats.get('technical_terms_found', 0)
                    st.metric("기술 용어", f"{tech_terms}개")
                
                # 토큰 분석
                if 'original' in query_stats:
                    st.json(query_stats['original'])
                    
        except Exception as e:
            st.error(f"쿼리 분석 실패: {e}")

if __name__ == "__main__":
    show_preprocessing_analysis() 