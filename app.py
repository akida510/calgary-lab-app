import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [수정 금지] 디자인 설정 및 테마 강제 고정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 및 글자색 강제 고정 */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    /* 입력창 및 선택창 글자색 흰색으로 고정 */
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    
    /* 비활성화된 입력창 스타일 */
    input:disabled { background-color: #262730 !important; color: #aaaaaa !important; }
    
    /* 라벨 가독성 확보 */
    label p, .stMarkdown p, .stMetric p, .stTabs [data-baseweb="tab"] p { 
        color: #ffffff !important; font-weight: 600 !important; 
    }

    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    
    .stButton>button { 
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important; 
        color: white !important; font-weight: bold; border-radius: 5px; 
    }

    /* 인보이스 컨테이너: 박스 제거 및 모바일 잘림 방지 */
    .invoice-container {
        background-color: white !important; color: black !important; 
        padding: 30px; border-radius: 0px; font-family: 'Arial', sans-serif;
        max-width: 100%; margin: 0 auto;
    }
    .invoice-container * { color: black !important; }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown { display: none !important; }
        .invoice-container { display: block !important; border: none !important; width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [데이터 관리] 
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier"},
])

def get_business_day(start_date, days_to_subtract):
    current_date = start_date
    while days_to_subtract > 0:
        current_date -= timedelta(days=1)
        if current_date.weekday() < 5: days_to_subtract -= 1
    return current_date

# ---------------------------------------------------------
# [메인 화면]
# ---------------------------------------------------------
st.markdown(f'<div class="header-container"><div style="font-size: 24px; font-weight: 800;">🦷 Skycad Lab Manager</div><div style="font-size: 12px;">Designed By Heechul Jung</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 Case Entry", "📊 Job List", "🔍 Search"])

# --- Tab 1: 케이스 등록 (희철님 원본 로직 보존) ---
with tab1:
    st.markdown("### 📋 Case Information")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="e.g. ET33")
        patient = st.text_input("Patient(환자명)", placeholder="Patient Name")
        clinics = sorted(list(set(ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic(병원명)", ["Select Clinic"] + clinics)
        filtered_docs = ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "Select Clinic" else []
        sel_doctor = st.selectbox("Doctor(의사명)", ["Select Doctor"] + filtered_docs)
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        if is_3d:
            st.text_input("접수일", value=today.strftime("%Y-%m-%d"), disabled=True)
            rec_date = today
        else:
            rec_date = st.date_input("접수일", today)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

    st.markdown("### 📅 Schedule Management")
    col3, col4, col5 = st.columns(3)
    with col5: 
        due_date = st.date_input("Due Date", today + timedelta(days=7))
    with col3: 
        lab_done_date = st.date_input("Lab Done", today + timedelta(days=1))
    with col4:
        ship_date = get_business_day(due_date, 1 if (sel_clinic != "Select Clinic" and ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0]=="Local") else 2)
        st.date_input("Shipping Date", ship_date)

    if st.button("💾 SAVE CASE"):
        if sel_clinic == "Select Clinic" or not case_no:
            st.error("Case No and Clinic are required.")
        else:
            new_case = {
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Material": material, "Arch": arch,
                "Received": rec_date, "Due": due_date, "Lab Done": lab_done_date, "Status": "Pending"
            }
            st.session_state.db.append(new_case)
            st.success(f"Case {case_no} Registered!")

# --- Tab 2: 리스트 및 완료 (영문 버튼 및 박스 없는 인보이스) ---
with tab2:
    st.subheader("📊 Work Process List")
    if not st.session_state.db:
        st.info("No pending cases.")
    else:
        for i, row in enumerate(st.session_state.db):
            c_info, c_btn = st.columns([4, 1.5])
            with c_info:
                st.markdown(f"**{row['Case No']}** | {row['Patient']} | {row['Clinic']} | Due: {row['Due']}")
            with c_btn:
                if row['Status'] == "Pending":
                    if st.button(f"Complete / Print", key=f"comp_{i}"):
                        st.session_state.db[i]['Status'] = "Completed"
                        st.session_state.selected_invoice = st.session_state.db[i]
                        st.rerun()
                else:
                    if st.button(f"Reprint", key=f"re_{i}"):
                        st.session_state.selected_invoice = st.session_state.db[i]
                        st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        # 박스 테두리 제거된 깔끔한 영문 인보이스
        st.markdown(f"""
        <div class="invoice-container">
            <h2 style="text-align:center;">SKYCAD DENTAL LAB INVOICE</h2>
            <hr style="border: 1px solid black;">
            <p><strong>Case No:</strong> {inv['Case No']} | <strong>Completed:</strong> {inv['Lab Done']}</p>
            <p><strong>Clinic:</strong> {inv['Clinic']} | <strong>Doctor:</strong> {inv['Doctor']}</p>
            <p><strong>Patient:</strong> {inv['Patient']}</p>
            <p><strong>Item:</strong> Night Guard ({inv['Material']}) - {inv['Arch']}</p>
            <hr style="border: 0.5px solid #eee;">
            <p style="text-align:center; font-size: 12px; color: #666;">Thank you for your business.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ PRINT"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3:
    st.write("🔍 Search Function Ready")
