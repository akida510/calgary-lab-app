import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [디자인 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 기본 테마 설정 */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    /* 입력창 및 버튼 스타일 */
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    .stButton > button {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important; width: 100%; font-weight: bold;
    }

    /* Letter 용지 비율 적용 (8.5 x 11 inch) */
    .invoice-container {
        width: 100%;
        display: flex;
        justify-content: center;
        padding: 20px 0;
        overflow-x: auto;
    }

    .invoice-paper {
        background-color: #ffffff !important; 
        width: 816px;       
        height: 1056px;     
        min-width: 816px;
        padding: 60px 70px; 
        border: 1px solid #ddd; 
        font-family: 'Arial', sans-serif;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        position: relative;
        box-sizing: border-box;
    }

    /* 인보이스 내 모든 텍스트 강제 검정색 */
    .invoice-paper * { color: #000000 !important; }

    /* [모바일] 폰 화면에서 Letter 용지 전체가 보이도록 자동 축소 */
    @media (max-width: 850px) {
        .invoice-container { justify-content: flex-start; padding-left: 10px; }
        .invoice-paper {
            transform: scale(0.42); 
            transform-origin: top left;
            margin-bottom: -600px; 
        }
    }
    
    /* 인보이스 세부 디자인 */
    .inv-header { display: flex; justify-content: space-between; margin-bottom: 50px; }
    .logo-main { font-size: 55px; font-weight: 900; font-style: italic; color: #1a4e8a !important; letter-spacing: -3px; line-height: 1; margin:0; }
    .info-right { text-align: right; }
    .info-right h1 { font-size: 40px; margin: 0 0 5px 0; font-weight: 500; letter-spacing: 2px; }
    
    .patient-line { 
        margin-top: 30px; padding: 15px 0;
        border-top: 2.5px solid black; border-bottom: 2.5px solid black;
        font-size: 20px; font-weight: bold;
    }
    
    .item-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    .item-table th { border-bottom: 1px solid black; padding: 12px 0; text-align: left; font-size: 16px; }
    .item-table td { padding: 25px 0; font-size: 17px; }

    /* 하단 안내문구 위치 고정 */
    .invoice-footer {
        position: absolute;
        bottom: 60px;
        left: 70px;
        right: 70px;
    }
    
    .total-line { display: flex; justify-content: space-between; font-weight: bold; font-size: 20px; margin-bottom: 40px; }
    .notice-box { border: 1.5px solid black; padding: 25px; text-align: center; }
    .notice-box u { font-weight: bold; font-size: 16px; display: block; margin-bottom: 10px; }
    .notice-box p { font-size: 12.5px; line-height: 1.5; margin: 0; }

    @media print {
        @page { size: letter; margin: 0; }
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-paper { 
            transform: scale(1) !important;
            border: none !important; margin: 0 !important; width: 100% !important; height: auto !important;
            box-shadow: none !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [로직 영역]
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Address": "205-7136 11 St NE, Calgary, AB", "Phone": "(403) 970-0600"},
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Amhipreat Kaur", "Address": "13510 177 St NW, Edmonton, AB", "Phone": "(780) 455-6806"}
])

tab1, tab2, tab3 = st.tabs(["📝 Case Entry", "📊 Management", "🔍 Search"])

with tab1:
    st.markdown("### 📋 Case Information")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No", placeholder="e.g. IT30")
        patient = st.text_input("Patient Name")
        clinics = sorted(ref_data['Clinic'].tolist())
        sel_clinic = st.selectbox("Clinic", ["Select Clinic"] + clinics)
    with c2:
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    if st.button("💾 SAVE CASE"):
        if sel_clinic == "Select Clinic" or not case_no:
            st.error("Please fill in all fields.")
        else:
            info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": info['Doctor'], "Address": info['Address'], "Phone": info['Phone'],
                "Material": material, "Arch": arch
            })
            st.success("Successfully Saved.")

with tab2:
    for i, row in enumerate(st.session_state.db):
        c_i, c_b = st.columns([4, 1])
        with c_i: st.write(f"**{row['Case No']}** | {row['Patient']} | {row['Clinic']}")
        with c_b:
            if st.button("View Invoice", key=f"v_{i}"):
                st.session_state.selected_invoice = st.session_state.db[i]
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        
        invoice_html = f"""
        <div class="invoice-container">
            <div class="invoice-paper">
                <div class="inv-header">
                    <div>
                        <p style="font-size:11px; font-weight:bold;">DENTAL TECHNOLOGY LTD</p>
                        <h1 class="logo-main">skycad</h1>
                        <p style="font-size:15px; margin-top:8px;">Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</p>
                    </div>
                    <div class="info-right">
                        <h1>INVOICE</h1>
                        <p style="font-size:18px;">No. 162084</p>
                        <p style="font-size:16px;">{date.today().strftime('%B %-d, %Y')}</p>
                        <div class="ship-to" style="margin-top:35px; line-height:1.5; font-size:15px;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Address']}<br>{inv['Phone']}
                        </div>
                    </div>
                </div>
                <div class="patient-line">Patient: &nbsp; {inv['Patient'].upper()}</div>
                <table class="item-table">
                    <thead><tr><th style="width:75%;">Description</th><th style="text-align:right;">Amount</th></tr></thead>
                    <tbody><tr><td>Nightguard ({inv['Material']}) {inv['Arch']}</td><td style="text-align:right;">$180.00</td></tr></tbody>
                </table>
                <div class="invoice-footer">
                    <div class="total-line"><div>{inv['Case No']}</div><div>Total: $180.00</div></div>
                    <div class="notice-box">
                        <u>All dental products we offer are custom made in Canada.</u>
                        <p>Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Thank you for your business.</p>
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
        if st.button("🖨️ PRINT INVOICE"):
            st.write('<script>window.print();</script>', unsafe_allow_html=True)gion": "Local"},
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Amhipreat Kaur", "Address": "13510 177 St NW, Edmonton, AB", "Phone": "(780) 455-6806", "Region": "Courier"}
])

tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트/완료", "🔍 검색"])

with tab1:
    st.markdown("### 📋 기본정보입력")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No", placeholder="예: IT30")
        patient = st.text_input("Patient")
        clinics = sorted(list(set(ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic", ["선택"] + clinics)
        docs = ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "선택" else []
        sel_doctor = st.selectbox("Doctor", ["선택"] + docs)
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    if st.button("💾 저장 및 등록"):
        if sel_clinic == "선택" or not case_no:
            st.error("정보를 입력하세요.")
        else:
            info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Address": info['Address'], "Phone": info['Phone'],
                "Material": material, "Arch": arch
            })
            st.success("등록 완료!")

with tab2:
    for i, row in enumerate(st.session_state.db):
        c_i, c_b = st.columns([4, 1])
        with c_i: st.write(f"**{row['Case No']}** | {row['Patient']} | {row['Clinic']}")
        with c_b:
            if st.button("인보이스 보기", key=f"v_{i}"):
                st.session_state.selected_invoice = st.session_state.db[i]
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        
        invoice_html = f"""
        <div class="invoice-container">
            <div class="invoice-paper">
                <div class="inv-header">
                    <div>
                        <p style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY LTD</p>
                        <h1 class="logo-main">skycad</h1>
                        <p style="font-size:14px;">Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</p>
                    </div>
                    <div class="info-right">
                        <h1>INVOICE</h1>
                        <p>No. 162084</p>
                        <p>{date.today().strftime('%-m/%-d/%Y')}</p>
                        <div class="ship-to" style="margin-top:25px;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Address']}<br>{inv['Phone']}
                        </div>
                    </div>
                </div>
                <div class="patient-line">Patient: &nbsp; {inv['Patient'].upper()}</div>
                <table class="item-table">
                    <thead><tr><th>Description</th><th style="text-align:right;">Amount</th></tr></thead>
                    <tbody><tr><td>Nightguard ({inv['Material']}) {inv['Arch']}</td><td style="text-align:right;">$180.00</td></tr></tbody>
                </table>
                <div class="bottom-section">
                    <div class="total-line"><div>{inv['Case No']}</div><div>Total: $180.00</div></div>
                    <div class="notice-box">
                        <u>All dental products we offer are custom made in Canada.</u>
                        <p>Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Thank you.</p>
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
        if st.button("🖨️ 인쇄하기"):
            st.write('<script>window.print();</script>', unsafe_allow_html=True)
