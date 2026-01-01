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

    # 필수 컬럼 자동 생성
    required_cols = ['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 'Material', 'Price', 'Qty', 'Total', 'Receipt Date', 'Completed Date', 'Shipping Date', 'Due Date', 'Status', 'Notes']
    for col in required_cols:
        if col not in main_df.columns:
            main_df[col] = 0 if col in ['Price', 'Qty', 'Total'] else ""
    
    main_df['Notes'] = main_df['Notes'].astype(str).fillna("")
    main_df['Clinic'] = main_df['Clinic'].astype(str).fillna("")
    
    if not main_df.empty:
        main_df['Price'] = pd.to_numeric(main_df['Price'], errors='coerce').fillna(0)
        main_df['Qty'] = pd.to_numeric(main_df['Qty'], errors='coerce').fillna(0)
        main_df['Total'] = pd.to_numeric(main_df['Total'], errors='coerce').fillna(0)
        # 날짜 형식 변환 (정산용)
        main_df['Shipping Date'] = pd.to_datetime(main_df['Shipping Date'], errors='coerce')

except Exception as e:
    st.error(f"데이터 연결 중 오류: {e}")
    st.stop()

# 모든 입력창 초기화 함수
def clear_form():
    st.session_state["case_id"] = ""
    st.session_state["p_name"] = ""
    st.session_state["clinic_sel"] = "선택하세요"
    st.session_state["doc_sel"] = "선택하세요"
    if "direct_clinic" in st.session_state: st.session_state["direct_clinic"] = ""
    if "direct_doc" in st.session_state: st.session_state["direct_doc"] = ""
    st.session_state["p_qty"] = 1
    st.session_state["memo"] = ""
    st.session_state["checks"] = []
    st.toast("모든 입력창을 비웠습니다!")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

# --- [TAB 1: 케이스 등록] ---
with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    with st.expander("1️⃣ 기본 정보 입력", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            case_no = st.text_input("A: Case #", placeholder="번호 입력", key="case_id")
            patient = st.text_input("D: Patient Name", placeholder="환자 성함", key="p_name")
        with c2:
            raw_clinics = ref_df.iloc[:, 1].unique().tolist()
            clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic']])
            clinic_opts = ["선택하세요"] + clean_clinics + ["➕ 새 클리닉 직접 입력"]
            selected_clinic_pick = st.selectbox("B: Clinic 선택", options=clinic_opts, key="clinic_sel")
            final_clinic = st.text_input("클리닉 직접 입력", key="direct_clinic") if selected_clinic_pick == "➕ 새 클리닉 직접 입력" else selected_clinic_pick
        with c3:
            doctor_options = ["선택하세요"]
            if selected_clinic_pick not in ["선택하세요", "➕ 새 클리닉 직접 입력"]:
                matched_docs = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[:, 2].unique().tolist()
                doctor_options += sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none']])
            doctor_options.append("➕ 새 의사 직접 입력")
            selected_doctor_pick = st.selectbox("C: Doctor 선택", options=doctor_options, key="doc_sel")
            final_doctor = st.text_input("의사 직접 입력", key="direct_doc") if selected_doctor_pick == "➕ 새 의사 직접 입력" else selected_doctor_pick

    with st.expander("2️⃣ 작업 상세 및 날짜", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            selected_arch = st.radio("Arch", options=["Max", "Mand"], horizontal=True, key="arch")
            selected_material = st.selectbox("Material", options=["Thermo", "Dual", "Soft", "Hard"], key="material")
            qty = st.number_input("Qty (수량)", min_value=1, value=1, key="p_qty")
        with d2:
            is_3d_model = st.checkbox("3D 모델 (접수일/시간 없음)", value=True, key="is_3d")
            if not is_3d_model:
                r_date = st.date_input("📅 접수일", datetime.now(), key="r_date_val")
                r_time = st.time_input("⏰ 시간", datetime.strptime("10:00", "%H:%M").time(), key="r_time_val")
                receipt_date_str = f"{r_date.strftime('%Y-%m-%d')} {r_time.strftime('%H:%M')}"
            else:
                receipt_date_str = "-"
            
            comp_date = st.date_input("✅ 완료일(기본:내일)", datetime.now() + timedelta(days=1), key="completed_date")
        with d3:
            due_date = st.date_input("🚨 마감일", datetime.now() + timedelta(days=7), key="due_date")
            shipping_date = st.date_input("🚚 출고일", due_date - timedelta(days=2), key="shipping_date")
            selected_status = st.selectbox("📊 Status", options=["Normal", "Hold", "Canceled"], key="p_status")

    current_price = 180 
    if selected_clinic_pick not in ["선택하세요", "➕ 새 클리닉 직접 입력"]:
        try:
            price_from_sheet = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[0, 3]
            current_price = int(float(price_from_sheet))
        except: pass
    unit_price = st.number_input("💵 단가 수정 ($)", value=current_price, step=5, key="u_price")
    total_amount = unit_price * qty
    st.info(f"💰 합계: ${total_amount}")

    with st.expander("3️⃣ 체크리스트 및 사진", expanded=True):
        checklist_pool = []
        for col in range(3, ref_df.shape[1]):
            items = ref_df.iloc[:, col].unique().tolist()
            checklist_pool.extend(items)
        checklist_options = sorted(list(set([i for i in checklist_pool if i and i.lower() not in ['nan', 'none', 'price', '']])))
        
        selected_checks = st.multiselect("📋 체크리스트 선택", options=checklist_options, key="checks")
        add_notes = st.text_input("추가 메모 (60% 작업 등)", key="memo")
        uploaded_file = st.file_uploader("📸 사진 첨부", type=['jpg', 'jpeg', 'png'], key="photo_upload")

    if st.button("🚀 구글 시트에 최종 저장", use_container_width=True):
        if not final_clinic or not patient or final_clinic == "선택하세요":
            st.error("⚠️ 클리닉 이름과 환자 성함은 필수야!")
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
                clear_form() 
                st.success(f"✅ {patient}님 케이스 저장 완료!")
                st.balloons()
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}")

# --- [TAB 2: 수당 정산] ---
with tab2:
    st.subheader("💵 이번 달 수당 요약 (출고일 기준)")
    # [수정] 출고일(Shipping Date) 데이터가 있는 것들만 필터링
    valid_df = main_df.dropna(subset=['Shipping Date'])
    if not valid_df.empty:
        now = datetime.now()
        # [수정] 출고일 기준으로 이번 달 데이터 추출
        this_month_df = valid_df[pd.to_datetime(valid_df['Shipping Date']).dt.month == now.month]
        
        is_normal = (this_month_df['Status'] == 'Normal')
        is_60_cancel = (this_month_df['Status'] == 'Canceled') & (this_month_df['Notes'].str.contains('60%', na=False))
        
        pay_df = this_month_df[is_normal | is_60_cancel]
        t_qty = int(pay_df['Qty'].sum())
        
        c1, c2 = st.columns(2)
        c1.metric("이번 달 출고량", f"{t_qty} 개")
        c2.metric("세후 수당 합계", f"${t_qty * 19.505333:,.2f}")
        
        st.write("---")
        st.write(f"📅 {now.month}월 출고 상세 내역")
        st.dataframe(pay_df[['Shipping Date', 'Clinic', 'Patient', 'Status', 'Notes']], use_container_width=True)
    else:
        st.info("이번 달 출고 기록이 없어.")

# --- [TAB 3: 환자 검색] ---
with tab3:
    st.subheader("🔍 통합 검색")
    search_q = st.text_input("환자 이름 또는 Case # 입력", key="search_bar")
    if search_q:
        res = main_df[main_df['Patient'].str.contains(search_q, na=False, case=False) | main_df['Case #'].astype(str).str.contains(search_q)]
        st.dataframe(res, use_container_width=True)
