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
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)

    # 필수 컬럼 설정
    required_cols = ['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 'Material', 'Price', 'Qty', 'Total', 'Receipt Date', 'Completed Date', 'Shipping Date', 'Due Date', 'Status', 'Notes']
    for col in required_cols:
        if col not in main_df.columns:
            main_df[col] = 0 if col in ['Price', 'Qty', 'Total'] else ""
    
    if not main_df.empty:
        main_df['Shipping Date'] = pd.to_datetime(main_df['Shipping Date'], errors='coerce')

except Exception as e:
    st.error(f"데이터 연결 오류: {e}")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

# --- [TAB 1: 케이스 등록] ---
with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    # clear_on_submit=True로 저장 후 자동 비우기 유지
    with st.form("case_entry_form", clear_on_submit=True):
        with st.expander("1️⃣ 기본 정보 입력 (필수 항목 포함)", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                # 필수 항목에 * 표시
                case_no = st.text_input("A: Case # *", placeholder="번호 입력 필수")
                patient = st.text_input("D: Patient Name *", placeholder="환자 성함 필수")
            with c2:
                raw_clinics = ref_df.iloc[:, 1].unique().tolist()
                clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic']])
                clinic_opts = ["선택하세요"] + clean_clinics + ["➕ 새 클리닉 직접 입력"]
                selected_clinic_pick = st.selectbox("B: Clinic 선택 *", options=clinic_opts)
                final_clinic = st.text_input("클리닉 직접 입력 (필요시)")
            with c3:
                doctor_options = ["선택하세요"]
                if selected_clinic_pick not in ["선택하세요", "➕ 새 클리닉 직접 입력"]:
                    matched_docs = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[:, 2].unique().tolist()
                    doctor_options += sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none']])
                doctor_options.append("➕ 새 의사 직접 입력")
                selected_doctor_pick = st.selectbox("C: Doctor 선택", options=doctor_options)
                final_doctor = st.text_input("의사 직접 입력 (필요시)")

        with st.expander("2️⃣ 작업 상세 및 날짜", expanded=True):
            d1, d2, d3 = st.columns(3)
            with d1:
                selected_arch = st.radio("Arch", options=["Max", "Mand"], horizontal=True)
                selected_material = st.selectbox("Material", options=["Thermo", "Dual", "Soft", "Hard"])
                qty = st.number_input("Qty (수량)", min_value=1, value=1)
            with d2:
                is_3d_model = st.checkbox("3D 모델 (접수일/시간 없음)", value=True)
                r_date = st.date_input("📅 접수일 (석고모델용)", datetime.now())
                r_time = st.time_input("⏰ 시간 (석고모델용)", datetime.strptime("10:00", "%H:%M").time())
                receipt_date_str = "-" if is_3d_model else f"{r_date.strftime('%Y-%m-%d')} {r_time.strftime('%H:%M')}"
                
                comp_date = st.date_input("✅ 완료일 (기본:내일)", datetime.now() + timedelta(days=1))
            with d3:
                due_date = st.date_input("🚨 마감일", datetime.now() + timedelta(days=7))
                shipping_date = st.date_input("🚚 출고일", due_date - timedelta(days=2))
                selected_status = st.selectbox("📊 Status", options=["Normal", "Hold", "Canceled"])

        # 단가 계산
        unit_price = 180
        if selected_clinic_pick not in ["선택하세요", "➕ 새 클리닉 직접 입력"]:
            try:
                price_val = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[0, 3]
                unit_price = int(float(price_val))
            except: pass
        
        st.info(f"💡 현재 설정 단가: ${unit_price} | 합계: ${unit_price * qty}")
        
        with st.expander("3️⃣ 체크리스트 및 메모", expanded=True):
            checklist_pool = []
            for col in range(3, ref_df.shape[1]):
                items = ref_df.iloc[:, col].unique().tolist()
                checklist_pool.extend(items)
            checklist_options = sorted(list(set([i for i in checklist_pool if i and i.lower() not in ['nan', 'none', 'price', '']])))
            selected_checks = st.multiselect("📋 체크리스트 선택", options=checklist_options)
            add_notes = st.text_input("추가 메모 (60% 작업 등)")

        # 최종 저장 버튼
        submit_button = st.form_submit_button("🚀 구글 시트에 최종 저장", use_container_width=True)

    # --- [핵심: 알렉스의 실수를 막아주는 필터링 로직] ---
    if submit_button:
        # 실제 저장될 클리닉/닥터 값 결정
        actual_clinic = final_clinic if selected_clinic_pick == "➕ 새 클리닉 직접 입력" else selected_clinic_pick
        actual_doctor = final_doctor if selected_doctor_pick == "➕ 새 의사 직접 입력" else selected_doctor_pick

        # 필수 입력값 검증 (Case #, Clinic, Patient)
        if not case_no.strip():
            st.error("⚠️ Case #를 입력하지 않았어! 번호를 확인해줘.")
        elif not actual_clinic or actual_clinic == "선택하세요":
            st.error("⚠️ 클리닉이 선택되지 않았어! Clinic을 골라줘.")
        elif not patient.strip():
            st.error("⚠️ 환자 이름(Patient Name)이 비어있어! 이름을 입력해줘.")
        else:
            # 모든 조건 통과 시 저장 진행
            final_notes = ", ".join(selected_checks) + (f" | {add_notes}" if add_notes else "")
            new_row = pd.DataFrame([{
                "Case #": case_no, "Clinic": actual_clinic, "Doctor": actual_doctor, "Patient": patient,
                "Arch": selected_arch, "Material": selected_material, "Price": unit_price, "Qty": qty,
                "Total": unit_price * qty, "Receipt Date": receipt_date_str, 
                "Completed Date": comp_date.strftime('%Y-%m-%d'),
                "Shipping Date": shipping_date.strftime('%Y-%m-%d'),
                "Due Date": due_date.strftime('%Y-%m-%d'),
                "Status": selected_status, "Notes": final_notes
            }])
            
            try:
                updated_df = pd.concat([main_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"✅ {patient}님 케이스 저장 완료! 입력창이 초기화되었습니다.")
                st.balloons()
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}")

# (TAB 2, 3은 이전과 동일)
with tab2:
    st.subheader("💵 이번 달 수당 요약 (출고일 기준)")
    valid_df = main_df.dropna(subset=['Shipping Date'])
    if not valid_df.empty:
        now = datetime.now()
        this_month_df = valid_df[pd.to_datetime(valid_df['Shipping Date']).dt.month == now.month]
        is_normal = (this_month_df['Status'] == 'Normal')
        is_60_cancel = (this_month_df['Status'] == 'Canceled') & (this_month_df['Notes'].str.contains('60%', na=False))
        pay_df = this_month_df[is_normal | is_60_cancel]
        t_qty = int(pay_df['Qty'].sum())
        c1, c2 = st.columns(2)
        c1.metric("이번 달 출고량", f"{t_qty} 개")
        c2.metric("세후 수당 합계", f"${t_qty * 19.505333:,.2f}")
        st.dataframe(pay_df[['Shipping Date', 'Clinic', 'Patient', 'Status', 'Notes']], use_container_width=True)

with tab3:
    st.subheader("🔍 통합 검색")
    search_q = st.text_input("환자 이름 또는 Case # 입력")
    if search_q:
        res = main_df[main_df['Patient'].str.contains(search_q, na=False, case=False) | main_df['Case #'].astype(str).str.contains(search_q)]
        st.dataframe(res, use_container_width=True)
