import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [수정 금지] 디자인 설정 및 테마 강제 고정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    label p, .stMarkdown p, .stMetric p, .stTabs [data-baseweb="tab"] p { 
        color: #ffffff !important; font-weight: 600 !important; 
    }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    .stButton>button { 
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important; 
        color: white !important; font-weight: bold; border-radius: 5px; 
    }

    /* 인보이스 출력물 - 깨짐 방지 핵심 스타일 */
    .invoice-print-area {
        background-color: white !important;
        color: black !important;
        padding: 40px;
        width: 800px; /* 가로폭 고정 */
        margin: 0 auto;
        font-family: 'Arial', sans-serif;
    }
    .invoice-print-area * { color: black !important; line-height: 1.2; }
    
    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-print-area { width: 100% !important; margin: 0 !important; padding: 0 !important; border: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

# 병원 데이터
ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Addr": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Addr": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9"},
])

st.markdown(f'<div class="header-container"><div style="font-size: 24px; font-weight: 800;">🦷 Skycad Lab Night Guard Manager</div><div style="font-size: 12px;">Heechul Jung Edition</div></div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: ET33")
        patient = st.text_input("Patient(환자명)")
        cln_list = sorted(ref_data['Clinic'].tolist())
        sel_cln = st.selectbox("Clinic", ["선택"] + cln_list)
    with c2:
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)
        lab_date = st.date_input("완료일", date.today())

    if st.button("💾 케이스 저장"):
        if sel_cln == "선택" or not case_no:
            st.error("정보를 입력하세요.")
        else:
            info = ref_data[ref_data['Clinic'] == sel_cln].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_cln, "Doctor": info['Doctor'],
                "Material": material, "Arch": arch, "Lab Done": lab_date, "Status": "Pending",
                "Addr": info['Addr'], "City": info['City']
            })
            st.success("✅ 저장 완료!")

with tab2:
    for i, row in enumerate(st.session_state.db):
        cols = st.columns([4, 1])
        with cols[0]: st.write(f"{row['Case No']} | {row['Patient']}")
        with cols[1]:
            if st.button("인보이스", key=f"v_{i}"):
                st.session_state.selected_invoice = row
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        if st.button("닫기"): st.session_state.selected_invoice = None; st.rerun()
        
        # ---------------------------------------------------------
        # 깨짐 방지용 올-테이블 레이아웃
        # ---------------------------------------------------------
        st.markdown(f"""
        <div class="invoice-print-area">
            <table style="width:100%; border:none; table-layout:fixed;">
                <tr>
                    <td style="vertical-align:top; width:60%;">
                        <div style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</div>
                        <div style="font-size:55px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-3px;">skycad</div>
                        <div style="margin-top:15px; font-size:13px; line-height:1.4;">
                            <b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600
                        </div>
                    </td>
                    <td style="vertical-align:top; text-align:right; width:40%;">
                        <div style="font-size:45px; letter-spacing:5px; margin-bottom:10px;">INVOICE</div>
                        <div style="font-size:14px; margin-bottom:20px;">No. {inv['Case No'].replace('ET','')}<br>{inv['Lab Done'].strftime('%d/%m/%Y')}</div>
                        <div style="text-align:left; border:1px solid black; padding:15px; width:220px; float:right; font-size:13px; line-height:1.4;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}
                        </div>
                    </td>
                </tr>
            </table>

            <div style="margin-top:30px; margin-bottom:10px; font-size:17px;">
                <b>Patient:</b> {str(inv['Patient']).upper()}
            </div>

            <table style="width:100%; border-collapse:collapse; border-top:2px solid black; border-bottom:2px solid black; table-layout:fixed;">
                <thead>
                    <tr style="border-bottom:1px solid black;">
                        <th style="text-align:left; padding:10px; font-size:16px;">Description</th>
                        <th style="text-align:right; padding:10px; font-size:16px; width:100px;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding:20px 10px; height:400px; vertical-align:top; font-size:16px;">
                            Nightguard ({inv['Material']}) {inv['Arch']}
                        </td>
                        <td style="padding:20px 10px; text-align:right; vertical-align:top; font-size:16px;">
                            $180.00
                        </td>
                    </tr>
                </tbody>
            </table>

            <table style="width:100%; border:none; margin-bottom:50px;">
                <tr>
                    <td style="padding:10px; font-weight:bold; font-size:18px;">{inv['Case No']}</td>
                    <td style="padding:10px; text-align:right; font-weight:bold; font-size:18px;">Total: $180.00</td>
                </tr>
            </table>

            <div style="text-align:center; margin-top:30px;">
                <div style="font-size:18px; font-weight:bold; text-decoration:underline; margin-bottom:15px;">
                    All dental products we offer are custom made in Canada.
                </div>
                <div style="font-size:12px; line-height:1.6; padding:0 20px;">
                    Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.
                </div>
            </div>

            <div style="margin-top:70px;">
                <div style="border-top:1px solid black; width:220px; padding-top:5px; font-size:13px;">Authorized Signature</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🖨️ 인쇄하기"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
