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
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)

    # 필수 컬럼 자동 생성 및 타입 고정
    required_cols = ['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 'Material', 'Price', 'Qty', 'Total', 'Status', 'Notes', 'Completed Date']
    for col in required_cols:
        if col not in main_df.columns:
            main_df[col] = 0 if col in ['Price', 'Qty', 'Total'] else ""
    
    main_df['Notes'] = main_df['Notes'].astype(str).fillna("")
    main_df['Clinic'] = main_df['Clinic'].astype(str).fillna("")
    
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
    col1, col2 = st.columns(2)
    
    with col1:
        case_no = st.text_input("A: Case #", placeholder="번호 입력", key="case_input")
        
        # 클리닉 선택
        raw_clinics = ref_df.iloc[:, 1].unique().tolist()
        clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic']])
        clinic_opts = ["선택하세요"] + clean_clinics + ["➕ 새 클리닉 직접 입력"]
        selected_clinic_pick = st.selectbox("B: Clinic 선택", options=clinic_opts)
        
        current_price = 180 
        if selected_clinic_pick != "선택하세요" and selected_clinic_pick != "➕ 새 클리닉 직접 입력":
            try:
                price_from_sheet = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[0, 3]
                if price_from_sheet and price_from_sheet.lower() != 'nan':
                    current_price = int(float(price_from_sheet))
            except:
                current_price = 180
        
        unit_price = st.number_input("💵 단가 수정/확인 ($)", value=current_price, step=5)
        final_clinic = st.text_input("클리닉 직접 입력", placeholder="타이핑하세요") if selected_clinic_pick == "➕ 새 클리닉 직접 입력" else selected_clinic_pick

        # 닥터 선택
        doctor_options = ["선택하세요"]
        if selected_clinic_pick not in ["선택하세요", "➕ 새 클리닉 직접 입력"]:
            matched_docs = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[:, 2].unique().tolist()
            doctor_options += sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none']])
        doctor_options.append("➕ 새 의사 직접 입력")
        selected_doctor_pick = st.selectbox("C: Doctor 선택", options=doctor_options)
        final_doctor = st.text_input("의사 입력") if selected_doctor_pick == "➕ 새 의사 직접 입력" else selected_doctor_pick

        patient = st.text_input("D: Patient Name", placeholder="환자 성함")

    with col2:
        is_3d_model = st.checkbox("3D 모델 (접수일 없음)", value=True)
        receipt_date_str = "-" if is_3d_model else st.date_input("📅 접수일", datetime.now()).strftime('%Y-%m-%d')
        
        # --- [변경 포인트] 완료일 기본값을 내일(오늘+1일)로 설정 ---
        completed_date = st.date_input("✅ 완료일", datetime.now() + timedelta(days=1))
        
        due_date = st.date_input("🚨 마감일", datetime.now() + timedelta(days=7))
        shipping_date = st.date_input("🚚 출고일", due_date - timedelta(days=2))
        
        selected_arch = st.radio("Arch", options=["Max", "Mand"], horizontal=True)
        selected_material = st.selectbox("Material", options=["Thermo", "Dual", "Soft", "Hard"])
        
        qty = st.number_input("Qty (수량)", min_value=1, value=1)
        total_amount = unit_price * qty
        st.info(f"💡 이번 케이스 합계: ${total_amount}")
        
        selected_status = st.selectbox("📊 Status", options=["Normal", "Hold", "Canceled"])

    # 체크리스트 및 기타 로직 (이하 동일)
    st.write("---")
    # ... (생략된 뒷부분 로직은 이전과 동일하게 유지하시면 됩니다) ...
