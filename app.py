import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.title("🦷 Skycad Lab Night Guard Manager")

# 2. 데이터 연결 및 로드
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Reference 시트 로드
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    # 메인 데이터 로드
    main_df = conn.read(ttl=0)

    # 필수 컬럼 자동 생성
    required_cols = ['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 'Material', 'Price', 'Qty', 'Total', 'Receipt Date', 'Completed Date', 'Shipping Date', 'Due Date', 'Status', 'Notes']
    for col in required_cols:
        if col not in main_df.columns:
            main_df[col] = 0 if col in ['Price', 'Qty', 'Total'] else ""
    
    if not main_df.empty:
        main_df['Shipping Date'] = pd.to_datetime(main_df['Shipping Date'], errors='coerce')

except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

# --- [TAB 1: 케이스 등록] ---
with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    # 1️⃣ 기본 정보 구역
    with st.expander("1️⃣ 기본 정보 입력 (필수)", expanded=True):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            case_no = st.text_input("A: Case # *", placeholder="번호 입력", key="k_case")
            patient = st.text_input("D: Patient Name *", placeholder="환자 성함", key="k_patient")

        with c2:
            raw_cl = ref_df.iloc[:, 1].unique().tolist()
            clean_cl = sorted([c for c in raw_cl if c and c.lower() not in ['nan', 'none', 'clinic']])
            cl_opts = ["선택하세요", "➕ 새 클리닉 직접 입력"] + clean_cl
            
            sel_clinic = st.selectbox("B: Clinic 선택 *", options=cl_opts, key="k_clinic_sel")
            
            final_clinic = ""
            if sel_clinic == "➕ 새 클리닉 직접 입력":
                final_clinic = st.text_input("클리닉 직접 입력", key="k_cl_direct")
            else:
                final_clinic = sel_clinic

        with c3:
            doc_opts = ["선택하세요", "➕ 새 의사 직접 입력"]
            if sel_clinic not in ["선택하세요", "➕ 새 클리닉 직접 입력"]:
                matched_docs = ref_df[ref_df.iloc[:, 1] == sel_clinic].iloc[:, 2].unique().tolist()
                doc_opts += sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none']])
            
            sel_doc = st.selectbox("C: Doctor 선택", options=doc_opts, key="k_doc_sel")
            
            final_doctor = ""
            if sel_doc == "➕ 새 의사 직접 입력":
                final_doctor = st.text_input("의사 직접 입력", key="k_doc_direct")
            else:
                final_doctor = sel_doc

    # 2️⃣ 작업 상세 및 날짜 연동 구역
    with st.expander("2️⃣ 작업 상세 및 날짜 연동", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            sel_arch = st.radio("Arch", options=["Max", "Mand"], horizontal=True, key="k_arch")
            sel_mat = st.selectbox("Material", options=["Thermo", "Dual", "Soft", "Hard"], key="k_mat")
            qty = st.number_input("Qty (수량)", min_value=1, value=1, key="k_qty")
        
        with d2:
            is_3d = st.checkbox("3D 모델 (접수일/시간 없음)", value=True, key="k_3d_check")
            if is_3d == False:
                r_date = st.date_input("📅 접수일 (석고용)", datetime.now(), key="k_r_date")
                r_time = st.time_input("⏰ 시간 (석고용)", datetime.strptime("10:00", "%H:%M").time(), key="k_r_time")
                receipt_date_str = f"{r_date.strftime('%Y-%m-%d')} {r_time.strftime('%H:%M')}"
            else:
                receipt_date_str = "-"
            
            comp_date = st.date_input("✅ 완료일 (기본:내일)", datetime.now() + timedelta(days=1), key="k_comp_date")
        
        with d3:
            # 알렉스 요청: 마감일 선택 시 출고일 자동 2일 전 연동
            due_date = st.date_input("🚨 마감일 (Due Date)", datetime.now() + timedelta(days=7), key="k_due_date")
            auto_ship_val = due_date - timedelta(days=2)
            ship_date = st.date_input("🚚 출고일 (마감 2일전 자동)", value=auto_ship_val, key="k_ship_date")
            
            sel_status = st.selectbox("📊 Status", options=["Normal", "Hold", "Canceled"], key="k_status")

    # 단가 계산
    u_price = 180
    if sel_clinic not in ["선택하세요", "➕ 새 클리닉 직접 입력"]:
        try:
            p_val = ref_df[ref_df.iloc[:, 1] == sel_clinic].iloc[0, 3]
            u_price = int(float(p_val))
        except:
            u_price = 180
    st.info(f"💰 현재 단가: ${u_price} | 합계: ${u_price * qty}")

    with st.expander("3️⃣ 체크리스트 및 메모", expanded=True):
        chk_pool = []
        for col in range(3, ref_df.shape[1]):
            items = ref_df.iloc[:, col].unique().tolist()
            chk_pool.extend(items)
        chk_opts = sorted(list(set([i for i in chk_pool if i and i.lower() not in ['nan', 'none', '']])))
        
        sel_checks = st.multiselect("📋 체크리스트 선택", options=chk_opts, key="k_checks")
        memo = st.text_input("추가 메모 (60% 작업 등)", key="k
