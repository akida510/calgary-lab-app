import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [수정 금지] 디자인 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    label p, .stMarkdown p, p, span { color: #ffffff !important; }

    /* 인보이스 출력 전용 스타일 (흰 종이 레이아웃) */
    .invoice-paper {
        background-color: white !important; color: black !important;
        padding: 50px; border: 1px solid black; font-family: 'Arial', sans-serif;
        width: 100%; max-width: 800px; margin: 0 auto; line-height: 1.3;
    }
    .invoice-paper * { color: black !important; margin: 0; padding: 0; }
    
    .inv-header { display: flex; justify-content: space-between; margin-bottom: 40px; }
    .logo-area h1 { font-size: 45px; color: #0056b3 !important; font-style: italic; }
    .logo-area p { font-size: 14px; font-weight: bold; }
    
    .ship-to { text-align: right; font-size: 14px; }
    .ship-to h2 { font-size: 28px; margin-bottom: 10px; }
    
    .patient-area { border-top: 2px solid black; border-bottom: 2px solid black; padding: 15px 0; margin: 20px 0; font-size: 16px; }
    
    .item-table { width: 100%; border-collapse: collapse; min-height: 300px; }
    .item-table th { border-bottom: 1px solid black; padding: 10px 0; text-align: left; }
    .item-table td { padding: 15px 0; vertical-align: top; }
    
    .footer-box { border: 2px solid black; padding: 20px; margin-top: 30px; text-align: center; }
    .footer-box h3 { text-decoration: underline; margin-bottom: 15px; font-size: 18px; }
    .footer-box p { font-size: 12px; line-height: 1.5; }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown { display: none !important; }
        .invoice-paper { border: none !important; padding: 0 !important; width: 100% !important; max-width: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [데이터 관리]
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

# ---------------------------------------------------------
# [메인 화면]
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트/완료", "🔍 검색"])

with tab1:
    st.markdown("### 📋 기본정보입력")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)")
        patient = st.text_input("Patient(환자명)")
        clinic = st.text_input("Clinic(병원명)")
    with c2:
        doctor = st.text_input("Doctor(의사명)")
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Upper", "Lower", "Both"], horizontal=True)

    if st.button("💾 저장"):
        st.session_state.db.append({
            "Case No": case_no, "Patient": patient, "Clinic": clinic, 
            "Doctor": doctor, "Material": material, "Arch": arch, "Status": "Pending"
        })
        st.success("저장되었습니다.")

with tab2:
    for i, row in enumerate(st.session_state.db):
        col_inf, col_btn = st.columns([4, 1])
        with col_inf: st.write(f"{row['Case No']} | {row['Patient']} | {row['Clinic']}")
        with col_btn:
            if st.button("완료 및 인보이스", key=f"inv_{i}"):
                st.session_state.selected_invoice = row
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        
        # 사진과 똑같은 HTML 구조
        invoice_html = f"""
        <div class="invoice-paper">
            <div class="inv-header">
                <div class="logo-area">
                    <p style="font-size:10px;">DENTAL TECHNOLOGY LTD</p>
                    <h1>skycad</h1>
                    <p>Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</p>
                </div>
                <div class="ship-to">
                    <h2>INVOICE</h2>
                    <p>No. 162084</p>
                    <p>{date.today().strftime('%-m/%-d/%Y')}</p>
                    <br><br>
                    <p><b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>병원 주소 및 전화번호 (추후 데이터 연동)</p>
                </div>
            </div>

            <div class="patient-area">
                <b>Patient:</b> {inv['Patient'].upper()}
            </div>

            <table class="item-table">
                <thead>
                    <tr><th>Description</th><th style="text-align:right;">Amount</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Nightguard ({inv['Material']}) {inv['Arch'].upper()}</td>
                        <td style="text-align:right;">$180.00</td>
                    </tr>
                </tbody>
            </table>

            <div style="display:flex; justify-content:space-between; font-weight:bold; margin-top:20px; font-size:18px;">
                <div>{inv['Case No']}</div>
                <div>Total: $180.00</div>
            </div>

            <div class="footer-box">
                <h3>All dental products we offer are custom made in Canada.</h3>
                <p> Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.552% APR, Thank you.</p>
            </div>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
        if st.button("🖨️ 인보이스 출력"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
