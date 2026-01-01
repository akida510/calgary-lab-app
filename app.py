import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="centered")
st.title("🦷 Skycad Lab Night Guard Manager")

# 2. 보안 키 처리
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# 3. 데이터 로드 및 오류 방지 로직
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    
    # 메인 데이터 읽기
    main_df = conn.read(ttl=0)

    # [핵심] 'Price' 등 필수 열이 시트에 없을 경우 자동으로 임시 생성하여 오류 방지
    required_columns = {
        'Case #': "", 'Clinic': "", 'Doctor': "", 'Patient': "", 
        'Arch': "Max", 'Material': "Thermo", 'Price': 0, 'Qty': 1, 
        'Total': 0, 'Receipt Date': "-", 'Completed Date': datetime.now().strftime('%Y-%m-%d'),
        'Shipping Date': "-", 'Due Date': "-", 'Status': "Normal", 'Notes': ""
    }

    for col, default_val in required_columns.items():
        if col not in main_df.columns:
            main_df[col] = default_val

    # 데이터 타입 변환 (정산 기능을 위해 숫자와 날짜로 변환)
    if not main_df.empty:
        main_df['Price'] = pd.to_numeric(main_df['Price'], errors='coerce').fillna(0)
        main_df['Qty'] = pd.to_numeric(main_df['Qty'], errors='coerce').fillna(0)
        main_df['Total'] = pd.to_numeric(main_df['Total'], errors='coerce').fillna(0)
        # 날짜 변환 시 에러 방지
        main_df['Completed Date'] = pd.to_datetime(main_df['Completed Date'], errors='coerce')
        
except Exception as e:
    st.error(f"⚠️ 연결 오류 발생: {e}")
    st.info("💡 팁: 구글 시트 첫 번째 탭의 맨 윗줄에 'Price', 'Qty', 'Total' 등의 제목이 있는지 확인해주세요.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

# --- TAB 1: 등록 로직 (생략되지 않은 전체 로직) ---
with tab1:
    st.subheader("새로운 케이스 정보 입력")
    # ... (기존 입력 폼 코드 그대로 사용) ...
    # 사장님, 기존에 쓰시던 입력 폼 코드를 여기에 그대로 두시면 됩니다.
    st.info("입력 폼은 기존과 동일하게 작동합니다.")

# --- TAB 2: 수당 정산 (오류 방지 강화) ---
with tab2:
    st.subheader("💵 이번 달 매출 및 수당 요약")
    
    # 유효한 날짜 데이터만 필터링
    valid_date_df = main_df.dropna(subset=['Completed Date'])
    
    if valid_date_df.empty:
        st.info("이번 달 정산할 데이터가 아직 없습니다.")
    else:
        now = datetime.now()
        this_month_df = valid_date_df[valid_date_df['Completed Date'].dt.month == now.month]
        
        # 정산 조건: Normal 이거나 Canceled 중 비고에 '60%' 포함
        pay_df = this_month_df[
            (this_month_df['Status'] == 'Normal') | 
            ((this_month_df['Status'] == 'Canceled') & (this_month_df['Notes'].str.contains('60%', na=False)))
        ]
        
        total_cases = int(pay_df['Qty'].sum())
        total_sales = pay_df['Total'].sum()
        post_tax_pay = total_cases * 19.505333
        
        col1, col2, col3 = st.columns(3)
        col1.metric("작업 수량", f"{total_cases} 개")
        col2.metric("총 매출", f"${total_sales:,.2f}")
        col3.metric("내 수당(세후)", f"${post_tax_pay:,.2f}")

# (이후 검색 탭 생략)
