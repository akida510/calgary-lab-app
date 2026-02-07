import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [디자인 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 1. 기본 배경 설정 (어두운 테마) */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    /* 2. 입력창 및 버튼 가독성 개선 (모바일 대응) */
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    .stButton > button {
        background-color: #1a4e8a !important; color: #ffffff !important;
        border: none !important; width: 100%; font-weight: bold; height: 3em;
    }

    /* 3. Letter 용지 규격 및 모바일 자동 축소 */
    .invoice-container {
        width: 100%;
        display: flex;
        justify-content: center;
        padding: 20px 0;
        overflow-x: auto;
    }

    .invoice-paper {
        background-color: #ffffff !important; 
        width: 816px; height: 1056px; min-width: 816px; /* Letter Size */
        padding: 60px 70px; border: 1px solid #ddd; 
        font-family: 'Arial', sans-serif;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        position: relative; box-sizing: border-box;
    }

    /* 인보이스 내 모든 텍스트 강제 검정색 고정 (흰바탕 대비) */
    .invoice-paper * { color: #000000 !important; }

    @media (max-width: 850px) {
        .invoice-container { justify-content: flex-start; }
        .invoice-paper {
            transform: scale(0.4); transform-origin: top left;
            margin-bottom: -630px; /* 축소 후 여백 보정 */
        }
    }
    
    /* 인보이스 내부 레이아웃 */
    .inv-header { display: flex; justify-content: space-between; margin-bottom: 50px; }
    .logo-main { font-size: 55px; font-weight: 900; font-style: italic; color: #1a4e8a !important; letter-spacing: -3px; line-height: 1; margin:0; }
    .info-right { text-align: right; }
    
    .patient-line { 
        margin-top: 30px; padding: 15px 0;
        border-top: 2.5px solid black; border-bottom: 2.5px solid black;
        font-size: 20px; font-weight: bold;
    }
    
    .item-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    .item-table th { border-bottom: 1px solid black; padding: 12px 0; text-align: left; }
    .item-table td { padding: 25px 0; font-size: 17px; }

    .invoice-footer { position: absolute; bottom: 60px; left: 70px; right: 70px; }
    .total-line { display: flex; justify-content: space-between; font-weight: bold; font-size: 20px; margin-bottom: 30px; }
    .notice-box { border: 1.5px solid black; padding: 20px; text-align: center; }

    /* 인쇄 설정 */
    @media print {
        @page { size: letter; margin: 0; }
        .stButton, [data-testid="stSidebar"], .stTabs, .stDivider { display: none !important; }
        .invoice-paper { transform: scale(1) !important; border: none !important; margin: 0 !important; box-shadow: none !important; width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [데이터 및 로직]
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Address": "205-7136 11 St NE, Calgary, AB", "Phone": "(403) 970-0600"},
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Amhipreat Kaur", "Address": "13510 177 St NW, Edmonton, AB", "Phone": "(780) 455-6806"}
])

tab1, tab2 = st.tabs(["📝 Case Entry", "📊 Case List"])

with tab1:
    st.subheader("📋 New Case Registration")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No (e.g. IT30)")
        patient = st.text_input("Patient Name")
        sel_clinic = st.selectbox("Clinic", ["Select Clinic"] + sorted(ref_data['Clinic'].tolist()))
    with c2:
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    if st.button("💾 SAVE AND REGISTER"):
        if sel_clinic != "Select Clinic" and case_no:
            info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": info['Doctor'], "Address": info['Address'], "Phone": info['Phone'],
                "Material": material, "Arch": arch
            })
            st.success(f"Case {case_no} has been saved!")
        else:
            st.error("Please enter Case No and Clinic.")

with tab2:
    st.subheader("📊 Registered Cases")
    for i, row in enumerate(st.session_state.db):
        cols = st.columns([4, 1])
        with cols[0]: st.write(f"**{row['Case No']}** | {row['Patient']} | {row['Clinic']}")
        with cols[1]:
            if st.button("Invoice", key=f"btn_{i}"):
                st.session_state.selected_invoice = st.session_state.db[i]
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        # f-string을 사용하여 안전하게 HTML 생성
        inv_html = f"""
        <div class="invoice-container">
            <div class="invoice-paper">
                <div class="inv-header">
                    <div>
                        <p style="font-weight:bold; font-size:11px;">DENTAL TECHNOLOGY LTD</p>
                        <h1 class="logo-main">skycad</h1>
                        <p style="font-size:15px;">Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</p>
                    </div>
                    <div class="info-right">
                        <h1 style="font-size:40px;">INVOICE</h1>
                        <p>No. 162084</p>
                        <p>{date.today().strftime('%B %-d, %Y')}</p>
                        <div style="margin-top:35px; font-size:15px; line-height:1.5;">
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
                        <p style="font-size:12px; margin-top:10px;">Please ensure your monthly payment is made within 30 days of statement. Thank you.</p>
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(inv_html, unsafe_allow_html=True)
        if st.button("🖨️ PRINT INVOICE"):
            st.write('<script>window.print();</script>', unsafe_allow_html=True)
