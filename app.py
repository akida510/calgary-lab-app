import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="centered")
st.title("🦷 Skycad Lab Night Guard Manager")

# --- [추가] 입력창 초기화 함수 ---
def reset_form():
    for key in st.session_state.keys():
        # 날짜나 라디오 버튼 같은 특수 키 제외하고 텍스트 입력창 위주로 초기화
        if key not in ['completed_date', 'due_date', 'shipping_date', 'arch', 'material']:
            st.session_state[key] = ""
    st.toast("입력창이 초기화되었습니다.")

# 2. 데이터 로드 및 에러 방지 (기존 동일)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)

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
        # 각 입력창에 고유한 key를 부여합니다.
        case_no = st.text_input("A: Case #", placeholder="번호 입력", key="case_id")
        
        raw_clinics = ref_df.iloc[:, 1].unique().tolist()
        clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic']])
        clinic_opts = ["선택하세요"] + clean_clinics + ["➕ 새 클리닉 직접 입력"]
        selected_clinic_pick = st.selectbox("B: Clinic 선택", options=clinic_opts, key="clinic_sel")
        
        current_price = 180 
        if selected_clinic_pick != "선택하세요" and selected_clinic_pick != "➕ 새 클리닉 직접 입력":
            try:
                price_from_sheet = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[0, 3]
                if price_from_sheet and price_from_sheet.lower() != 'nan':
                    current_price = int(float(price_from_sheet))
            except:
                current_price = 180
        
        unit_price = st.number_input("💵 단가 수정/확인 ($)", value=current_price, step=5, key="u_price")
        final_clinic = st.text_input("클리닉 직접 입력", key="direct_clinic") if selected_clinic_pick == "➕ 새 클리닉 직접 입력" else selected_clinic_pick

        doctor_options = ["선택하세요"]
        if selected_clinic_pick not in ["선택하세요", "➕ 새 클리닉 직접 입력"]:
            matched_docs = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[:, 2].unique().tolist()
            doctor_options += sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none']])
        doctor_options.append("➕ 새 의사 직접 입력")
        selected_doctor_pick = st.selectbox("C: Doctor 선택", options=doctor_options, key="doc_sel")
        final_doctor = st.text_input("의사 직접 입력", key="direct_doc") if selected_doctor_pick == "➕ 새 의사 직접 입력" else selected_doctor_pick

        patient = st.text_input("D: Patient Name", placeholder="환자 성함", key="p_name")

    with col2:
        is_3d_model = st.checkbox("3D 모델 (접수일 없음)", value=True, key="is_3d")
        receipt_date_str = "-" if is_3d_model else st.date_input("📅 접수일", datetime.now()).strftime('%Y-%m-%d')
        
        comp_date = st.date_input("✅ 완료일", datetime.now() + timedelta(days=1), key="completed_date")
        due_date = st.date_input("🚨 마감일", datetime.now() + timedelta(days=7), key="due_date")
        shipping_date = st.date_input("🚚 출고일", due_date - timedelta(days=2), key="shipping_date")
        
        selected_arch = st.radio("Arch", options=["Max", "Mand"], horizontal=True, key="arch")
        selected_material = st.selectbox("Material", options=["Thermo", "Dual", "Soft", "Hard"], key="material")
        
        qty = st.number_input("Qty (수량)", min_value=1, value=1, key="p_qty")
        total_amount = unit_price * qty
        st.info(f"💡 이번 케이스 합계: ${total_amount}")
        
        selected_status = st.selectbox("📊 Status", options=["Normal", "Hold", "Canceled"], key="p_status")

    # 체크리스트
    st.write("---")
    checklist_pool = []
    for col in range(3, ref_df.shape[1]):
        items = ref_df.iloc[:, col].unique().tolist()
        checklist_pool.extend(items)
    checklist_options = sorted(list(set([i for i in checklist_pool if i and i.lower() not in ['nan', 'none', 'price', '']])))

    selected_checks = st.multiselect("체크리스트 선택 (자동완성)", options=checklist_options, key="checks")
    add_notes = st.text_input("추가 메모 / 리메이크 사유", key="memo")

    # 사진 등록
    st.write("---")
    uploaded_file = st.file_uploader("📸 사진 첨부 (선택 사항)", type=['jpg', 'jpeg', 'png'], key="photo")

    # --- 저장 및 초기화 로직 ---
    if st.button("✅ 구글 시트에 저장하기", use_container_width=True):
        if not final_clinic or not patient or final_clinic == "선택하세요":
            st.warning("클리닉과 환자명은 필수입니다.")
        else:
            final_notes = ", ".join(selected_checks) + (f" | {add_notes}" if add_notes else "")
            
            new_row = pd.DataFrame([{
                "Case #": case_no, "Clinic": final_clinic, "Doctor": final_doctor, "Patient": patient,
                "Arch": selected_arch, "Material": selected_material, "Price": unit_price, "Qty": qty,
                "Total": total_amount, "Receipt Date": receipt_date_str, 
                "Completed Date": comp_date.strftime('%Y-%m-%d'),
                "Shipping Date": shipping_date.strftime('%Y-%m-%d'),
                "Due Date": due_date.strftime('%Y-%m-%d'),
                "Status": selected_status, "Notes": final_notes
            }])
            
            try:
                updated_df = pd.concat([main_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"🎉 {patient}님 저장 성공!")
                
                # [핵심] 저장 후 모든 입력값 초기화
                st.balloons()
                # 쿼리 파라미터를 사용하여 페이지를 완전히 새로고침하여 상태 초기화
                st.cache_data.clear()
                st.rerun()
                
            except Exception as e:
                st.error(f"저장 오류: {e}")

# (수당 정산 및 검색 탭은 이전과 동일)
