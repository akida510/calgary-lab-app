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
    .invoice-container {
        background-color: white !important; color: black !important; 
        padding: 50px; border-radius: 0px; font-family: 'Arial', sans-serif;
        width: 100%; max-width: 850px; margin: 0 auto; box-sizing: border-box;
    }
    .invoice-container * { color: black !important; line-height: 1.2; }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-container { display: block !important; border: none !important; padding: 0 !important; margin: 0 !important; width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Addr": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier", "Addr": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9"},
])

def get_business_day(start_date, days_to_subtract):
    current_date = start_date
    while days_to_subtract > 0:
        current_date -= timedelta(days=1)
        if current_date.weekday() < 5: days_to_subtract -= 1
    return current_date

st.markdown(f'<div class="header-container"><div style="font-size: 24px; font-weight: 800;">🦷 Skycad Lab Night Guard Manager</div><div style="font-size: 12px;">Heechul Jung Edition</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료", "🔍 검색"])

with tab1:
    st.markdown("### 📋 기본정보입력")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: ET33")
        patient = st.text_input("Patient(환자명)", placeholder="환자 성함")
        clinics = sorted(list(set(ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic(병원명)", ["선택"] + clinics)
        filtered_docs = ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "선택" else []
        sel_doctor = st.selectbox("Doctor(의사명)", ["선택"] + filtered_docs)
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        rec_date = today if is_3d else st.date_input("접수일", today)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("요청일 (Due Date)", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("완료일 (Lab Done)", today + timedelta(days=1))
    with col4:
        reg = ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0] if sel_clinic != "선택" else "Local"
        ship_date = get_business_day(due_date, 1 if reg=="Local" else 2)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("💾 케이스 저장 (접수 완료)"):
        if sel_clinic == "선택" or not case_no:
            st.error("입력 정보를 확인하세요.")
        else:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, "Doctor": sel_doctor,
                "Material": material, "Arch": arch, "Lab Done": lab_done_date, "Status": "Pending",
                "Addr": c_info['Addr'], "City": c_info['City']
            })
            st.success(f"✅ {case_no}번 저장 완료!")

with tab2:
    for i, row in enumerate(st.session_state.db):
        c_info, c_btn = st.columns([4, 1])
        with c_info: st.markdown(f"**{'🟡' if row['Status']=='Pending' else '🟢'} {row['Case No']}** | {row['Patient']}")
        with c_btn:
            if st.button("인보이스 보기", key=f"inv_{i}"):
                st.session_state.db[i]['Status'] = "Completed"
                st.session_state.selected_invoice = st.session_state.db[i]
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        st.markdown(f"""
        <div class="invoice-container">
            <table style="width:100%; border:none; margin-bottom:40px;">
                <tr>
                    <td style="vertical-align:top; width:50%;">
                        <span style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                        <span style="font-size:52px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-2px; line-height:1;">skycad</span><br>
                        <div style="margin-top:20px; font-size:12px;">
                            <b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600
                        </div>
                    </td>
                    <td style="vertical-align:top; text-align:right; width:50%;">
                        <h1 style="font-size:40px; margin:0; font-weight:400; letter-spacing:4px;">INVOICE</h1>
                        <p style="font-size:14px; margin:10px 0;">No. {inv['Case No'].replace('ET','')}<br>{inv['Lab Done'].strftime('%d/%m/%Y')}</p>
                        <div style="text-align:left; margin-top:20px; font-size:13px; border:1px solid #000; padding:15px; width:220px; display:inline-block; line-height:1.4;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}
                        </div>
                    </td>
                </tr>
            </table>

            <div style="margin-bottom:15px; font-size:16px;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>

            <table style="width:100%; border-collapse:collapse; border-top:2.5px solid black; border-bottom:2.5px solid black; table-layout:fixed;">
                <thead>
                    <tr style="border-bottom: 1.5px solid black;">
                        <th style="padding:12px 5px; text-align:left; font-size:15px; width:80%;">Description</th>
                        <th style="padding:12px 5px; text-align:right; font-size:15px; width:20%;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding:25px 5px; vertical-align:top; height:380px; font-size:15px;">
                            Nightguard ({inv['Material']}) {inv['Arch']}
                        </td>
                        <td style="padding:25px 5px; vertical-align:top; text-align:right; font-size:15px;">$180.00</td>
                    </tr>
                </tbody>
            </table>

            <table style="width:100%; border-collapse:collapse; margin-bottom:50px;">
                <tr>
                    <td style="padding:10px 5px; font-weight:bold; font-size:17px;">{inv['Case No']}</td>
                    <td style="padding:10px 5px; font-weight:bold; font-size:17px; text-align:right;">Total: $180.00</td>
                </tr>
            </table>

            <div style="text-align:center; margin-top:40px;">
                <span style="font-size:18px; font-weight:bold; text-decoration:underline; display:block; margin-bottom:20px;">
                    All dental products we offer are custom made in Canada.
                </span>
                <p style="font-size:12px; line-height:1.7; padding:0 30px; margin:0;">
                    Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.
                </p>
            </div>

            <div style="margin-top:80px;">
                <div style="border-top:1px solid black; width:220px; padding-top:8px; font-size:13px;">Authorized Signature</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🖨️ 인쇄하기"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3: st.write("검색 준비 중")
