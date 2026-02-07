import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 기본 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; }
    .invoice-wrapper { display: flex; justify-content: center; padding: 20px; background-color: #262730; }
    .invoice-paper {
        background-color: #ffffff !important;
        width: 100%; max-width: 800px; 
        aspect-ratio: 8.5 / 11; padding: 50px; border: 1px solid #000;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: flex; flex-direction: column; box-sizing: border-box;
    }
    .invoice-paper * {
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important;
        font-family: 'Arial', sans-serif !important;
    }
    .logo-main { font-size: 58px !important; font-weight: 900; font-style: italic; color: #1a4e8a !important; line-height: 1; }
    .patient-line { margin: 25px 0; padding: 15px 0; border-top: 2.5px solid black; border-bottom: 2.5px solid black; font-size: 20px; font-weight: bold; }
    .item-table { width: 100%; border-collapse: collapse; flex-grow: 1; }
    .item-table th { border-bottom: 1.5px solid black; padding: 10px 0; text-align: left; }
    .item-table td { padding: 25px 0; font-size: 17px; }
    .bottom-box { margin-top: auto; }
    .notice-box { border: 1.5px solid black; padding: 15px; text-align: center; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 초기화 및 로직]
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Amhipreat Kaur", "Address": "13510 177 St NW, Edmonton, AB", "Phone": "(780) 455-6806", "Region": "Courier"},
    {"Clinic": "Calgary Central Dental", "Doctor": "Dr. Lana Huynh", "Address": "205-7136 11 St NE, Calgary, AB", "Phone": "(403) 970-0600", "Region": "Local"}
])

def get_business_day(start_date, days):
    curr = start_date
    while days > 0:
        curr -= timedelta(days=1)
        if curr.weekday() < 5: days -= 1
    return curr

# [3. UI 화면]
tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트", "🔍 검색"])

with tab1:
    st.markdown("### 📋 케이스 등록 (기본정보)")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: ET177")
        patient = st.text_input("Patient(환자명)")
        
        # 병원/의사 드롭다운 연동
        cln_list = ["선택"] + sorted(ref_data["Clinic"].tolist())
        doc_list = ["선택"] + sorted(ref_data["Doctor"].tolist())
        def sync_c():
            if st.session_state.ck != "선택":
                st.session_state.dk = ref_data[ref_data["Clinic"] == st.session_state.ck]["Doctor"].iloc[0]
        def sync_d():
            if st.session_state.dk != "선택":
                st.session_state.ck = ref_data[ref_data["Doctor"] == st.session_state.dk]["Clinic"].iloc[0]

        sel_clinic = st.selectbox("Clinic(병원명)", cln_list, key="ck", on_change=sync_c)
        sel_doctor = st.selectbox("Doctor(의사명)", doc_list, key="dk", on_change=sync_d)

    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        rec_date = st.date_input("접수일(Received Date)", date.today())
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    st.markdown("### 📅 일정 관리 (기본설정)")
    col3, col4, col5 = st.columns(3)
    
    # 병원 지역 정보 가져오기
    clinic_reg = "Courier"
    if st.session_state.ck != "선택":
        clinic_reg = ref_data[ref_data["Clinic"] == st.session_state.ck]["Region"].iloc[0]

    with col5: 
        due_date = st.date_input("요청일 (Due Date)", date.today() + timedelta(days=7))
    with col3: 
        lab_done_date = st.date_input("완료일 (Lab Done)", date.today() + timedelta(days=1))
    with col4:
        # 지역별 출고일 계산 복구
        ship_days = 1 if clinic_reg == "Local" else 2
        ship_date = get_business_day(due_date, ship_days)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("💾 케이스 저장 및 등록"):
        if st.session_state.ck == "선택" or not case_no:
            st.error("필수 정보를 입력해주세요.")
        else:
            info = ref_data[ref_data["Clinic"] == st.session_state.ck].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": st.session_state.ck,
                "Doctor": st.session_state.dk, "Address": info["Address"], "Phone": info["Phone"],
                "Material": material, "Arch": arch, "Status": "진행중",
                "Lab Done": lab_done_date, "Due Date": due_date
            })
            st.success("성공적으로 등록되었습니다.")

with tab2:
    st.subheader("📊 작업 상황 리스트")
    for i, row in enumerate(st.session_state.db):
        cols = st.columns([3, 1, 1])
        status_icon = "🟡" if row['Status'] == "진행중" else "🟢"
        cols[0].write(f"{status_icon} **{row['Case No']}** | {row['Patient']} ({row['Clinic']})")
        if cols[1].button("완료/되돌리기", key=f"s_{i}"):
            st.session_state.db[i]['Status'] = "완료" if row['Status'] == "진행중" else "진행중"
            st.rerun()
        if cols[2].button("인보이스 보기", key=f"i_{i}"):
            st.session_state.selected_invoice = row

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.markdown('<div class="invoice-wrapper">', unsafe_allow_html=True)
        invoice_content = f"""
<div class="invoice-paper">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 40px;">
        <div style="flex: 1;">
            <p style="font-size:10px; font-weight:bold; margin-bottom:5px;">DENTAL TECHNOLOGY LTD</p>
            <h1 class="logo-main" style="margin:0;">skycad</h1>
            <p style="font-size:14px; line-height:1.3;">Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</p>
        </div>
        <div style="flex: 1; text-align: right;">
            <h1 style="font-size:42px; font-weight:500; margin:0 0 15px 0;">INVOICE</h1>
            <p style="margin:0;">No. 162084</p>
            <p style="margin:0 0 20px 0;">{date.today().strftime('%-m/%-d/%Y')}</p>
            <div style="text-align:left; display:inline-block; font-size:13px; line-height:1.3;">
                <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Address']}<br>{inv['Phone']}
            </div>
        </div>
    </div>
    <div class="patient-line">Patient: &nbsp; {inv['Patient'].upper()}</div>
    <table class="item-table">
        <thead>
            <tr><th style="text-align:left;">Description</th><th style="text-align:right;">Amount</th></tr>
        </thead>
        <tbody>
            <tr>
                <td style="padding:25px 0;">Nightguard ({inv['Material']}) {inv['Arch']}</td>
                <td style="text-align:right;">$180.00</td>
            </tr>
        </tbody>
    </table>
    <div class="bottom-box">
        <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:20px; margin-bottom:15px; border-top:1px solid #eee; padding-top:10px;">
            <div>{inv['Case No']}</div>
            <div>Total: $180.00</div>
        </div>
        <div class="notice-box">
            <u style="font-weight:bold; display:block; margin-bottom:8px; font-size:14px; text-align:center;">All dental products we offer are custom made in Canada.</u>
            <p style="font-size:11px; line-height:1.4; text-align:center; margin:0;">Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.552% APR, Thank you.</p>
        </div>
    </div>
</div>"""
        st.markdown(invoice_content, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
