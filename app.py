import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import streamlit.components.v1 as components

# [페이지 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    label p, .stMarkdown p, .stTabs [data-baseweb="tab"] p { 
        color: #ffffff !important; font-weight: 600 !important; 
    }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    /* 버튼: 얇고 세련된 디자인으로 전면 수정 */
    .stButton>button { 
        height: 1.8rem !important;
        font-size: 10px !important;
        padding: 0 10px !important;
        background-color: #2b3a67 !important;
        color: #dbe4ff !important;
        border: 1px solid #4c6ef5 !important;
        border-radius: 4px !important;
        display: flex; align-items: center; justify-content: center;
    }
    .stButton>button:hover { background-color: #4c6ef5 !important; color: white !important; }
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
        patient = st.text_input("Patient(환자명)")
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
    with col5: due_date = st.date_input("Due Date", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("Lab Done", today + timedelta(days=1))
    with col4:
        ship_date = get_business_day(due_date, 1 if (sel_clinic != "선택" and ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0]=="Local") else 2)
        st.date_input("Shipping Date", ship_date)

    if st.button("💾 케이스 저장"):
        if sel_clinic != "선택" and case_no:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Material": material, "Arch": arch,
                "Lab Done": lab_done_date, "Status": "Pending", "Addr": c_info['Addr'], "City": c_info['City']
            })
            st.success("등록 완료!")

with tab2:
    for i, row in enumerate(st.session_state.db):
        c_info, c_btn1, c_btn2 = st.columns([4, 1, 1])
        with c_info: st.write(f"**{row['Case No']}** | {row['Patient']} | {row['Clinic']}")
        with c_btn1:
            if st.button("완료/출력", key=f"inv_{i}"):
                st.session_state.db[i]['Status'] = "Completed"
                st.session_state.selected_invoice = st.session_state.db[i]
                st.rerun()
        with c_btn2:
            if row['Status'] == "Completed":
                if st.button("취소", key=f"un_{i}"):
                    st.session_state.db[i]['Status'] = "Pending"
                    st.session_state.selected_invoice = None
                    st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        
        # [핵심] 인보이스를 HTML 컴포넌트로 분리하여 렌더링
        invoice_html = f"""
        <div style="background:white; color:black; padding:40px; font-family:Arial; height:900px; position:relative;">
            <table style="width:100%; border:none;">
                <tr>
                    <td>
                        <span style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                        <span style="font-size:55px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-3px;">skycad</span><br>
                        <div style="font-size:12px;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9</div>
                    </td>
                    <td style="text-align:right; vertical-align:top;">
                        <h1 style="font-size:45px; margin:0; letter-spacing:5px;">INVOICE</h1>
                        <p style="font-size:14px;">No. {inv['Case No'].replace('ET','')}<br>{inv['Lab Done'].strftime('%d/%m/%Y')}</p>
                        <div style="border:1px solid #000; padding:10px; width:200px; text-align:left; float:right; font-size:12px;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Addr']}
                        </div>
                    </td>
                </tr>
            </table>
            <div style="margin:40px 0 20px 0; font-size:18px;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>
            <table style="width:100%; border-top:2px solid black; border-bottom:2px solid black; border-collapse:collapse;">
                <tr style="border-bottom:1px solid black; font-weight:bold;">
                    <td style="padding:10px;">Description</td>
                    <td style="padding:10px; text-align:right;">Amount</td>
                </tr>
                <tr>
                    <td style="padding:20px 10px; height:400px; vertical-align:top;">Nightguard ({inv['Material']}) - {inv['Arch']}</td>
                    <td style="padding:20px 10px; text-align:right; vertical-align:top;">$180.00</td>
                </tr>
            </table>
            <div style="display:flex; justify-content:space-between; font-weight:bold; margin:20px 0;">
                <span>{inv['Case No']}</span><span>Total: $180.00</span>
            </div>
            <div style="position:absolute; bottom:50px; width:100%; text-align:center; left:0;">
                <p style="font-size:16px; font-weight:bold; text-decoration:underline;">All dental products we offer are custom made in Canada.</p>
                <p style="font-size:10px; padding:0 100px;">Please ensure your monthly payment is made within 30 days... (Thank you)</p>
                <div style="margin-top:40px; border-top:1px solid black; width:200px; margin-left:40px; text-align:left;">Authorized Signature</div>
            </div>
        </div>
        """
        components.html(invoice_html, height=1000, scrolling=False)
        if st.button("🖨️ 인쇄하기"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3: st.write("검색 준비 중")
