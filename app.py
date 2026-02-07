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

    /* [핵심] 사진과 똑같은 인보이스 레이아웃 */
    .invoice-paper {
        background-color: white !important; color: black !important;
        padding: 60px 50px; border: 1px solid #000; font-family: 'Helvetica', 'Arial', sans-serif;
        width: 100%; max-width: 850px; margin: 0 auto; min-height: 1000px;
        position: relative;
    }
    .invoice-paper * { color: black !important; margin: 0; padding: 0; line-height: 1.2; }
    
    /* 상단 영역 */
    .top-section { display: flex; justify-content: space-between; margin-bottom: 50px; }
    
    /* 로고 텍스트 스타일링 */
    .logo-container { position: relative; }
    .logo-small { font-size: 8px; font-weight: bold; letter-spacing: 0.5px; margin-bottom: -5px; }
    .logo-main { font-size: 52px; font-weight: 900; font-style: italic; color: #1a4e8a !important; letter-spacing: -2px; }
    .company-info { font-size: 13px; margin-top: 5px; line-height: 1.4; }
    
    /* 우측 상단 정보 */
    .info-right { text-align: right; }
    .info-right h1 { font-size: 32px; font-weight: 400; margin-bottom: 5px; }
    .info-right p { font-size: 14px; margin-bottom: 2px; }
    .ship-to { margin-top: 25px; font-size: 14px; text-align: left; float: right; width: 220px; }
    .ship-to b { display: block; margin-bottom: 5px; }

    /* 중앙 환자 영역 */
    .patient-line { 
        clear: both; margin-top: 160px; padding: 12px 0;
        border-top: 1.5px solid black; border-bottom: 1.5px solid black;
        font-size: 16px; font-weight: bold;
    }
    
    /* 테이블 영역 */
    .item-table { width: 100%; margin-top: 10px; border-collapse: collapse; }
    .item-table th { text-align: left; border-bottom: 1px solid #ccc; padding: 5px 0; font-size: 15px; }
    .item-table td { padding: 15px 0; font-size: 15px; }
    
    /* 하단 금액 및 박스 */
    .bottom-section { margin-top: 350px; }
    .total-line { display: flex; justify-content: space-between; font-weight: bold; font-size: 16px; margin-bottom: 30px; }
    
    .notice-box { border: 1.5px solid black; padding: 25px 20px; text-align: center; }
    .notice-box u { font-size: 16px; font-weight: bold; display: block; margin-bottom: 12px; }
    .notice-box p { font-size: 11.5px; line-height: 1.5; color: #333 !important; }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-paper { border: none !important; padding: 0 !important; width: 100% !important; max-width: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [데이터 관리]
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Amhipreat Kaur", "Address": "13510 177 St NW, Edmonton, AB TSL 189", "Phone": "(780) 455-6806", "Region": "Courier"},
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Address": "205-7136 11 St NE, Calgary, AB", "Phone": "(403) 970-0600", "Region": "Local"}
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
        case_no = st.text_input("Case No(팬번호)", placeholder="예: ET12")
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
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("요청일 (Due Date)", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("완료일 (Lab Done)", today + timedelta(days=1))
    with col4:
        reg = ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0] if sel_clinic != "선택" else "Courier"
        ship_date = get_business_day(due_date, 1 if reg == "Local" else 2)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("💾 케이스 저장"):
        if sel_clinic == "선택" or not case_no:
            st.error("필수 정보를 입력하세요.")
        else:
            clinic_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Address": clinic_info['Address'], "Phone": clinic_info['Phone'],
                "Material": material, "Arch": arch, "Lab Done": lab_done_date, "Status": "Pending"
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
            <div class="top-section">
                <div class="logo-container">
                    <p class="logo-small">DENTAL TECHNOLOGY LTD</p>
                    <h1 class="logo-main">skycad</h1>
                    <div class="company-info">
                        <b>Skycad AB</b><br>
                        205-7136 11 St NE<br>
                        Calgary, AB T2E 4Y9<br>
                        (403) 970-0600
                    </div>
                </div>
                <div class="info-right">
                    <h1>INVOICE</h1>
                    <p>No. 162084</p>
                    <p>{date.today().strftime('%-m/%-d/%Y')}</p>
                    <div class="ship-to">
                        <b>Ship To:</b>
                        {inv['Clinic']}<br>
                        {inv['Doctor']}<br>
                        {inv['Address']}<br>
                        {inv['Phone']}
                    </div>
                </div>
            </div>

            <div class="patient-line">
                Patient: &nbsp; {inv['Patient'].upper()}
            </div>

            <table class="item-table">
                <thead>
                    <tr><th>Description</th><th style="text-align:right;">Amount</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Nightguard ({inv['Material']}) {inv['Arch']}</td>
                        <td style="text-align:right;">$180.00</td>
                    </tr>
                </tbody>
            </table>

            <div class="bottom-section">
                <div class="total-line">
                    <div>{inv['Case No']}</div>
                    <div>Total: $180.00</div>
                </div>
                <div class="notice-box">
                    <u>All dental products we offer are custom made in Canada.</u>
                    <p>Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.552% APR, Thank you.</p>
                </div>
            </div>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
        st.button("🖨️ 인쇄 / PDF 저장")
