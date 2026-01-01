import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="centered")
st.title("🦷 Skycad Lab Night Guard Manager")

# 2. 보안 키 처리 (기존 동일)
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# 3. 데이터 로드
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Reference 시트 로드 (D열 단가 포함)
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)
    
    # 체크리스트 목록 추출 (E열 이후부터)
    checklist_pool = []
    for col in range(4, ref_df.shape[1]):
        items = ref_df.iloc[:, col].unique().tolist()
        checklist_pool.extend(items)
    checklist_options = sorted(list(set([i for i in checklist_pool if i and i.lower() not in ['nan', 'none', ''] High])))
except Exception as e:
    st.error(f"연결 오류: {e}")
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
        selected_clinic_pick = st.selectbox("B: Clinic 선택", options=clinic_opts, key="clinic_select")
        
        # --- [단가 자동 호출 로직] ---
        # 1. 시트 D열(인덱스 3)에서 단가를 찾아옴
        # 2. 밴쿠버처럼 값이 없거나(nan) 오류가 나면 기본값 180으로 설정
        current_price = 180 
        if selected_clinic_pick != "선택하세요" and selected_clinic_pick != "➕ 새 클리닉 직접 입력":
            try:
                # 선택한 클리닉의 D열 값을 가져옴
                price_from_sheet = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[0, 3]
                if price_from_sheet and price_from_sheet.lower() != 'nan':
                    current_price = int(float(price_from_sheet))
            except:
                current_price = 180 # 오류 시 기본값
        
        # 화면에서 단가 확인 및 즉시 수정 가능
        unit_price = st.number_input("💵 단가 수정/확인 ($)", value=current_price, step=5)
        
        final_clinic = st.text_input("클리닉 직접 입력", placeholder="타이핑하세요") if selected_clinic_pick == "➕ 새 클리닉 직접 입력" else selected_clinic_pick

        # 닥터 선택
        doctor_options = ["선택하세요"]
        if selected_clinic_pick not in ["선택하세요", "➕ 새 클리닉 직접 입력"]:
            matched_docs = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[:, 2].unique().tolist()
            doctor_options += sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none']])
        doctor_options.append("➕ 새 의사 직접 입력")
        selected_doctor_pick = st.selectbox("C: Doctor 선택", options=doctor_options)
        final_doctor = st.text_input("의사 입력", placeholder="타이핑하세요") if selected_doctor_pick == "➕ 새 의사 직접 입력" else selected_doctor_pick

        patient = st.text_input("D: Patient Name", placeholder="환자 성함")

    with col2:
        is_3d_model = st.checkbox("3D 모델 (접수일 없음)", value=True)
        receipt_date_str = "-" if is_3d_model else st.date_input("📅 접수일", datetime.now()).strftime('%Y-%m-%d')
        
        completed_date = st.date_input("✅ 완료일", datetime.now())
        due_date = st.date_input("🚨 마감일", datetime.now() + timedelta(days=7))
        shipping_date = st.date_input("🚚 출고일", due_date - timedelta(days=2))
        
        selected_arch = st.radio("Arch", options=["Max", "Mand"], horizontal=True)
        selected_material = st.selectbox("Material", options=["Thermo", "Dual", "Soft", "Hard"])
        
        # 수량 입력 및 합계 표시
        qty = st.number_input("Qty (수량)", min_value=1, value=1)
        total_amount = unit_price * qty
        st.info(f"💡 이번 케이스 합계: ${total_amount}")
        
        selected_status = st.selectbox("📊 Status", options=["Normal", "Hold", "Canceled"])

    # 체크리스트 (기존 기능)
    st.write("---")
    selected_checks = st.multiselect("📋 Check List (자동완성)", options=checklist_options, placeholder="검색하세요...")
    add_notes = st.text_input("추가 메모", placeholder="직접 입력할 내용")

    if st.button("✅ 구글 시트에 저장하기", use_container_width=True):
        if not final_clinic or not patient:
            st.warning("필수 항목을 입력하세요.")
        else:
            final_notes = ", ".join(selected_checks) + (f" | {add_notes}" if add_notes else "")
            new_row = pd.DataFrame([{
                "Case #": case_no,
                "Clinic": final_clinic,
                "Doctor": final_doctor,
                "Patient": patient,
                "Arch": selected_arch,
                "Material": selected_material,
                "Price": unit_price,
                "Qty": qty,
                "Total": total_amount,
                "Receipt Date": receipt_date_str,
                "Completed Date": completed_date.strftime('%Y-%m-%d'),
                "Shipping Date": shipping_date.strftime('%Y-%m-%d'),
                "Due Date": due_date.strftime('%Y-%m-%d'),
                "Status": selected_status,
                "Notes": final_notes
            }])
            try:
                updated_df = pd.concat([main_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"💰 {patient}님 저장 성공! 총액: ${total_amount}")
                st.rerun()
            except Exception as e:
                st.error(f"저장 오류: {e}")
