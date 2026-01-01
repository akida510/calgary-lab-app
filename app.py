import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="centered")
st.title("🦷 Skycad Lab Night Guard Manager")

# 2. 보안 키 및 데이터 로드 (기존 로직 동일)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    main_df = conn.read(ttl=0)
    # 데이터 타입 정리 (금액, 수량 등을 숫자로 변환)
    if not main_df.empty:
        main_df['Price'] = pd.to_numeric(main_df['Price'], errors='coerce').fillna(0)
        main_df['Qty'] = pd.to_numeric(main_df['Qty'], errors='coerce').fillna(0)
        main_df['Total'] = pd.to_numeric(main_df['Total'], errors='coerce').fillna(0)
        main_df['Completed Date'] = pd.to_datetime(main_df['Completed Date'], errors='coerce')
except Exception as e:
    st.error(f"연결 오류: {e}")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

# --- [TAB 1: 케이스 등록] (기존 기능 유지) ---
with tab1:
    # (앞선 코드의 등록 로직 동일)
    st.subheader("새로운 케이스 정보 입력")
    # ... (생략: 이전 코드와 동일한 입력 폼) ...
    # [참고] 저장 시 'Status'가 'Normal'이거나 'Canceled(60%완료)'일 때 정산되도록 유도

# --- [TAB 2: 수당 정산] (신규 추가) ---
with tab2:
    st.subheader("💵 이번 달 매출 및 수당 요약")
    
    if main_df.empty:
        st.info("등록된 데이터가 없습니다.")
    else:
        # 이번 달 데이터만 필터링
        now = datetime.now()
        this_month_df = main_df[main_df['Completed Date'].dt.month == now.month]
        
        # 정산 대상 필터링: Normal 상태 + Canceled 중 비고란에 '60%'가 포함된 경우
        pay_df = this_month_df[
            (this_month_df['Status'] == 'Normal') | 
            ((this_month_df['Status'] == 'Canceled') & (this_month_df['Notes'].str.contains('60%', na=False)))
        ]
        
        total_cases = int(pay_df['Qty'].sum())
        total_sales = pay_df['Total'].sum()
        
        # 수당 계산 (세전 30 / 세후 19.505333)
        pre_tax_pay = total_cases * 30
        post_tax_pay = total_cases * 19.505333
        
        # 상단 요약 카드
        col1, col2, col3 = st.columns(3)
        col1.metric("총 작업 수량", f"{total_cases} 개")
        col2.metric("총 매출 (Lab)", f"${total_sales:,.2f}")
        col3.metric("내 수당 (세후)", f"${post_tax_pay:,.2f}")
        
        st.divider()
        
        with st.expander("상세 내역 보기"):
            st.write(f"**{now.month}월 정산 대상 리스트** (취소 건 중 60% 작업 포함)")
            display_df = pay_df[['Completed Date', 'Clinic', 'Patient', 'Qty', 'Total', 'Status', 'Notes']]
            st.dataframe(display_df, use_container_width=True)
            
            st.info(f"💡 세전 수당 합계: ${pre_tax_pay:,.2f}")

# --- [TAB 3: 환자 검색] (기존 기능) ---
with tab3:
    st.subheader("🔍 케이스 검색")
    search_q = st.text_input("환자 이름 또는 Case # 입력", placeholder="검색어를 입력하세요")
    if search_q:
        res = main_df[main_df['Patient'].str.contains(search_q, na=False) | main_df['Case #'].astype(str).str.contains(search_q)]
        st.table(res[['Case #', 'Clinic', 'Patient', 'Status', 'Completed Date']])
