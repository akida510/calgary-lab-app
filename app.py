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
    /* 버튼: 아주 얇고 세련된 디자인 (폰트 10px) */
    .stButton>button { 
        height: 1.8rem !important;
        font-size: 10px !important;
        padding: 0 10px !important;
        background-color: #2b3a67 !important;
        color: #dbe4ff !important;
        border: 1px solid #4c6ef5 !important;
        border-radius: 4px !important;
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
                "Lab Done": lab_done_date, "Status": "Pending", 
                "Addr": c_info['Addr'], "City": c_info['City']
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
        
        # [수정] 사진에 있는 긴 문구 전체 복원 및 레이아웃 수정
        invoice_html = f"""
        <div style="background:white; color:black; padding:40px; font-family:Arial, sans-serif; height:1050px; position:relative; box-sizing:border-box;">
            <table style="width:100%; border:none;">
                <tr>
                    <td style="width:60%;">
                        <span style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                        <span style="font-size:65px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-4px; line-height:0.8;">skycad</span><br>
                        <div style="margin-top:20px; font-size:13px; line-height:1.2;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</div>
                    </td>
                    <td style="text-align:right; vertical-align:top;">
                        <h1 style="font-size:55px; margin:0; font-weight:400; letter-spacing:8px;">INVOICE</h1>
                        <p style="font-size:16px; margin:5px 0;">No. {inv['Case No'].replace('ET','')}<br>{inv['Lab Done'].strftime('%d/%m/%Y')}</p>
                        <div style="text-align:left; border:1.5px solid black; padding:15px; width:220px; float:right; margin-top:15px; font-size:13px;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}
                        </div>
                    </td>
                </tr>
            </table>

            <div style="margin: 50px 0 20px 0; font-size:22px;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>

            <table style="width:100%; border-top:2.5px solid black; border-bottom:2.5px solid black; border-collapse:collapse;">
                <tr style="border-bottom:1.2px solid black; font-weight:bold; font-size:18px;">
                    <td style="padding:12px 5px;">Description</td>
                    <td style="padding:12px 5px; text-align:right;">Amount</td>
                </tr>
                <tr>
                    <td style="padding:30px 5px; height:450px; vertical-align:top; font-size:18px;">
                        Nightguard ({inv['Material']}) - {inv['Arch']}
                    </td>
                    <td style="padding:30px 5px; text-align:right; vertical-align:top; font-size:18px;">$180.00</td>
                </tr>
            </table>

            <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:20px; margin:25px 0 60px 0;">
                <span>{inv['Case No']}</span><span>Total: $180.00</span>
            </div>

            <div style="text-align:center;">
                <div style="font-size:19px; font-weight:bold; text-decoration:underline; margin-bottom:20px;">All dental products we offer are custom made in Canada.</div>
                <p style="font-size:12px; line-height:1.8; padding:0 40px; color:#333;">Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.</p>
            </div>
            
            <div style="margin-top:80px; border-top:1.5px solid black; width:240px; padding-top:10px; font-size:14px; text-align:left;">Authorized Signature</div>
        </div>
        """
        components.html(invoice_html, height=1100, scrolling=False)
        if st.button("🖨️ 인쇄 (Print)"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3: st.write("Search...")
