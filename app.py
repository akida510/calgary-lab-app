import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [디자인 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    label p, .stMarkdown p, p, span { color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    .invoice-paper {
        background-color: white !important; padding: 50px; border: 1px solid #000;
        width: 100%; max-width: 800px; margin: 20px auto;
    }
    .invoice-paper * { color: #000000 !important; } /* 인보이스 글자색 검정 고정 */
    
    /* 버튼 스타일 조정 */
    .stButton>button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Address": "205-7136 11 St NE, Calgary, AB", "Phone": "(403) 970-0600", "Region": "Local"},
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Amhipreat Kaur", "Address": "13510 177 St NW, Edmonton, AB", "Phone": "(780) 455-6806", "Region": "Courier"}
])

def get_business_day(start_date, days_to_subtract):
    curr = start_date
    while days_to_subtract > 0:
        curr -= timedelta(days=1)
        if curr.weekday() < 5: days_to_subtract -= 1
    return curr

tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트/완료", "🔍 검색"])

with tab1:
    st.markdown("### 📋 케이스 등록")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)")
        patient = st.text_input("Patient(환자명)")
        clinics = sorted(list(set(ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic(병원명)", ["선택"] + clinics)
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("요청일 (Due Date)", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("완료일 (Lab Done)", today + timedelta(days=1))
    with col4:
        reg = ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0] if sel_clinic != "선택" else "Courier"
        ship_date = get_business_day(due_date, 1 if reg == "Local" else 2)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("💾 저장 및 등록"):
        if sel_clinic == "선택" or not case_no:
            st.error("필수 정보를 입력하세요.")
        else:
            clinic_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": clinic_info['Doctor'], "Address": clinic_info['Address'], "Phone": clinic_info['Phone'],
                "Material": material, "Arch": arch, "Lab Done": lab_done_date, "Status": "진행중"
            })
            st.success("등록되었습니다.")

with tab2:
    st.markdown("### 📊 진행 상황 리스트")
    for i, row in enumerate(st.session_state.db):
        c_status, c_info, c_action = st.columns([1, 3, 2])
        
        with c_status:
            status_emoji = "🟡" if row['Status'] == "진행중" else "🟢"
            st.markdown(f"**{status_emoji} {row['Status']}**")
        
        with c_info:
            st.write(f"**{row['Case No']}** | {row['Patient']} ({row['Clinic']})")
            
        with c_action:
            col_a, col_b = st.columns(2)
            with col_a:
                # 상태 전환 버튼 (진행중 <-> 완료)
                if row['Status'] == "진행중":
                    if st.button("완료처리", key=f"done_{i}"):
                        st.session_state.db[i]['Status'] = "완료"
                        st.session_state.selected_invoice = st.session_state.db[i]
                        st.rerun()
                else:
                    if st.button("되돌리기", key=f"undo_{i}"):
                        st.session_state.db[i]['Status'] = "진행중"
                        if st.session_state.selected_invoice == row:
                            st.session_state.selected_invoice = None
                        st.rerun()
            with col_b:
                if st.button("인보이스", key=f"inv_{i}"):
                    st.session_state.selected_invoice = row
                    st.rerun()

    # 인보이스 출력 영역
    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        invoice_html = f"""
        <div class="invoice-paper">
            <div style="display: flex; justify-content: space-between; margin-bottom: 40px;">
                <div>
                    <p style="font-size:9px; font-weight:bold;">DENTAL TECHNOLOGY LTD</p>
                    <h1 style="font-size:50px; font-style:italic; color:#1a4e8a !important; font-weight:900;">skycad</h1>
                    <p style="font-size:13px;">Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</p>
                </div>
                <div style="text-align:right;">
                    <h1 style="font-size:35px;">INVOICE</h1>
                    <p>No. 162084</p>
                    <p>{date.today().strftime('%-m/%-d/%Y')}</p>
                    <div style="margin-top:20px; text-align:left; float:right;">
                        <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Address']}<br>{inv['Phone']}
                    </div>
                </div>
            </div>
            <div style="margin-top:20px; padding:15px 0; border-top:2px solid black; border-bottom:2px solid black; font-size:18px; font-weight:bold;">
                Patient: &nbsp; {inv['Patient'].upper()}
            </div>
            <table style="width:100%; border-collapse:collapse; margin-top:10px; min-height:200px;">
                <thead><tr><th style="border-bottom:1px solid black; text-align:left; padding:10px 0;">Description</th><th style="border-bottom:1px solid black; text-align:right;">Amount</th></tr></thead>
                <tbody><tr><td style="padding:20px 0;">Nightguard ({inv['Material']}) {inv['Arch']}</td><td style="text-align:right;">$180.00</td></tr></tbody>
            </table>
            <div style="margin-top:50px;">
                <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:18px; margin-bottom:30px;">
                    <div>{inv['Case No']}</div><div>Total: $180.00</div>
                </div>
                <div style="border:1.5px solid black; padding:20px; text-align:center;">
                    <u style="font-weight:bold; font-size:16px; display:block; margin-bottom:10px;">All dental products we offer are custom made in Canada.</u>
                    <p style="font-size:12px; line-height:1.4;">Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.552% APR, Thank you.</p>
                </div>
            </div>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
        st.button("🖨️ 인쇄하기", on_click=None)
