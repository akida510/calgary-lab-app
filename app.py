import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [수정 금지] 디자인 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    label p, .stMarkdown p, p, span { color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    input:disabled { background-color: #262730 !important; color: #aaaaaa !important; }

    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; }

    /* 인보이스 출력 스타일 (사진 복사) */
    .invoice-paper {
        background-color: white !important; color: black !important;
        padding: 50px; border: 1px solid #eee; font-family: 'Arial', sans-serif;
        width: 100%; max-width: 800px; margin: 0 auto;
    }
    .invoice-paper * { color: black !important; margin: 0; }
    .inv-header { display: flex; justify-content: space-between; margin-bottom: 30px; }
    .logo-area h1 { font-size: 42px; color: #1a4a8a !important; font-style: italic; font-weight: 900; }
    .patient-area { border-top: 2px solid black; border-bottom: 2px solid black; padding: 12px 0; margin: 20px 0; font-weight: bold; }
    .footer-box { border: 1px solid black; padding: 15px; margin-top: 30px; text-align: center; }
    
    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-paper { border: none !important; padding: 0 !important; width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [로직 영역] 데이터 및 날짜 계산
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

# 병원 레퍼런스 데이터 (주소 정보 추가 예정)
ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Address": "Calgary, AB", "Phone": "(403) 000-0000"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier", "Address": "Edmonton, AB", "Phone": "(780) 000-0000"},
])

def get_business_day(start_date, days_to_subtract):
    curr = start_date
    while days_to_subtract > 0:
        curr -= timedelta(days=1)
        if curr.weekday() < 5: days_to_subtract -= 1
    return curr

# ---------------------------------------------------------
# [메인 화면]
# ---------------------------------------------------------
st.markdown('<div class="header-container"><div style="font-size: 24px; font-weight: 800;">🦷 Skycad Lab Night Guard Manager</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트/완료", "🔍 검색"])

with tab1:
    st.markdown("### 📋 기본정보입력")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: ET33")
        patient = st.text_input("Patient(환자명)")
        clinics = sorted(list(set(ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic(병원명)", ["선택"] + clinics)
        docs = ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "선택" else []
        sel_doctor = st.selectbox("Doctor(의사명)", ["선택"] + docs)
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        if is_3d:
            st.text_input("접수일", value=today.strftime("%Y-%m-%d"), disabled=True)
            rec_date = today
        else:
            rec_date = st.date_input("접수일", today)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Upper", "Lower", "Both"], horizontal=True)

    st.markdown("### 📅 일정 관리") # 복구 완료!
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("요청일 (Due Date)", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("완료일 (Lab Done)", today + timedelta(days=1))
    with col4:
        reg = ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0] if sel_clinic != "선택" else "Courier"
        ship_date = get_business_day(due_date, 1 if reg == "Local" else 2)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("💾 케이스 저장"):
        if sel_clinic == "선택" or not case_no:
            st.error("Case No와 병원명은 필수입니다.")
        else:
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, "Doctor": sel_doctor,
                "Material": material, "Arch": arch, "Due": due_date, "Lab Done": lab_done_date, "Status": "Pending"
            })
            st.success(f"{case_no} 저장 완료!")

with tab2:
    for i, row in enumerate(st.session_state.db):
        c_i, c_b = st.columns([4, 1])
        with c_i: st.write(f"**{row['Case No']}** | {row['Patient']} | {row['Clinic']}")
        with c_b:
            if st.button("완료/인보이스", key=f"v_{i}"):
                st.session_state.db[i]['Status'] = "Completed"
                st.session_state.selected_invoice = st.session_state.db[i]
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        invoice_html = f"""
        <div class="invoice-paper">
            <div class="inv-header">
                <div>
                    <p style="font-size:9px; letter-spacing:1px;">DENTAL TECHNOLOGY LTD</p>
                    <h1>skycad</h1>
                    <p style="font-size:12px;">Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</p>
                </div>
                <div style="text-align:right;">
                    <h2 style="font-size:28px;">INVOICE</h2>
                    <p>No. 162084</p><p>{date.today().strftime('%-m/%-d/%Y')}</p><br>
                    <p style="font-size:13px;"><b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}</p>
                </div>
            </div>
            <div class="patient-area">Patient: &nbsp; {inv['Patient'].upper()}</div>
            <table style="width:100%; margin: 20px 0; border-collapse:collapse;">
                <thead><tr style="border-bottom:1px solid black;"><th style="text-align:left; padding-bottom:5px;">Description</th><th style="text-align:right; padding-bottom:5px;">Amount</th></tr></thead>
                <tbody><tr><td style="padding-top:10px;">Nightguard ({inv['Material']}) {inv['Arch'].upper()}</td><td style="text-align:right; padding-top:10px;">$180.00</td></tr></tbody>
            </table>
            <div style="display:flex; justify-content:space-between; font-weight:bold; margin-top:80px;">
                <div>{inv['Case No']}</div><div>Total: $180.00</div>
            </div>
            <div class="footer-box">
                <p style="text-decoration:underline; font-weight:bold; margin-bottom:10px;">All dental products we offer are custom made in Canada.</p>
                <p style="font-size:11px;">Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.552% APR, Thank you.</p>
            </div>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
        st.button("🖨️ 인보이스 출력", on_click=None)
