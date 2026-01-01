import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.title("🦷 Skycad Lab Night Guard Manager")

# 2. 보안 키 처리
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# 3. 데이터 로드 및 전처리
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)

    # 필수 컬럼 자동 생성 (데이터 누락 방지)
    required_cols = ['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 'Material', 'Price', 'Qty', 'Total', 'Receipt Date', 'Completed Date', 'Shipping Date', 'Due Date', 'Status', 'Notes']
    for col in required_cols:
        if col not in main_df.columns:
            main_df[col] = 0 if col in ['Price', 'Qty', 'Total'] else ""
    
    # 텍스트 형식 강제 지정 (에러 방지)
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

# --- [TAB 1: 케이스 등록] ---
with tab1:
    st.subheader("새로운 케이스 정보 입력")
    col1, col2 = st.columns(2)
    
    with col1:
        case_no = st.text_input("A: Case #", placeholder="번호 입력", key="case_id")
        
        # 클리닉 및 단가 연동
        raw_clinics = ref_df.iloc[:, 1].unique().tolist()
        clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic']])
        clinic_opts = ["선택하세요"] + clean_clinics + ["➕ 새 클리닉 직접 입력"]
        selected_clinic_pick = st.selectbox("B: Clinic 선택", options=clinic_opts, key="clinic_sel")
        
        current_price = 180 
        if selected_clinic_pick not in ["선택하세요", "➕ 새 클리닉 직접 입력"]:
            try:
                # Reference 탭 D열에서 단가 로드
                price_from_sheet = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[0, 3]
                if price_from_sheet and price_from_sheet.lower() != 'nan':
                    current_price = int(float(price_from_sheet))
            except:
                current_price = 180
        
        unit_price = st.number_input("💵 단가 수정/확인 ($)", value=current_price, step=5, key="u_price")
        final_clinic = st.text_input("클리닉 직접 입력", key="direct_clinic") if selected_clinic_pick == "➕ 새 클리닉 직접 입력" else selected_clinic_pick

        # 닥터 선택
        doctor_options = ["선택하세요"]
        if selected_clinic_pick not in ["선택하세요", "➕ 새 클리닉 직접 입력"]:
            matched_docs = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[:, 2].unique().tolist()
            doctor_options += sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none']])
        doctor_options.append("➕ 새 의사 직접 입력")
        selected_doctor_pick = st.selectbox("C: Doctor 선택", options=doctor_options, key="doc_sel")
        final_doctor = st.text_input("의사 직접 입력", key="direct_doc") if selected_doctor_pick == "➕ 새 의사 직접 입력" else selected_doctor_pick

        patient = st.text_input("D: Patient Name", placeholder="환자 성함", key="p_name")

    with col2:
        # 접수 시간 입력 (석고모델 대응)
        is_3d_model = st.checkbox("3D 모델 (접수일/시간 없음)", value=True, key="is_3d")
        if is_3d_model:
            receipt_date_str = "-"
        else:
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                r_date = st.date_input("📅 접수일", datetime.now())
            with r_col2:
                r_time = st.time_input("⏰ 시간", datetime.strptime("10:00", "%H:%M").time())
            receipt_date_str = f"{r_date.strftime('%Y-%m-%d')} {r_time.strftime('%H:%M')}"
