import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [디자인 고정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    /* 인보이스 배경 (화이트 종이) */
    .invoice-paper {
        background-color: white !important; color: black !important;
        padding: 50px; border: 1px solid #000; font-family: 'Arial', sans-serif;
        width: 100%; max-width: 800px; margin: 20px auto; line-height: 1.2;
    }
    .invoice-paper * { color: black !important; margin: 0; padding: 0; }
    
    /* 상단 로고 및 정보 */
    .inv-header { display: flex; justify-content: space-between; margin-bottom: 40px; }
    .logo-main { font-size: 50px; font-weight: 900; font-style: italic; color: #1a4e8a !important; letter-spacing: -2px; }
    .info-right { text-align: right; }
    .info-right h1 { font-size: 35px; margin-bottom: 5px; font-weight: 500; }
    .ship-to { margin-top: 20px; font-size: 14px; text-align: left; border-left: none; }

    /* 환자명 라인 (선 2개) */
    .patient-line { 
        margin-top: 20px; padding: 15px 0;
        border-top: 2px solid black; border-bottom: 2px solid black;
        font-size: 18px; font-weight: bold;
    }
    
    /* 품목 테이블 */
    .item-table { width: 100%; border-collapse: collapse; margin-top: 10px; min-height: 200px; }
    .item-table th { border-bottom: 1px solid black; padding: 10px 0; text-align: left; }
    .item-table td { padding: 20px 0; font-size: 16px; }

    /* 하단 섹션 */
    .bottom-section { margin-top: 50px; }
    .total-line { display: flex; justify-content: space-between; font-weight: bold; font-size: 18px; margin-bottom: 30px; }
    
    /* 안내 문구 박스 */
    .notice-box { border: 1.5px solid black; padding: 20px; text-align: center; }
    .notice-box u { font-weight: bold; font-size: 16px; display: block; margin-bottom: 10px; }
    .notice-box p { font-size: 12px; line-height: 1.4; }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown { display: none !important; }
        .invoice-paper { border: none !important; width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [데이터 및 로직]
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Address": "205-7136 11 St NE, Calgary, AB", "Phone": "(403) 970-0600", "Region": "Local"}
])

# ---------------------------------------------------------
# [UI 화면]
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트/완료", "🔍 검색"])

with tab1:
    st.markdown("### 📋 기본정보입력")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", value="IT30")
        patient = st.text_input("Patient(환자명)", value="Bishop Kelsey")
        sel_clinic = st.selectbox("Clinic(병원명)", ["Calgary Central"])
    with c2:
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    if st.button("💾 저장"):
        st.session_state.db.append({
            "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
            "Material": material, "Arch": arch, "Status": "Pending"
        })
        st.success("저장되었습니다.")

with tab2:
    for i, row in enumerate(st.session_state.db):
        col1, col2 = st.columns([4, 1])
        with col1: st.write(f"**{row['Case No']}** | {row['Patient']}")
        with col2:
            if st.button("완료/인보이스", key=f"v_{i}"):
                st.session_state.selected_invoice = row
                st.rerun()

    # 인보이스 출력 (태그 노출 방지 처리)
    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        
        # HTML 코드를 문자열로 작성
        invoice_content = f"""
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
                    <div class="ship-to">
                        <b>Ship To:</b><br>{inv['Clinic']}<br>Lana Huynh<br>205-7136 11 St NE, Calgary, AB<br>(403) 970-0600
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
        # 이 부분이 핵심: st.markdown과 unsafe_allow_html=True를 사용해야 코드가 아닌 그림으로 보입니다.
        st.markdown(invoice_content, unsafe_allow_html=True)
        
        if st.button("🖨️ 인쇄하기"):
            st.write('<script>window.print();</script>', unsafe_allow_html=True)
