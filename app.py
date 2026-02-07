import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [디자인 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    .stButton>button { 
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important; 
        color: white !important; font-weight: bold;
    }

    /* 인보이스 출력물용 (절대 안 깨지는 테이블 구조) */
    .inv-paper {
        background-color: white !important; color: black !important;
        padding: 50px; width: 850px; margin: 0 auto; font-family: 'Arial', sans-serif;
    }
    .inv-paper * { color: black !important; }
    
    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .inv-paper { width: 100% !important; margin: 0 !important; padding: 0 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Addr": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Addr": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9"},
])

st.markdown(f'<div class="header-container"><div style="font-size: 24px; font-weight: 800;">🦷 Skycad Lab Night Guard Manager</div><div style="font-size: 12px;">Heechul Jung Edition</div></div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📝 등록", "📊 리스트"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)")
        patient = st.text_input("Patient")
        sel_cln = st.selectbox("Clinic", ["선택"] + ref_data['Clinic'].tolist())
    with c2:
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)
        lab_date = st.date_input("완료일", date.today())

    if st.button("💾 케이스 저장"):
        if sel_cln != "선택" and case_no:
            info = ref_data[ref_data['Clinic'] == sel_cln].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_cln, "Doctor": info['Doctor'],
                "Material": material, "Arch": arch, "Lab Done": lab_date, "Status": "Pending",
                "Addr": info['Addr'], "City": info['City']
            })
            st.success("저장 완료!")

with tab2:
    for i, row in enumerate(st.session_state.db):
        cols = st.columns([4, 1])
        with cols[0]: st.write(f"{row['Case No']} | {row['Patient']}")
        with cols[1]:
            if st.button("출력", key=f"p_{i}"):
                st.session_state.selected_invoice = row
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        if st.button("닫기"): st.session_state.selected_invoice = None; st.rerun()
        
        st.markdown(f"""
        <div class="inv-paper">
            <table style="width:100%; border:none; table-layout:fixed;">
                <tr>
                    <td style="vertical-align:top;">
                        <div style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</div>
                        <div style="font-size:55px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-3px; line-height:1;">skycad</div>
                        <div style="margin-top:15px; font-size:13px;">
                            <b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600
                        </div>
                    </td>
                    <td style="vertical-align:top; text-align:right;">
                        <div style="font-size:45px; letter-spacing:5px; margin-bottom:5px;">INVOICE</div>
                        <div style="font-size:14px; margin-bottom:20px;">No. {inv['Case No'].replace('ET','')}<br>{inv['Lab Done'].strftime('%d/%m/%Y')}</div>
                        <div style="text-align:left; border:1px solid black; padding:15px; width:220px; float:right; font-size:13px; line-height:1.4;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}
                        </div>
                    </td>
                </tr>
            </table>

            <div style="margin-top:50px; margin-bottom:15px; font-size:18px;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>

            <table style="width:100%; border-collapse:collapse; border-top:2.5px solid black; border-bottom:2.5px solid black;">
                <thead>
                    <tr style="border-bottom:1.5px solid black;">
                        <th style="text-align:left; padding:12px 5px; font-size:16px;">Description</th>
                        <th style="text-align:right; padding:12px 5px; font-size:16px; width:120px;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding:30px 5px; height:400px; vertical-align:top; font-size:16px;">
                            Nightguard ({inv['Material']}) {inv['Arch']}
                        </td>
                        <td style="padding:30px 5px; text-align:right; vertical-align:top; font-size:16px;">$180.00</td>
                    </tr>
                </tbody>
            </table>

            <table style="width:100%; border:none; margin-bottom:60px;">
                <tr>
                    <td style="padding:15px 5px; font-weight:bold; font-size:19px;">{inv['Case No']}</td>
                    <td style="padding:15px 5px; text-align:right; font-weight:bold; font-size:19px;">Total: $180.00</td>
                </tr>
            </table>

            <div style="text-align:center;">
                <div style="font-size:18px; font-weight:bold; text-decoration:underline; margin-bottom:20px;">All dental products we offer are custom made in Canada.</div>
                <div style="font-size:12.5px; line-height:1.7; padding:0 40px;">
                    Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.
                </div>
            </div>

            <div style="margin-top:80px; border-top:1px solid black; width:220px; padding-top:8px; font-size:13px;">Authorized Signature</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🖨️ 인쇄하기"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
