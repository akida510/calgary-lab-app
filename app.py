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
    input:disabled { background-color: #262730 !important; color: #aaaaaa !important; }
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

    /* 인보이스 컨테이너: 박스 테두리 제거 & 모바일 대응 */
    .invoice-container {
        background-color: white !important; color: black !important; 
        padding: 40px 20px; font-family: 'Arial', sans-serif;
        max-width: 850px; margin: 0 auto;
    }
    .invoice-container * { color: black !important; border-color: black !important; }

    /* 모바일에서 로고와 인보이스 정보가 겹치지 않게 설정 */
    @media screen and (max-width: 600px) {
        .inv-header { flex-direction: column !important; }
        .inv-header-right { text-align: left !important; margin-top: 20px !important; }
        .ship-box { width: 100% !important; float: none !important; }
        .skycad-logo { font-size: 50px !important; }
    }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-container { display: block !important; border: none !important; padding: 0 !important; width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Addr": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9", "Phone": "(403) 970-0600"},
    {"Clinic": "Edmonton North", "Doctor": "Arshpreet Kaur", "Addr": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9", "Phone": "(780) 455-6806"},
])

def get_business_day(start_date, days_to_subtract):
    current_date = start_date
    while days_to_subtract > 0:
        current_date -= timedelta(days=1)
        if current_date.weekday() < 5: days_to_subtract -= 1
    return current_date

st.markdown(f'<div class="header-container"><div style="font-size: 24px; font-weight: 800;">🦷 Skycad Lab Manager</div><div style="font-size: 12px;">Designed By Heechul Jung</div></div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📝 Case Entry", "📊 Job List", "🔍 Search"])

with tab1:
    st.markdown("### 📋 Case Information")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="e.g. ET33")
        patient = st.text_input("Patient(환자명)")
        clinics = sorted(list(set(ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic(병원명)", ["Select"] + clinics)
        docs = ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "Select" else []
        sel_doctor = st.selectbox("Doctor(의사명)", ["Select"] + docs)
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        rec_date = today if is_3d else st.date_input("접수일", today)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

    st.markdown("### 📅 Schedule")
    due_date = st.date_input("Due Date", today + timedelta(days=7))
    if st.button("💾 SAVE CASE"):
        if sel_clinic == "Select" or not case_no: st.error("Check Case No/Clinic")
        else:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, "Doctor": sel_doctor,
                "Material": material, "Arch": arch, "Lab Done": today, "Due": due_date,
                "Addr": c_info['Addr'], "City": c_info['City'], "Phone": c_info['Phone']
            })
            st.success("Saved!")

with tab2:
    for i, row in enumerate(st.session_state.db):
        c_info, c_btn = st.columns([5, 2])
        with c_info: st.write(f"**{row['Case No']}** | {row['Patient']} ({row['Clinic']})")
        with c_btn:
            if st.button("Complete / Print", key=f"p_{i}"):
                st.session_state.selected_invoice = row
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        st.markdown(f"""
        <div class="invoice-container">
            <div class="inv-header" style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <div style="font-size: 10px; font-weight: bold; color: #1a4e8a !important;">DENTAL TECHNOLOGY Ltd</div>
                    <div class="skycad-logo" style="font-size: 65px; font-weight: 900; font-style: italic; color: #1a4e8a !important; line-height: 0.8; letter-spacing: -3px;">skycad</div>
                    <div style="margin-top: 15px; font-size: 13px;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</div>
                </div>
                <div class="inv-header-right" style="flex: 1; text-align: right;">
                    <div style="font-size: 32px; font-weight: bold; letter-spacing: 4px;">INVOICE</div>
                    <div style="font-size: 15px; font-weight: bold;">No. 162{inv['Case No'].replace('ET', '')}<br>{inv['Lab Done'].strftime('%m/%d/%Y')}</div>
                    <div class="ship-box" style="margin-top: 20px; text-align: left; font-size: 13px; border: 1px solid black; padding: 12px; width: 230px; display: inline-block;">
                        <b>Ship To:</b><br>{inv['Clinic']}<br>Dr. {inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}<br>{inv['Phone']}
                    </div>
                </div>
            </div>
            <div style="margin: 40px 0 10px 0; font-size: 18px; border-bottom: 2px solid black; padding-bottom: 5px;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1.5px solid black; font-weight: bold;">
                    <td style="padding: 10px 0; text-decoration: underline;">Description</td>
                    <td style="padding: 10px 0; text-align: right; text-decoration: underline;">Amount</td>
                </tr>
                <tr>
                    <td style="padding: 20px 0; height: 300px; vertical-align: top;">Nightguard ({inv['Material']}) {inv['Arch'].upper()}</td>
                    <td style="padding: 20px 0; text-align: right; vertical-align: top;">$180.00</td>
                </tr>
            </table>
            <div style="border-top: 2px solid black; padding-top: 10px; display: flex; justify-content: space-between; font-weight: bold; font-size: 18px;">
                <span>{inv['Case No']}</span><span>Total: $180.00</span>
            </div>
            <div style="margin-top: 60px; text-align: center; font-size: 10px; line-height: 1.4; color: #444 !important;">
                <div style="font-size: 14px; font-weight: bold; text-decoration: underline; margin-bottom: 10px; color: black !important;">All dental products we offer are custom made in Canada.</div>
                Please ensure your monthly payment is made within 30 days... (Balances over 30 days 1.5% charge). Thank you.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ PRINT INVOICE"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3: st.write("Search")
