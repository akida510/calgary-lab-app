import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import time

# [1. 디자인 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #30363d !important;
    }

    /* 인보이스 출력물 정밀 디자인 */
    .inv-outer-container { display: flex; justify-content: center; padding: 20px 0; background-color: #0d1117; }
    .invoice-letter { 
        background-color: white !important; color: black !important; 
        width: 8.5in; min-height: 11in; padding: 0.7in; 
        border: 1px solid #d0d7de; box-sizing: border-box; 
        font-family: 'Arial', sans-serif; position: relative;
    }
    .invoice-letter * { color: black !important; }
    
    /* 헤더 영역 */
    .inv-header { display: flex; justify-content: space-between; margin-bottom: 50px; }
    .inv-logo-area { font-size: 13px; line-height: 1.4; }
    .inv-info-area { text-align: left; width: 250px; }
    
    /* 테이블 영역 */
    .inv-table { width: 100%; border-collapse: collapse; margin-top: 30px; border-top: 1.5px solid black; border-bottom: 1.5px solid black; }
    .inv-table th { padding: 10px 5px; text-align: left; font-size: 15px; border-bottom: 1px solid black; }
    .inv-table td { padding: 15px 5px; vertical-align: top; font-size: 15px; height: 380px; }
    
    /* 하단 토탈 라인 */
    .inv-total-line { 
        display: flex; justify-content: space-between; 
        padding: 10px 5px; border-top: 1.5px solid black; 
        font-weight: bold; font-size: 16px; margin-top: 10px;
    }

    /* 하단 문구 (사진 텍스트 1:1 복사) */
    .inv-notice-section { margin-top: 50px; text-align: center; }
    .custom-made-text { 
        font-size: 18px; font-weight: bold; text-decoration: underline; margin-bottom: 20px; display: block;
    }
    .finance-text { 
        font-size: 12.5px; line-height: 1.6; text-align: center; color: #222 !important; padding: 0 30px;
    }

    @media print {
        .stButton, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .inv-outer-container { padding: 0; background: white; }
        .invoice-letter { border: none; width: 100%; padding: 0; margin: 0; }
    }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 및 세션 관리]
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084

# 마스터 데이터
ref_data = pd.DataFrame([
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Arshpreet Kaur", "Address": "13510 127 St NW", "City": "Edmonton, Alberta T5L 1B9", "Phone": "(780) 455-6806"},
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Address": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9", "Phone": "(403) 970-0600"},
])

# [3. UI 구성]
st.title("🦷 Skycad Lab Manager")
tab1, tab2 = st.tabs(["📝 케이스 등록", "📊 인보이스 리스트"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case Number (예: ET12)")
        patient = st.text_input("Patient Name")
        clinic_choice = st.selectbox("Clinic", ref_data['Clinic'].tolist())
    with c2:
        mat = st.selectbox("Material", ["Thermo", "Dual", "Soft"])
        arch = st.selectbox("Arch", ["UPPER", "LOWER", "BOTH"])
        # 희철님 요청대로 180불 고정
        fixed_price = 180.00
        st.write(f"**Unit Price: ${fixed_price}** (Fixed)")

    if st.button("💾 케이스 저장하기"):
        if not case_no or not patient:
            st.error("Case No와 Patient 이름을 입력해주세요.")
        else:
            info = ref_data[ref_data['Clinic'] == clinic_choice].iloc[0]
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter, "Case": case_no, "Patient": patient,
                "Clinic": info['Clinic'], "Doctor": info['Doctor'], "Addr": info['Address'], "City": info['City'], "Phone": info['Phone'],
                "Desc": f"Nightguard ({mat}) {arch}", "Amount": fixed_price, "Date": date.today().strftime('%-d/%-m/%Y')
            })
            st.session_state.inv_counter += 1
            st.success("✅ 저장 완료!")
            time.sleep(0.5); st.rerun()

with tab2:
    for i, row in enumerate(st.session_state.db):
        if st.button(f"📄 {row['Case']} - {row['Patient']}", key=f"inv_{i}"):
            st.session_state.selected_invoice = row
            st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        col_close, col_print = st.columns([1, 6])
        with col_close:
            if st.button("닫기"): st.session_state.selected_invoice = None; st.rerun()
        with col_print:
            if st.button("🖨️ 인쇄하기"): st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="inv-outer-container">
            <div class="invoice-letter">
                <div class="inv-header">
                    <div class="inv-logo-area">
                        <span style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                        <span style="font-size:45px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-2px; line-height:1;">skycad</span><br>
                        <div style="margin-top:10px;">
                            <b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600
                        </div>
                    </div>
                    <div class="inv-info-area">
                        <h2 style="font-size:32px; margin:0; font-weight:400;">INVOICE</h2>
                        <p style="margin:5px 0;">No. {inv['Inv_No']}<br>{inv['Date']}</p>
                        <div style="margin-top:20px; font-size:14px; line-height:1.4;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}<br>{inv['Phone']}
                        </div>
                    </div>
                </div>
                
                <div style="margin-bottom:20px; font-size:16px;"><b>Patient:</b> {inv['Patient'].upper()}</div>
                
                <table class="inv-table">
                    <thead><tr><th>Description</th><th style="text-align:right;">Amount</th></tr></thead>
                    <tbody>
                        <tr>
                            <td>{inv['Desc']}</td>
                            <td style="text-align:right;">${inv['Amount']:,.2f}</td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="inv-total-line">
                    <span>{inv['Case']}</span>
                    <span>Total: ${inv['Amount']:,.2f}</span>
                </div>
                
                <div class="inv-notice-section">
                    <span class="custom-made-text">All dental products we offer are custom made in Canada.</span>
                    <p class="finance-text">
                        Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.
                    </p>
                </div>
                
                <div style="margin-top:80px;">
                    <div style="border-top:1px solid black; width:220px; padding-top:5px; font-size:13px;">Authorized Signature</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
