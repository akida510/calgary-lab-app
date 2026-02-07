import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [디자인 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 기본 테마 설정 */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    label p, .stMarkdown p, p, span { color: #ffffff !important; }
    
    /* 입력창 스타일 */
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    input:disabled { background-color: #262730 !important; color: #aaaaaa !important; }

    /* [추가] 버튼 가독성 수정 (모바일 대응) */
    .stButton > button {
        background-color: #1a1c24 !important;
        color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
        width: 100%; /* 모바일에서 누르기 편하게 넓게 설정 */
    }
    .stButton > button:hover {
        border-color: #1a4e8a !important;
        color: #1a4e8a !important;
    }

    /* 인보이스 종이 디자인 (원본 유지) */
    .invoice-paper {
        background-color: white !important; 
        padding: 50px; border: 1px solid #000; font-family: 'Arial', sans-serif;
        width: 100%; max-width: 800px; margin: 20px auto; line-height: 1.2;
    }
    
    .invoice-paper, .invoice-paper div, .invoice-paper p, .invoice-paper span, 
    .invoice-paper b, .invoice-paper u, .invoice-paper h1, .invoice-paper h2, 
    .invoice-paper table, .invoice-paper td, .invoice-paper th {
        color: #000000 !important; 
    }
    
    .inv-header { display: flex; justify-content: space-between; margin-bottom: 40px; }
    .logo-main { font-size: 50px; font-weight: 900; font-style: italic; color: #1a4e8a !important; letter-spacing: -2px; }
    .info-right { text-align: right; }
    .info-right h1 { font-size: 35px; margin-bottom: 5px; font-weight: 500; }
    
    .patient-line { 
        margin-top: 20px; padding: 15px 0;
        border-top: 2px solid black; border-bottom: 2px solid black;
        font-size: 18px; font-weight: bold;
    }
    
    .item-table { width: 100%; border-collapse: collapse; margin-top: 10px; min-height: 200px; }
    .item-table th { border-bottom: 1px solid black; padding: 10px 0; text-align: left; }
    .item-table td { padding: 20px 0; font-size: 16px; }

    .bottom-section { margin-top: 50px; }
    .total-line { display: flex; justify-content: space-between; font-weight: bold; font-size: 18px; margin-bottom: 30px; }
    
    .notice-box { border: 1.5px solid black; padding: 20px; text-align: center; background-color: #ffffff !important; }
    .notice-box u { font-weight: bold; font-size: 16px; display: block; margin-bottom: 10px; text-decoration: underline !important; }
    .notice-box p { font-size: 12px; line-height: 1.4; font-weight: 500; }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-paper { border: none !important; width: 100% !important; margin: 0 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 이하 로직 및 탭 구성은 원본 코드와 100% 동일합니다.
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Address": "205-7136 11 St NE, Calgary, AB", "Phone": "(403) 970-0600", "Region": "Local"},
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Amhipreat Kaur", "Address": "13510 177 St NW, Edmonton, AB", "Phone": "(780) 455-6806", "Region": "Courier"}
])

def get_business_day(start_date, days_to_subtract):
    curr = start_date
    while days_to_subtract > 0:
        curr -= timedelta(days=1)
        if curr.weekday() < 5: days_to_subtract -= 1
    return curr

tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트/완료", "🔍 검색"])

with tab1:
    st.markdown("### 📋 기본정보입력")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: IT30")
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

    if st.button("💾 저장 및 등록"):
        if sel_clinic == "선택" or not case_no:
            st.error("필수 정보를 입력하세요.")
        else:
            clinic_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Address": clinic_info['Address'], "Phone": clinic_info['Phone'],
                "Material": material, "Arch": arch, "Lab Done": lab_done_date, "Status": "Pending"
            })
            st.success(f"{case_no}번 케이스 등록 완료!")

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
                    <p style="font-size:9px; font-weight:bold;">DENTAL TECHNOLOGY LTD</p>
                    <h1 class="logo-main">skycad</h1>
                    <p style="font-size:13px;">Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</p>
                </div>
                <div class="info-right">
                    <h1>INVOICE</h1>
                    <p>No. 162084</p>
                    <p>{date.today().strftime('%-m/%-d/%Y')}</p>
                    <div class="ship-to" style="margin-top:20px;">
                        <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Address']}<br>{inv['Phone']}
                    </div>
                </div>
            </div>
            <div class="patient-line">Patient: &nbsp; {inv['Patient'].upper()}</div>
            <table class="item-table">
                <thead><tr><th style="text-align:left;">Description</th><th style="text-align:right;">Amount</th></tr></thead>
                <tbody><tr><td style="padding:20px 0;">Nightguard ({inv['Material']}) {inv['Arch']}</td><td style="text-align:right;">$180.00</td></tr></tbody>
            </table>
            <div class="bottom-section">
                <div class="total-line"><div>{inv['Case No']}</div><div>Total: $180.00</div></div>
                <div class="notice-box">
                    <u>All dental products we offer are custom made in Canada.</u>
                    <p>Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.552% APR, Thank you.</p>
                </div>
            </div>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
        if st.button("🖨️ 인쇄하기"):
            st.write('<script>window.print();</script>', unsafe_allow_html=True)
