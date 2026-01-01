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

# 3. 데이터 로드 및 에러 방지
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    main_df = conn.read(ttl=0)

    # 필수 컬럼 자동 생성 및 타입 고정 (에러 방지 핵심)
    required_cols = ['Price', 'Qty', 'Total', 'Status', 'Notes', 'Completed Date']
    for col in required_cols:
        if col not in main_df.columns:
            main_df[col] = 0 if col in ['Price', 'Qty', 'Total'] else ""
    
    # [에러 해결!] Notes를 강제로 문자열(str)로 변환
    main_df['Notes'] = main_df['Notes'].astype(str).fillna("")
    
    if not main_df.empty:
        main_df['Price'] = pd.to_numeric(main_df['Price'], errors='coerce').fillna(0)
        main_df['Qty'] = pd.to_numeric(main_df['Qty'], errors='coerce').fillna(0)
        main_df['Total'] = pd.to_numeric(main_df['Total'], errors='coerce').fillna(0)
        main_df['Completed Date'] = pd.to_datetime(main_df['Completed Date'], errors='coerce')

except Exception as e:
    st.error(f"데이터 연결 중 오류: {e}")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    st.subheader("새로운 케이스 정보 입력")
    # ... (기존 입력 코드 생략 - 사장님 기존 폼 그대로 사용) ...
    
    # --- [추가] 사진 업로드 기능 ---
    st.write("---")
    st.markdown("### 📸 사진 첨부 (선택 사항)")
    uploaded_file = st.file_uploader("이미지 파일을 선택하세요 (용량 최소화 권장)", type=['jpg', 'jpeg', 'png'])
    if uploaded_file:
        st.image(uploaded_file, caption="업로드 예정 사진", width=200)
        st.warning("⚠️ 현재 버전은 사진 경로 기록만 지원합니다. 실제 사진 저장을 위해서는 클라우드 설정이 필요할 수 있습니다.")

    # (저장 버튼 클릭 시 로직은 기존과 동일하되, Notes 처리에 주의)
    # ... (저장 로직 생략) ...

with tab2:
    st.subheader("💵 이번 달 수당 정산")
    
    # 에러 방지용 필터링
    valid_df = main_df.dropna(subset=['Completed Date'])
    if not valid_df.empty:
        now = datetime.now()
        this_month = valid_df[valid_df['Completed Date'].dt.month == now.month]
        
        # [에러 수정 포인트] .str.contains 사용 전 다시 한번 타입 체크
        is_normal = (this_month['Status'] == 'Normal')
        is_60_percent_canceled = (this_month['Status'] == 'Canceled') & (this_month['Notes'].str.contains('60%', na=False))
        
        pay_df = this_month[is_normal | is_60_percent_canceled]
        
        total_cases = int(pay_df['Qty'].sum())
        post_tax_pay = total_cases * 19.505333
        
        col1, col2 = st.columns(2)
        col1.metric("이번 달 작업 개수", f"{total_cases} 개")
        col2.metric("내 수당 (세후)", f"${post_tax_pay:,.2f}")
        
        st.dataframe(pay_df[['Completed Date', 'Clinic', 'Patient', 'Status', 'Notes']], use_container_width=True)
    else:
        st.info("정산할 데이터가 없습니다.")

with tab3:
    # (검색 로직 생략)
    pass
