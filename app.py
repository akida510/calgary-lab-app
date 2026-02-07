import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 디자인 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #30363d !important;
    }
    input:disabled { background-color: #21262d !important; color: #8b949e !important; }

    .header-box {
        display: flex; justify-content: space-between; align-items: flex-end;
        padding-bottom: 15px; border-bottom: 2px solid #30363d; margin-bottom: 25px;
    }
    .main-title { font-size: 38px !important; font-weight: 800 !important; color: #ffffff !important; }
    .creator-info { font-size: 14px !important; color: #8b949e !important; font-style: italic; }
    .section-header { font-size: 24px !important; font-weight: 700 !important; color: #4c6ef5 !important; margin-top: 35px !important; }

    /* 인보이스 정밀 재현 */
    .inv-outer-container { display: flex; justify-content: center; padding: 20px 0; background-color: #0d1117; }
    .invoice-letter { 
        background-color: white !important; color: black !important; 
        width: 8.5in; min-height: 11in; padding: 0.7in; 
        border: 1px solid #d0d7de; box-sizing: border-box; 
        font-family: 'Arial', sans-serif; position: relative;
    }
    .invoice-letter * { color: black !important; }
    
    .inv-table { width: 100%; border-collapse: collapse; margin-top: 30px; }
    .inv-table th { border-top: 2px solid black; border-bottom: 2px solid black; padding: 12px 5px; text-align: left; font-size: 14px; }
    .inv-table td { padding: 20px 5px; vertical-align: top; font-size: 14px; }
    
    /* 하단 금액란 */
    .inv-footer-wrapper { margin-top: 30px; display: flex; justify-content: flex-end; }
    .inv-totals-table { width: 280px; border-collapse: collapse; }
    .inv-totals-table td { padding: 6px 5px; font-size: 15px; }
    .inv-totals-table .label { text-align: left; font-weight: bold; }
    .inv-totals-table .value { text-align: right; }
    .amount-due-row { border-top: 2px solid black; font-size: 18px !important; font-weight: 900 !important; }

    /* 사진 속 하단 긴 문구 (중요) */
    .inv-notice-box {
        margin-top: 60px; font-size: 11px; line-height: 1.5; color: #333 !important;
    }
    .payment-info {
        margin-top: 20px; font-size: 12px; font-weight: bold;
    }

    @media print {
        .stButton, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider, .header-box, .stat-card { display: none !important; }
        .inv-outer-container { padding: 0; background: white; }
        .invoice-letter { border: none; width: 100%; padding: 0; margin: 0; }
    }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 및 세션 로직 (이전과 동일)]
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084
ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Address": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier", "Address": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9"},
])
if 'cur_cln' not in st.session_state: st.session_state.cur_cln = "선택"
if 'cur_doc' not in st.session_state: st.session_state.cur_doc = "선택"

def sync_cln():
    if st.session_state.cln_select != "선택":
        st.session_state.cur_cln = st.session_state.cln_select
        st.session_state.cur_doc = ref_data[ref_data['Clinic'] == st.session_state.cln_select]['Doctor'].iloc[0]
    else: st.session_state.cur_cln = st.session_state.cur_doc = "선택"

def sync_doc():
    if st.session_state.doc_select != "선택":
        st.session_state.cur_doc = st.session_state.doc_select
        st.session_state.cur_cln = ref_data[ref_data['Doctor'] == st.session_state.doc_select]['Clinic'].iloc[0]
    else: st.session_state.cur_cln = st.session_state.cur_doc = "선택"

def get_business_day(start_date, days):
    curr = start_date
    while days > 0:
        curr -= timedelta(days=1)
        if curr.weekday() < 5: days -= 1
    return curr

# [3. 메인 화면]
st.markdown('<div class="header-box"><div class="main-title">🦷 Skycad Lab Manager</div><div class="creator-info">Created by Heechul Jung</div></div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료", "🔍 검색"])

with tab1:
    st.markdown('<span class="section-header">📋 기본정보입력</span>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No")
        patient = st.text_input("Patient")
        clns = ["선택"] + sorted(ref_data['Clinic'].tolist())
        st.selectbox("Clinic", clns, key="cln_select", index=clns.index(st.session_state.cur_cln), on_change=sync_cln)
        docs = ["선택"] + sorted(ref_data['Doctor'].tolist())
        st.selectbox("Doctor", docs, key="doc_select", index=docs.index(st.session_state.cur_doc), on_change=sync_doc)
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        rec_date = st.date_input("접수일", value=today, disabled=is_3d)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

    st.markdown('<span class="section-header">📅 일정 관리</span>', unsafe_allow_html=True)
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("Due Date", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("Lab Done", today + timedelta(days=1))
    with col4:
        reg = ref_data[ref_data['Clinic']==st.session_state.cur_cln]['Region'].iloc[0] if st.session_state.cur_cln != "선택" else "Local"
        ship_date = get_business_day(due_date, 1 if reg=="Local" else 2)
        st.date_input("Shipping Date", ship_date)

    if st.button("💾 케이스 저장하기"):
        if st.session_state.cur_cln == "선택" or not case_no: st.error("정보를 입력하세요")
        else:
            c_info = ref_data[ref_data['Clinic'] == st.session_state.cur_cln].iloc[0]
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter, "Case No": case_no, "Patient": patient, 
                "Clinic": st.session_state.cur_cln, "Doctor": st.session_state.cur_doc, 
                "Material": material, "Arch": arch, "Status": "Pending",
                "Address": c_info['Address'], "City": c_info['City'],
                "Inv_Date": today.strftime('%m/%d/%Y'), "Due": due_date, "Month": today.strftime('%Y-%m')
            })
            st.session_state.inv_counter += 1
            st.rerun()

with tab2:
    for i, row in enumerate(st.session_state.db):
        c_info, c_btn = st.columns([6, 1])
        with c_info: st.markdown(f"**{'🟢' if row['Status']=='Completed' else '🟡'} {row['Case No']}** | {row['Patient']} | {row['Clinic']}")
        with c_btn:
            if st.button("완료" if row['Status']=="Pending" else "재출력", key=f"b_{i}"):
                st.session_state.db[i]['Status'] = "Completed"; st.session_state.selected_invoice = st.session_state.db[i]; st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        if st.button("닫기"): st.session_state.selected_invoice = None; st.rerun()
        if st.button("🖨️ 인쇄하기"): st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="inv-outer-container">
            <div class="invoice-letter">
                <div style="display: flex; justify-content: space-between; margin-bottom: 50px;">
                    <div>
                        <span style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                        <span style="font-size:50px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-3px; line-height:1;">skycad</span>
                        <div style="font-size:12px; margin-top:25px;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9</div>
                    </div>
                    <div style="text-align: right;">
                        <h1 style="font-size:42px; font-weight:400; margin:0; letter-spacing:5px;">INVOICE</h1>
                        <p style="font-size:14px; margin-top:12px;"><b>Date:</b> {inv['Inv_Date']}<br><b>Invoice No:</b> {inv['Inv_No']}</p>
                        <div style="text-align:left; font-size:13px; margin-top:40px; border:1px solid #ddd; padding:15px; width:240px; float:right;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Address']}<br>{inv['City']}
                        </div>
                    </div>
                </div>
                <div style="clear:both; margin-bottom:25px; font-size:16px;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>
                <table class="inv-table">
                    <thead><tr><th>Description</th><th style="text-align:right;">Amount</th></tr></thead>
                    <tbody>
                        <tr>
                            <td style="height:350px;">Nightguard ({inv['Material']}) {inv['Arch']}<br>
                                <span style="font-size:13px; color:#555; display:block; margin-top:8px;">Case No: {inv['Case No']}</span></td>
                            <td style="text-align:right;">180.00</td>
                        </tr>
                    </tbody>
                </table>
                <div class="inv-footer-wrapper">
                    <table class="inv-totals-table">
                        <tr><td class="label">Subtotal</td><td class="value">180.00</td></tr>
                        <tr><td class="label">Total</td><td class="value">180.00</td></tr>
                        <tr><td class="label">Amount Paid</td><td class="value">0.00</td></tr>
                        <tr class="amount-due-row"><td class="label">Amount Due</td><td class="value">$180.00</td></tr>
                    </table>
                </div>
                <div class="inv-notice-box">
                    All accounts are due and payable within 30 days of the invoice date. 
                    Interest at the rate of 2% per month (24% per annum) will be charged on all overdue accounts.
                    <div class="payment-info">
                        Please make all E-transfers to: skycadlab@gmail.com
                    </div>
                </div>
                <div style="margin-top:50px;">
                    <div style="border-top:1px solid black; width:220px; padding-top:5px; font-size:13px;">Authorized Signature</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
