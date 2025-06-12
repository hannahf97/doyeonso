import streamlit as st
import pandas as pd
import psycopg2
from config.database_config import get_db_connection
import json
from datetime import datetime

# 캐싱을 위한 함수들
@st.cache_data(ttl=30)  # 30초 캐시
def get_statistics():
    """통계 정보를 캐시하여 조회"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # 전체 레코드 수
        cursor.execute("SELECT COUNT(*) FROM domyun")
        total_count = cursor.fetchone()[0]
        
        # 사용자별 레코드 수
        cursor.execute('SELECT COUNT(DISTINCT "user") FROM domyun')
        user_count = cursor.fetchone()[0]
        
        # 오늘 업로드된 레코드 수
        cursor.execute("SELECT COUNT(*) FROM domyun WHERE DATE(create_date) = CURRENT_DATE")
        today_count = cursor.fetchone()[0]
        
        # 이번 주 업로드된 레코드 수
        cursor.execute("SELECT COUNT(*) FROM domyun WHERE create_date >= CURRENT_DATE - INTERVAL '7 days'")
        week_count = cursor.fetchone()[0]
        
        return {
            'total': total_count,
            'users': user_count,
            'today': today_count,
            'week': week_count
        }
    except Exception as e:
        return None
    finally:
        conn.close()

@st.cache_data(ttl=10)  # 10초 캐시
def get_users_list():
    """사용자 목록을 캐시하여 조회"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT \"user\" FROM domyun ORDER BY \"user\"")
        users = [row[0] for row in cursor.fetchall()]
        return users
    except Exception as e:
        return []
    finally:
        conn.close()

def show():
    st.title("📊 데이터베이스 조회")
    st.markdown("저장된 domyun 테이블의 데이터를 확인할 수 있습니다.")
    
    # 데이터베이스 연결 확인
    conn = get_db_connection()
    if not conn:
        st.error("❌ 데이터베이스 연결에 실패했습니다.")
        st.info("PostgreSQL 서버가 실행 중인지 확인해주세요.")
        return
    
    try:
        # 쿼리 옵션
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("🔍 조회 옵션")
        with col2:
            if st.button("🔄 새로고침"):
                # 캐시 클리어
                get_statistics.clear()
                get_users_list.clear()
                st.rerun()
        
        # 정렬 옵션
        sort_by = st.selectbox(
            "정렬 기준",
            ["최신순 (create_date DESC)", "오래된 순 (create_date ASC)", "이름순 (d_name)", "ID순 (d_id)"],
            index=0
        )
        
        # 사용자 필터 (캐시된 데이터 사용)
        users = get_users_list()
        user_filter = st.selectbox("사용자 필터", ["모든 사용자"] + users)
        
        # 개수 제한
        limit = st.number_input("표시할 레코드 수", min_value=1, max_value=1000, value=50)
        
        # 쿼리 생성
        base_query = """
        SELECT 
            d_id,
            d_name,
            "user",
            create_date,
            image_path,
            json_data
        FROM domyun
        """
        
        # WHERE 조건
        where_conditions = []
        params = []
        
        if user_filter != "모든 사용자":
            where_conditions.append('"user" = %s')
            params.append(user_filter)
        
        if where_conditions:
            base_query += " WHERE " + " AND ".join(where_conditions)
        
        # ORDER BY
        if sort_by == "최신순 (create_date DESC)":
            base_query += " ORDER BY create_date DESC"
        elif sort_by == "오래된 순 (create_date ASC)":
            base_query += " ORDER BY create_date ASC"
        elif sort_by == "이름순 (d_name)":
            base_query += " ORDER BY d_name"
        elif sort_by == "ID순 (d_id)":
            base_query += " ORDER BY d_id"
        
        # LIMIT
        base_query += f" LIMIT {limit}"
        
        # 데이터 조회
        cursor = conn.cursor()
        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        
        if not rows:
            st.warning("조회된 데이터가 없습니다.")
            return
        
        # 통계 정보 (캐시된 데이터 사용)
        st.subheader("📈 통계 정보")
        stats = get_statistics()
        
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("전체 레코드", stats['total'])
            with col2:
                st.metric("등록된 사용자", stats['users'])
            with col3:
                st.metric("오늘 업로드", stats['today'])
            with col4:
                st.metric("이번 주 업로드", stats['week'])
        else:
            st.error("통계 정보를 불러올 수 없습니다.")
        
        st.divider()
        
        # 데이터 테이블 표시
        st.subheader("📋 데이터 목록")
        
        # DataFrame 생성 (JSON 데이터 제외하고 표시)
        df_display = pd.DataFrame(rows, columns=['ID', '파일명', '사용자', '등록일시', '이미지 경로', 'JSON 데이터'])
        
        # JSON 열은 간단히 표시
        df_display['JSON 데이터'] = df_display['JSON 데이터'].apply(
            lambda x: f"데이터 있음 ({len(str(x))} chars)" if x else "데이터 없음"
        )
        
        # 등록일시 포맷팅
        df_display['등록일시'] = pd.to_datetime(df_display['등록일시']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 테이블 표시 (안정화된 버전)
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=400,  # 고정 높이로 떨림 방지
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "파일명": st.column_config.TextColumn("파일명", width="medium"),
                "사용자": st.column_config.TextColumn("사용자", width="small"),
                "등록일시": st.column_config.TextColumn("등록일시", width="medium"),
                "이미지 경로": st.column_config.TextColumn("이미지 경로", width="large"),
                "JSON 데이터": st.column_config.TextColumn("JSON 데이터", width="small")
            }
        )
        
        # 상세 조회 섹션
        st.divider()
        st.subheader("🔍 상세 조회")
        
        # 레코드 선택
        selected_id = st.selectbox(
            "상세 조회할 레코드 ID 선택",
            options=[row[0] for row in rows],
            format_func=lambda x: f"ID {x}: {[row[1] for row in rows if row[0] == x][0]}"
        )
        
        if selected_id:
            # 선택된 레코드 상세 정보
            selected_row = next(row for row in rows if row[0] == selected_id)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.info(f"""
                **기본 정보**
                - ID: {selected_row[0]}
                - 파일명: {selected_row[1]}
                - 사용자: {selected_row[2]}
                - 등록일시: {selected_row[3]}
                - 이미지 경로: {selected_row[4]}
                """)
            
            with col2:
                if selected_row[5]:  # JSON 데이터가 있는 경우
                    st.info("**JSON 데이터 요약**")
                    try:
                        json_data = selected_row[5]
                        if isinstance(json_data, str):
                            json_data = json.loads(json_data)
                        
                        # JSON 구조 분석
                        keys = list(json_data.keys()) if isinstance(json_data, dict) else []
                        st.write(f"- 키 개수: {len(keys)}")
                        if keys:
                            st.write(f"- 주요 키: {', '.join(keys[:5])}")
                            if len(keys) > 5:
                                st.write(f"- 기타 {len(keys)-5}개 키...")
                        
                    except Exception as e:
                        st.write(f"JSON 파싱 오류: {e}")
                else:
                    st.warning("JSON 데이터가 없습니다.")
            
            # JSON 데이터 전체 보기
            if st.button("JSON 데이터 전체 보기"):
                if selected_row[5]:
                    st.json(selected_row[5])
                else:
                    st.warning("JSON 데이터가 없습니다.")
    
    except Exception as e:
        st.error(f"데이터 조회 중 오류가 발생했습니다: {e}")
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    show() 