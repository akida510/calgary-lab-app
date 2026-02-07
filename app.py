import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [수정 금지] 디자인 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    /* 모바일 가독성 확보 */
    label p, .stMarkdown p, .stMetric p, p, span { color: #ffffff !important; }
    
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }

    /* 실제 인보이스 스타일 */
    .invoice-container {
        background-color: white !important; color: black !important;
        padding: 40px; border-radius: 2px; font-family: 'Arial', sans-serif;
        max-width: 800px; margin: 0 auto; border: 1px solid #ccc;
    }
    .invoice-container p, .invoice-container b, .invoice-container span, 
    .invoice-container h1, .invoice-container h2, .invoice-container div {
        color: black !important;
    }
    .inv-grid { display: flex; justify-content: space-between; }
    .inv-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
    .inv-table th { border-bottom: 2px solid black; text-align: left; padding: 5px; }
    .inv-table td { border-bottom: 1px solid #eee; padding: 10px 5px; }
    
    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown { display: none !important; }
        .invoice-container { border: none !important; margin: 0 !important; width: 100% !important; }
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
st.markdown(f'<div class="header-container"><div style="font-size: 24px; font-weight: 800; color:white;">🦷 Skycad Lab Night Guard Manager</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료", "🔍 검색"])

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
        today = date.today()
        if is_3d:
            st.text_input("접수일", value=today.strftime("%Y-%m-%d"), disabled=True)
            rec_date = today
        else:
            rec_date = st.date_input("접수일", today)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("요청일 (Due Date)", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("완료일 (Lab Done)", today + timedelta(days=1))
    with col4:
        ship_date = get_business_day(due_date, 1 if (sel_clinic != "선택" and ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0]=="Local") else 2)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("💾 케이스 저장 (접수 완료)"):
        if sel_clinic == "선택" or not case_no:
            st.error("Case No와 Clinic은 필수입니다.")
        else:
            new_case = {
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Material": material, "Arch": arch,
                "Received": rec_date, "Due": due_date, "Lab Done": lab_done_date, "Status": "Pending"
            }
            st.session_state.db.append(new_case)
            st.success(f"{case_no}번 등록 완료!")

with tab2:
    st.subheader("📊 작업 진행 리스트")
    for i, row in enumerate(st.session_state.db):
        c_info, c_btn = st.columns([4, 1])
        with c_info:
            st.markdown(f"**{'🟡' if row['Status']=='Pending' else '🟢'} {row['Case No']}** | {row['Patient']} | {row['Clinic']}")
        with c_btn:
            if st.button(f"완료/인보이스", key=f"inv_{i}"):
                st.session_state.db[i]['Status'] = "Completed"
                st.session_state.selected_invoice = st.session_state.db[i]
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        # 요청하신 기본 금액 180.00 반영
        invoice_html = f"""
        <div class="invoice-container">
            <div class="inv-grid">
                <div>
                    <h2 style="color:#0056b3 !important; margin:0;">skycad</h2>
                    <p style="font-size:12px; margin:0;">Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9</p>
                </div>
                <div style="text-align: right;">
                    <h1 style="margin:0;">INVOICE</h1>
                    <p style="margin:0;">{date.today().strftime('%m/%d/%Y')}</p>
                    <br>
                    <p style="margin:0; font-size:13px;"><b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}</p>
                </div>
            </div>
            <p style="margin-top:30px;"><b>Patient:</b> {inv['Patient'].upper()}</p>
            <table class="inv-table">
                <thead><tr><th>Description</th><th style="text-align:right;">Amount</th></tr></thead>
                <tbody>
                    <tr>
                        <td>Nightguard ({inv['Material']}) {inv['Arch'].upper()}</td>
                        <td style="text-align:right;">$180.00</td>
                    </tr>
                </tbody>
            </table>
            <div class="inv-grid" style="margin-top:50px; font-weight:bold;">
                <div>{inv['Case No']}</div>
                <div>Total: $180.00</div>
            </div>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
        if st.button("🖨️ 인쇄하기"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
