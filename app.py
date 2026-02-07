import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [수정 금지] 디자인 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    input:disabled { background-color: #262730 !important; color: #777777 !important; }
    .stButton>button { width: 100%; height: 3em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 5px; }
    
    /* 인보이스 스타일 */
    .invoice-container {
        background-color: white; color: black; padding: 30px; border-radius: 5px;
        font-family: 'Arial', sans-serif; margin-top: 20px;
    }
    .invoice-header { text-align: center; border-bottom: 2px solid #333; margin-bottom: 20px; }
    
    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown { display: none !important; }
        .invoice-container { display: block !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [데이터 관리] 세션 상태 초기화
# ---------------------------------------------------------
if 'db' not in st.session_state:
    st.session_state.db = []  # 전체 데이터 저장소

if 'selected_invoice' not in st.session_state:
    st.session_state.selected_invoice = None

# 공통 데이터 (병원/의사)
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
st.markdown(f'<div class="header-container"><div style="font-size: 24px; font-weight: 800;">🦷 Skycad Lab Night Guard Manager</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료", "🔍 검색"])

# --- Tab 1: 케이스 등록 ---
with tab1:
    st.markdown("### 📋 기본정보입력")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: ET33")
        patient = st.text_input("Patient(환자명)", placeholder="환자 성함")
        clinics = sorted(list(set(ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic(병원명)", ["선택"] + clinics)
        filtered_docs = ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "선택" else []
        sel_doctor = st.selectbox("Doctor(의사명)", ["선택"] + filtered_docs)
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        rec_date = date.today()
        if is_3d:
            st.text_input("접수일", value=rec_date.strftime("%Y-%m-%d"), disabled=True)
        else:
            rec_date = st.date_input("접수일", date.today())
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("요청일 (Due Date)", date.today() + timedelta(days=7))
    with col4:
        ship_date = get_business_day(due_date, 1 if (sel_clinic != "선택" and ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0]=="Local") else 2)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("💾 케이스 저장 (접수 완료)"):
        if sel_clinic == "선택" or not case_no:
            st.error("필수 정보를 입력하세요.")
        else:
            new_case = {
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Material": material, "Arch": arch,
                "Received": rec_date, "Due": due_date, "Status": "Pending"
            }
            st.session_state.db.append(new_case)
            st.success(f"{case_no}번 케이스가 성공적으로 등록되었습니다.")

# --- Tab 2: 리스트 및 완료 처리 ---
with tab2:
    st.subheader("📊 작업 진행 리스트")
    if not st.session_state.db:
        st.info("현재 대기 중인 케이스가 없습니다.")
    else:
        # 데이터프레임으로 변환
        df = pd.DataFrame(st.session_state.db)
        
        for i, row in df.iterrows():
            col_info, col_btn = st.columns([4, 1])
            with col_info:
                # 상태에 따라 다른 색상 표시
                status_color = "🟡" if row['Status'] == "Pending" else "🟢"
                st.markdown(f"**{status_color} {row['Case No']}** | {row['Patient']} | {row['Clinic']} | Due: {row['Due']}")
            
            with col_btn:
                if row['Status'] == "Pending":
                    if st.button(f"완료 및 인보이스", key=f"btn_{i}"):
                        st.session_state.db[i]['Status'] = "Completed"
                        st.session_state.db[i]['Done Date'] = date.today()
                        st.session_state.selected_invoice = st.session_state.db[i]
                        st.rerun()
                else:
                    if st.button(f"인보이스 재출력", key=f"re_{i}"):
                        st.session_state.selected_invoice = st.session_state.db[i]
                        st.rerun()

    # 인보이스 미리보기 영역 (선택된 경우에만 표시)
    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        st.markdown("### 📑 Invoice Preview")
        invoice_html = f"""
        <div class="invoice-container">
            <div class="invoice-header"><h1>SKYCAD DENTAL LAB</h1><p>Invoice / Statement</p></div>
            <p><strong>Case No:</strong> {inv['Case No']} | <strong>Date:</strong> {inv.get('Done Date', date.today())}</p>
            <p><strong>Clinic:</strong> {inv['Clinic']} | <strong>Doctor:</strong> {inv['Doctor']}</p>
            <p><strong>Patient:</strong> {inv['Patient']}</p>
            <hr>
            <p><strong>Description:</strong> Night Guard ({inv['Material']}) - {inv['Arch']}</p>
            <p style="text-align:center; margin-top:30px; font-size:12px; color:gray;">Thank you for your business.</p>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
        if st.button("🖨️ 이 인보이스 출력하기"):
            st.write('<script>window.print();</script>', unsafe_allow_html=True)

with tab3:
    st.write("🔍 검색 기능 준비 중")
