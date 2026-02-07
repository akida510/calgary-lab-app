import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [디자인 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    label p, .stMarkdown p, p, span { color: #ffffff !important; }
    
    /* 레터 용지 비율 컨테이너 */
    .invoice-wrapper { display: flex; justify-content: center; padding: 20px; background-color: #262730; }
    .invoice-paper {
        background-color: white !important; width: 100%; max-width: 750px; 
        aspect-ratio: 8.5 / 11; padding: 40px 50px; border: 1px solid #000;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: flex; flex-direction: column; box-sizing: border-box;
    }
    .invoice-paper * { color: #000000 !important; font-family: 'Arial', sans-serif; }
    .logo-main { font-size: 55px; font-weight: 900; font-style: italic; color: #1a4e8a !important; letter-spacing: -3px; line-height: 1; }
    .patient-line { margin: 20px 0; padding: 12px 0; border-top: 2px solid black; border-bottom: 2px solid black; font-size: 18px; font-weight: bold; }
    .item-table { width: 100%; border-collapse: collapse; flex-grow: 1; }
    .item-table th { border-bottom: 1.5px solid black; text-align: left; padding: 8px 0; }
    .item-table td { padding: 15px 0; vertical-align: top; font-size: 16px; }
    .bottom-box { margin-top: auto; }
    .notice-box { border: 1.5px solid black; padding: 15px; text-align: center; }
    
    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown { display: none !important; }
        .invoice-wrapper { padding: 0; background: none; }
        .invoice-paper { border: none; box-shadow: none; width: 100%; max-width: none; aspect-ratio: auto; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [데이터 연동 영역]
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

# 병원 및 의사 DB
ref_data = pd.DataFrame([
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Amhipreat Kaur", "Address": "13510 177 St NW, Edmonton, AB", "Phone": "(780) 455-6806", "Region": "Courier"},
    {"Clinic": "Calgary Central Dental", "Doctor": "Dr. Lana Huynh", "Address": "205-7136 11 St NE, Calgary, AB", "Phone": "(403) 970-0600", "Region": "Local"}
])

def get_business_day(start_date, days_to_subtract):
    curr = start_date
    while days_to_subtract > 0:
        curr -= timedelta(days=1)
        if curr.weekday() < 5: days_to_subtract -= 1
    return curr

# ---------------------------------------------------------
# [UI 화면]
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트/완료", "🔍 검색"])

with tab1:
    st.markdown("### 📋 케이스 등록")
    c1, c2 = st.columns(2)
    
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: IT30")
        patient = st.text_input("Patient(환자명)")
        
        # 상호 연동 드롭다운 로직
        clinic_list = ["선택"] + ref_data["Clinic"].tolist()
        doctor_list = ["선택"] + ref_data["Doctor"].tolist()
        
        # 상태 관리를 위한 session_state 사용
        if 'sel_clinic' not in st.session_state: st.session_state.sel_clinic = "선택"
        if 'sel_doctor' not in st.session_state: st.session_state.sel_doctor = "선택"

        def update_from_clinic():
            if st.session_state.c_box != "선택":
                doc = ref_data[ref_data["Clinic"] == st.session_state.c_box]["Doctor"].iloc[0]
                st.session_state.d_box = doc

        def update_from_doctor():
            if st.session_state.d_box != "선택":
                cln = ref_data[ref_data["Doctor"] == st.session_state.d_box]["Clinic"].iloc[0]
                st.session_state.c_box = cln

        sel_clinic = st.selectbox("Clinic(병원명)", clinic_list, key="c_box", on_change=update_from_clinic)
        sel_doctor = st.selectbox("Doctor(의사명)", doctor_list, key="d_box", on_change=update_from_doctor)
        
        # 인보이스용 데이터 추출
        current_clinic = st.session_state.c_box
        current_doctor = st.session_state.d_box
        
        if current_clinic != "선택":
            info = ref_data[ref_data["Clinic"] == current_clinic].iloc[0]
            clinic_addr = info["Address"]
            clinic_phone = info["Phone"]
            clinic_reg = info["Region"]
        else:
            clinic_addr, clinic_phone, clinic_reg = "", "", "Courier"

    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        rec_date = st.date_input("접수일(Received Date)", date.today())
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("요청일 (Due Date)", date.today() + timedelta(days=7))
    with col3: lab_done_date = st.date_input("완료일 (Lab Done)", date.today() + timedelta(days=1))
    with col4:
        ship_days = 1 if clinic_reg == "Local" else 2
        ship_date = get_business_day(due_date, ship_days)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("💾 케이스 저장"):
        if current_clinic == "선택" or not case_no:
            st.error("Case No와 병원/의사를 선택해주세요.")
        else:
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": current_clinic, 
                "Doctor": current_doctor, "Address": clinic_addr, "Phone": clinic_phone,
                "Material": material, "Arch": arch, "Status": "진행중"
            })
            st.success("등록 완료!")

with tab2:
    # 리스트 및 인보이스 출력 (v3.6과 동일)
    for i, row in enumerate(st.session_state.db):
        c_st, c_inf, c_btn = st.columns([1, 3, 2])
        with c_st: st.write("🟡" if row['Status']=="진행중" else "🟢")
        with c_inf: st.write(f"**{row['Case No']}** | {row['Patient']} ({row['Clinic']})")
        with c_btn:
            if st.button("완료" if row['Status']=="진행중" else "복구", key=f"btn_{i}"):
                st.session_state.db[i]['Status'] = "완료" if row['Status']=="진행중" else "진행중"
                st.rerun()
            if st.button("인보이스", key=f"inv_{i}"):
                st.session_state.selected_invoice = row

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.markdown('<div class="invoice-wrapper">', unsafe_allow_html=True)
        # 인보이스 HTML 생략(v3.6과 동일한 레터지 비율 디자인)
        st.markdown('</div>', unsafe_allow_html=True)
