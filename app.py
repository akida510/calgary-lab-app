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

    /* Letter 용지 비율 (8.5 x 11 inch) */
    .invoice-container {
        width: 100%;
        display: flex;
        justify-content: center;
        padding: 20px 0;
        overflow-x: auto;
    }

    .invoice-paper {
        background-color: #ffffff !important; 
        width: 816px; height: 1056px; min-width: 816px;
        padding: 60px 70px; border: 1px solid #ddd; 
        font-family: 'Arial', sans-serif;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        position: relative; box-sizing: border-box;
    }

    /* 인보이스 내 텍스트 강제 검정 */
    .invoice-paper * { color: #000000 !important; }

    /* 모바일 자동 축소 (한 화면에 다 들어오게) */
    @media (max-width: 850px) {
        .invoice-container { justify-content: flex-start; }
        .invoice-paper {
            transform: scale(0.4); transform-origin: top left;
            margin-bottom: -630px; 
        }
    }
    
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

    @media print {
        @page { size: letter; margin: 0; }
        .stButton, [data-testid="stSidebar"], .stTabs, .stDivider { display: none !important; }
        .invoice-paper { transform: scale(1) !important; border: none !important; margin: 0 !important; box-shadow: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# [데이터 로직]
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Address": "205-7136 11 St NE, Calgary, AB", "Phone": "(403) 970-0600"},
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Amhipreat Kaur", "Address": "13510 177 St NW, Edmonton, AB", "Phone": "(780) 455-6806"}
])

tab1, tab2 = st.tabs(["📝 등록", "📊 리스트"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No")
        patient = st.text_input("Patient")
        sel_clinic = st.selectbox("Clinic", ["선택"] + sorted(ref_data['Clinic'].tolist()))
    with c2:
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    if st.button("💾 저장"):
        if sel_clinic != "선택" and case_no:
            info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": info['Doctor'], "Address": info['Address'], "Phone": info['Phone'],
                "Material": material, "Arch": arch
            })
            st.success("저장되었습니다.")

with tab2:
    for i, row in enumerate(st.session_state.db):
        cols = st.columns([4, 1])
        with cols[0]: st.write(f"**{row['Case No']}** | {row['Patient']} | {row['Clinic']}")
        with cols[1]:
            if st.button("인보이스", key=f"btn_{i}"):
                st.session_state.selected_invoice = st.session_state.db[i]
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        html_code = f"""
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
                        <div style="margin-top:35px; font-size:15px;">
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
        st.markdown(html_code, unsafe_allow_html=True)
        if st.button("🖨️ 인쇄하기"):
            st.write('<script>window.print();</script>', unsafe_allow_html=True)
