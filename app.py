import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [디자인 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    label p, .stMarkdown p, p, span { color: #ffffff !important; }
    
    /* 레터 용지 비율 컨테이너 (8.5 : 11) */
    .invoice-wrapper {
        display: flex; justify-content: center; padding: 20px; background-color: #262730;
    }
    .invoice-paper {
        background-color: white !important; 
        width: 100%; 
        max-width: 750px; /* 레터지 폭 기준 */
        aspect-ratio: 8.5 / 11; /* 레터 용지 비율 고정 */
        padding: 40px 50px; 
        border: 1px solid #000;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        display: flex; flex-direction: column;
        box-sizing: border-box;
    }
    
    /* 인보이스 내부 검정 글자 강제 고정 */
    .invoice-paper * { color: #000000 !important; font-family: 'Arial', sans-serif; }
    
    .inv-header { display: flex; justify-content: space-between; margin-bottom: 30px; }
    .logo-main { font-size: 55px; font-weight: 900; font-style: italic; color: #1a4e8a !important; letter-spacing: -3px; line-height: 1; }
    .patient-line { 
        margin: 20px 0; padding: 12px 0; border-top: 2px solid black; border-bottom: 2px solid black;
        font-size: 18px; font-weight: bold;
    }
    .item-table { width: 100%; border-collapse: collapse; flex-grow: 1; margin-top: 10px; }
    .item-table th { border-bottom: 1.5px solid black; text-align: left; padding: 8px 0; }
    .item-table td { padding: 15px 0; vertical-align: top; font-size: 16px; }

    .bottom-box { margin-top: auto; } /* 안내문구를 항상 종이 하단에 배치 */
    .total-line { display: flex; justify-content: space-between; font-weight: bold; font-size: 18px; padding: 10px 0; }
    .notice-box { border: 1.5px solid black; padding: 15px; text-align: center; }
    .notice-box u { font-weight: bold; display: block; margin-bottom: 8px; }
    .notice-box p { font-size: 11px; line-height: 1.4; }

    /* 모바일 가독성: 폰에서는 비율 유지하며 축소 */
    @media (max-width: 600px) {
        .invoice-paper { padding: 20px 25px; }
        .logo-main { font-size: 40px; }
        .patient-line { font-size: 15px; }
    }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown { display: none !important; }
        .invoice-wrapper { padding: 0; background: none; }
        .invoice-paper { border: none; box-shadow: none; width: 100%; max-width: none; aspect-ratio: auto; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [로직 영역]
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트/완료", "🔍 검색"])

with tab1:
    st.markdown("### 📋 케이스 등록")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: IT30")
        patient = st.text_input("Patient(환자명)")
        clinic = st.text_input("Clinic(병원명)")
        doctor = st.text_input("Doctor(의사명)")
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        rec_date = st.date_input("접수일(Received Date)", date.today())
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("요청일 (Due Date)", date.today() + timedelta(days=7))
    with col3: lab_done_date = st.date_input("완료일 (Lab Done)", date.today() + timedelta(days=1))
    with col4: st.date_input("출고일 (Shipping Date)", due_date - timedelta(days=1))

    if st.button("💾 케이스 저장"):
        st.session_state.db.append({
            "Case No": case_no, "Patient": patient, "Clinic": clinic, "Doctor": doctor,
            "Material": material, "Arch": arch, "Status": "진행중"
        })
        st.success("등록 완료!")

with tab2:
    for i, row in enumerate(st.session_state.db):
        c_st, c_inf, c_btn = st.columns([1, 3, 2])
        with c_st: st.write("🟡" if row['Status']=="진행중" else "🟢")
        with c_inf: st.write(f"**{row['Case No']}** | {row['Patient']}")
        with c_btn:
            ca, cb = st.columns(2)
            with ca:
                if st.button("완료" if row['Status']=="진행중" else "복구", key=f"btn_{i}"):
                    st.session_state.db[i]['Status'] = "완료" if row['Status']=="진행중" else "진행중"
                    st.rerun()
            with cb:
                if st.button("인보이스", key=f"inv_{i}"):
                    st.session_state.selected_invoice = row

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.markdown('<div class="invoice-wrapper">', unsafe_allow_html=True)
        invoice_html = f"""
        <div class="invoice-paper">
            <div class="inv-header">
                <div>
                    <p style="font-size:9px; font-weight:bold;">DENTAL TECHNOLOGY LTD</p>
                    <h1 class="logo-main">skycad</h1>
                    <p style="font-size:13px;">Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</p>
                </div>
                <div style="text-align:right;">
                    <h1 style="font-size:32px;">INVOICE</h1>
                    <p>No. 162084</p><p>{date.today().strftime('%-m/%-d/%Y')}</p><br>
                    <div style="text-align:left; float:right;"><b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}</div>
                </div>
            </div>
            <div class="patient-line">Patient: &nbsp; {inv['Patient'].upper()}</div>
            <table class="item-table">
                <thead><tr><th>Description</th><th style="text-align:right;">Amount</th></tr></thead>
                <tbody><tr><td>Nightguard ({inv['Material']}) {inv['Arch']}</td><td style="text-align:right;">$180.00</td></tr></tbody>
            </table>
            <div class="bottom-box">
                <div class="total-line"><div>{inv['Case No']}</div><div>Total: $180.00</div></div>
                <div class="notice-box">
                    <u>All dental products we offer are custom made in Canada.</u>
                    <p>Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.552% APR, Thank you.</p>
                </div>
            </div>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("🖨️ PDF로 저장 / 인쇄"):
             st.write('<script>window.print();</script>', unsafe_allow_html=True)
