import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 기본 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; }
    /* 인보이스 미리보기 팝업 배경 */
    .invoice-overlay {
        background-color: rgba(0,0,0,0.8); padding: 40px; border-radius: 15px;
        border: 1px solid #444; margin-top: 20px;
    }
    .invoice-paper {
        background-color: #ffffff !important; width: 100%; max-width: 800px; 
        aspect-ratio: 8.5 / 11; padding: 50px; border: 1px solid #000;
        margin: 0 auto; display: flex; flex-direction: column; box-sizing: border-box;
    }
    .invoice-paper * { color: #000000 !important; -webkit-text-fill-color: #000000 !important; font-family: 'Arial', sans-serif !important; }
    .logo-main { font-size: 58px !important; font-weight: 900; font-style: italic; color: #1a4e8a !important; line-height: 1; }
    .patient-line { margin: 25px 0; padding: 15px 0; border-top: 2.5px solid black; border-bottom: 2.5px solid black; font-size: 20px; font-weight: bold; }
    .item-table { width: 100%; border-collapse: collapse; flex-grow: 1; }
    .item-table th { border-bottom: 1.5px solid black; padding: 10px 0; text-align: left; }
    .item-table td { padding: 25px 0; font-size: 17px; }
    .bottom-box { margin-top: auto; }
    .notice-box { border: 1.5px solid black; padding: 15px; text-align: center; margin-top: 10px; }
    .metric-container { background-color: #1e212b; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #3d414d; }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 초기화]
if 'db' not in st.session_state: st.session_state.db = []
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084  # 시작 번호
if 'active_invoice' not in st.session_state: st.session_state.active_invoice = None

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
tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트 / 정산", "🔍 검색"])

with tab1:
    st.markdown("### 📋 케이스 등록")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: ET177")
        patient = st.text_input("Patient(환자명)")
        cln_list = ["선택"] + sorted(ref_data["Clinic"].tolist())
        doc_list = ["선택"] + sorted(ref_data["Doctor"].tolist())
        
        def sync_c():
            if st.session_state.ck != "선택":
                st.session_state.dk = ref_data[ref_data["Clinic"] == st.session_state.ck]["Doctor"].iloc[0]
        def sync_d():
            if st.session_state.dk != "선택":
                st.session_state.ck = ref_data[ref_data["Doctor"] == st.session_state.dk]["Clinic"].iloc[0]
        
        st.selectbox("Clinic(병원명)", cln_list, key="ck", on_change=sync_c)
        st.selectbox("Doctor(의사명)", doc_list, key="dk", on_change=sync_d)

    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        f_rec_date = "-" if is_3d else st.date_input("접수일", value=date.today())
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    if st.button("💾 케이스 저장"):
        if st.session_state.ck == "선택" or not case_no:
            st.error("필수 정보를 입력해주세요.")
        else:
            info = ref_data[ref_data["Clinic"] == st.session_state.ck].iloc[0]
            # 인보이스 번호 자동 할당 및 카운터 증가
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter,
                "Case No": case_no, "Patient": patient, "Clinic": st.session_state.ck,
                "Doctor": st.session_state.dk, "Address": info["Address"], "Phone": info["Phone"],
                "Material": material, "Arch": arch, "Status": "진행중", "Date": f_rec_date
            })
            st.session_state.inv_counter += 1
            st.success(f"등록 완료! (Invoice No. {st.session_state.inv_counter-1})")

with tab2:
    # [정산 대시보드] - 이전과 동일
    total_count = len(st.session_state.db)
    st.markdown(f'<div class="metric-container"><h4>📊 이달의 실적: {total_count} / 320</h4></div>', unsafe_allow_html=True)

    # [리스트 출력]
    for i, row in enumerate(st.session_state.db):
        l_col, b_col1, b_col2 = st.columns([3, 1, 1])
        with l_col: st.write(f"{'🟢' if row['Status'] == '완료' else '🟡'} **{row['Case No']}** | {row['Patient']}")
        with b_col1: 
            if st.button("완료/복구", key=f"done_{i}"):
                st.session_state.db[i]['Status'] = "완료" if row['Status']=="진행중" else "진행중"
                st.rerun()
        with b_col2:
            if st.button("🔍 인보이스", key=f"inv_{i}"):
                st.session_state.active_invoice = row # 클릭 시에만 데이터 로드

    # [인보이스 미리보기 영역 - 클릭했을 때만 활성화]
    if st.session_state.active_invoice:
        st.markdown('---')
        inv = st.session_state.active_invoice
        col_c1, col_c2 = st.columns([5, 1])
        col_c1.subheader(f"📄 Invoice Preview (No. {inv['Inv_No']})")
        if col_c2.button("❌ 닫기"):
            st.session_state.active_invoice = None
            st.rerun()

        st.markdown('<div class="invoice-overlay">', unsafe_allow_html=True)
        invoice_html = f"""<div class="invoice-paper">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 40px;">
                <div style="flex: 1;">
                    <p style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY LTD</p>
                    <h1 class="logo-main" style="margin:0;">skycad</h1>
                    <p style="font-size:14px; line-height:1.3;">Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</p>
                </div>
                <div style="flex: 1; text-align: right;">
                    <h1 style="font-size:42px; font-weight:500; margin:0 0 15px 0;">INVOICE</h1>
                    <p style="margin:0;">No. {inv['Inv_No']}</p><p style="margin:0 0 20px 0;">{date.today().strftime('%-m/%-d/%Y')}</p>
                    <div style="text-align:left; display:inline-block; font-size:13px;"><b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Address']}<br>{inv['Phone']}</div>
                </div>
            </div>
            <div class="patient-line">Patient: &nbsp; {inv['Patient'].upper()}</div>
            <table class="item-table"><thead><tr><th>Description</th><th style="text-align:right;">Amount</th></tr></thead>
            <tbody><tr><td style="padding:25px 0;">Nightguard ({inv['Material']}) {inv['Arch']}</td><td style="text-align:right;">$180.00</td></tr></tbody></table>
            <div class="bottom-box"><div style="display:flex; justify-content:space-between; font-weight:bold; font-size:20px; border-top:1px solid #eee; padding-top:10px;">
            <div>{inv['Case No']}</div><div>Total: $180.00</div></div>
            <div class="notice-box"><p style="font-size:11px; margin:0;">All dental products we offer are custom made in Canada. Thank you.</p></div></div></div>"""
        st.markdown(invoice_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
