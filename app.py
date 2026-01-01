import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="centered")
st.title("🦷 Skycad Lab Night Guard Manager")

# 2. 보안 키 처리 (생략 - 기존과 동일)
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# 3. 데이터 로드
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Reference 시트 전체 로드
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    main_df = conn.read(ttl=0)
    
    # --- [추가] 체크리스트 목록 추출 ---
    # 레퍼런스 시트의 D열(인덱스 3)부터 있는 데이터들을 하나의 리스트로 통합
    # 사장님이 주신 텍스트 기반으로 모든 유효한 텍스트를 중복 없이 가져옵니다.
    checklist_pool = []
    for col in range(3, ref_df.shape[1]): # D열부터 끝까지 탐색
        items = ref_df.iloc[:, col].unique().tolist()
        checklist_pool.extend(items)
    
    # 쓸데없는 값 제거 및 정리
    checklist_options = sorted(list(set([
        i.strip() for i in checklist_pool 
        if i and i.lower() not in ['nan', 'none', 'null', 'checklist', '']
    ])))
except Exception as e:
    st.error(f"연결 오류: {e}")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    st.subheader("새로운 케이스 정보 입력")
    col1, col2 = st.columns(2)
    
    with col1:
        case_no = st.text_input("A: Case #", placeholder="번호 입력", key="case_input")
        
        # 클리닉/닥터 선택 (기존 로직 유지)
        raw_clinics = ref_df.iloc[:, 1].unique().tolist()
        clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic']])
        clinic_opts = ["선택하세요"] + clean_clinics + ["➕ 새 클리닉 직접 입력"]
        selected_clinic_pick = st.selectbox("B: Clinic 선택", options=clinic_opts)
        final_clinic = st.text_input("클리닉 입력", key="new_clinic") if selected_clinic_pick == "➕ 새 클리닉 직접 입력" else selected_clinic_pick

        # 닥터 선택
        doctor_options = ["선택하세요"]
        if selected_clinic_pick not in ["선택하세요", "➕ 새 클리닉 직접 입력"]:
            matched_docs = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[:, 2].unique().tolist()
            doctor_options += sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none']])
        doctor_options.append("➕ 새 의사 직접 입력")
        selected_doctor_pick = st.selectbox("C: Doctor 선택", options=doctor_options)
        final_doctor = st.text_input("의사 입력", key="new_doc") if selected_doctor_pick == "➕ 새 의사 직접 입력" else selected_doctor_pick

        patient = st.text_input("D: Patient Name", placeholder="환자 성함")

    with col2:
        is_3d_model = st.checkbox("3D 모델 (접수일 없음)", value=True)
        receipt_date_str = "-" if is_3d_model else st.date_input("📅 접수일", datetime.now()).strftime('%Y-%m-%d')
        
        completed_date = st.date_input("✅ 완료일", datetime.now())
        due_date = st.date_input("🚨 마감일", datetime.now() + timedelta(days=7))
        shipping_date = st.date_input("🚚 출고일", due_date - timedelta(days=2))
        
        selected_arch = st.radio("Arch", options=["Max", "Mand"], horizontal=True)
        selected_material = st.selectbox("Material", options=["Thermo", "Dual", "Soft", "Hard"])
        selected_status = st.selectbox("📊 Status", options=["Normal", "Hold", "Canceled"])

    # --- [핵심] 체크리스트 자동 완성 선택 창 ---
    st.write("---")
    st.markdown("### 📋 F: Check List / 리메이크 사유")
    selected_checks = st.multiselect(
        "항목을 검색하거나 선택하세요 (앞글자를 치면 추천이 뜹니다)",
        options=checklist_options,
        placeholder="예: Thin, Anterior, Canine..."
    )
    
    # 직접 타이핑하고 싶은 경우를 위한 추가 메모장
    additional_notes = st.text_input("추가 메모 (목록에 없는 경우 직접 입력)")

    if st.button("✅ 구글 시트에 저장하기", use_container_width=True):
        if final_clinic in ["선택하세요", ""] or not patient:
            st.warning("필수 항목을 확인해 주세요.")
        else:
            # 선택한 체크리스트들을 콤마(,)로 연결해서 하나의 문장으로 만듦
            final_notes = ", ".join(selected_checks)
            if additional_notes:
                final_notes += f" | {additional_notes}"
            
            new_row = pd.DataFrame([{
                "Case #": case_no,
                "Clinic": final_clinic,
                "Doctor": final_doctor,
                "Patient": patient,
                "Arch": selected_arch,
                "Material": selected_material,
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
                st.success("🎉 저장 성공!")
                st.rerun()
            except Exception as e:
                st.error(f"저장 오류: {e}")
