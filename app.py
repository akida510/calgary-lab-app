import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 기본 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

# 현재 월 및 단가 설정
now = datetime.now()
current_month_name = now.strftime('%m월')
PRE_TAX_UNIT = 30.0
POST_TAX_UNIT = 19.505333

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; }
    .metric-card {
        background: linear-gradient(135deg, #1e2130 0%, #11141d 100%);
        padding: 25px; border-radius: 15px; border: 1px solid #3498db;
        text-align: center; margin-bottom: 25px;
    }
    .metric-title { font-size: 1.1rem; color: #94a3b8; margin-bottom: 8px; }
    .metric-value { font-size: 2.2rem; font-weight: bold; color: #ffffff; margin-bottom: 5px; }
    .metric-delta { font-size: 1.3rem; color: #ef4444; font-weight: bold; margin-bottom: 15px; }
    .money-grid { display: flex; justify-content: center; gap: 20px; border-top: 1px solid #334155; padding-top: 15px; }
    .money-item { text-align: center; }
    .money-label { font-size: 0.8rem; color: #94a3b8; }
    .money-amount { font-size: 1.2rem; font-weight: bold; color: #10b981; }
    
    .invoice-overlay { background-color: rgba(0,0,0,0.85); padding: 30px; border-radius: 10px; border: 1px solid #444; }
    .invoice-paper {
        background-color: #ffffff !important; width: 100%; max-width: 800px; 
        aspect-ratio: 8.5 / 11; padding: 50px; border: 1px solid #000; margin: 0 auto;
        display: flex; flex-direction: column; box-sizing: border-box;
    }
    .invoice-paper * { color: #000000 !important; -webkit-text-fill-color: #000000 !important; font-family: 'Arial', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 초기화 및 함수]
if 'db' not in st.session_state: st.session_state.db = []
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084
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

# [3. UI 탭 구성]
tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 실적 및 리스트", "🔍 검색"])

with tab1:
    st.markdown("### 📋 케이스 기본 정보")
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
        if is_3d:
            st.text_input("접수일(Received Date)", value="-", disabled=True)
            f_rec_date = "-"
        else:
            f_rec_date = st.date_input("접수일(Received Date)", value=date.today())
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    # [중요] 일정 등록 섹션 복구
    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    
    # 지역 정보에 따른 출고일 계산
    clinic_reg = "Courier"
    if st.session_state.ck != "선택":
        clinic_reg = ref_data[ref_data["Clinic"] == st.session_state.ck]["Region"].iloc[0]

    with col5: 
        due_date = st.date_input("요청일 (Due Date)", date.today() + timedelta(days=7))
    with col3: 
        lab_done_date = st.date_input("완료일 (Lab Done)", date.today() + timedelta(days=1))
    with col4:
        ship_days = 1 if clinic_reg == "Local" else 2
        ship_date = get_business_day(due_date, ship_days)
        st.date_input("출고일 (Shipping Date)", value=ship_date)

    if st.button("💾 케이스 저장 및 등록"):
        if st.session_state.ck == "선택" or not case_no:
            st.error("필수 정보를 입력해주세요.")
        else:
            info = ref_data[ref_data["Clinic"] == st.session_state.ck].iloc[0]
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter,
                "Case No": case_no, "Patient": patient, "Clinic": st.session_state.ck,
                "Doctor": st.session_state.dk, "Address": info["Address"], "Phone": info["Phone"],
                "Material": material, "Arch": arch, "Status": "진행중", 
                "Received Date": f_rec_date, "Lab Done": lab_done_date, "Due Date": due_date
            })
            st.session_state.inv_counter += 1
            st.success(f"등록 완료! (Invoice No. {st.session_state.inv_counter-1})")

with tab2:
    # [정산 대시보드]
    total_count = len(st.session_state.db)
    target = 320
    remaining = total_count - target
    total_pre_tax = total_count * PRE_TAX_UNIT
    total_post_tax = total_count * POST_TAX_UNIT

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">📅 {current_month_name} 작업 현황 및 정산</div>
        <div class="metric-value">{total_count} / {target}개</div>
        <div class="metric-delta">({remaining:+}개)</div>
        <div class="money-grid">
            <div class="money-item">
                <div class="money-label">세전 총액 (Pre-tax)</div>
                <div class="money-amount">${total_pre_tax:,.2f}</div>
            </div>
            <div style="border-left: 1px solid #334155; height: 40px; margin-top: 5px;"></div>
            <div class="money-item">
                <div class="money-label">세후 총액 (After-tax)</div>
                <div class="money-amount" style="color: #3498db;">${total_post_tax:,.2f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # [리스트 출력]
    st.markdown("### 📊 작업 리스트")
    for i, row in enumerate(st.session_state.db):
        l_col, b_col1, b_col2 = st.columns([3, 1, 1])
        with l_col:
            st.write(f"{'🟢' if row['Status'] == '완료' else '🟡'} **{row['Case No']}** | {row['Patient']} ({row['Clinic']})")
        with b_col1:
            if st.button("완료/복구", key=f"d_{i}"):
                st.session_state.db[i]['Status'] = "완료" if row['Status']=="진행중" else "진행중"
                st.rerun()
        with b_col2:
            if st.button("🔍 인보이스", key=f"v_{i}"):
                st.session_state.active_invoice = row

    # [인보이스 팝업] - 생략 없이 전체 구조 유지
    if st.session_state.active_invoice:
        st.markdown('---')
        if st.button("❌ 미리보기 닫기"):
            st.session_state.active_invoice = None
            st.rerun()
        inv = st.session_state.active_invoice
        st.markdown('<div class="invoice-overlay">', unsafe_allow_html=True)
        # 인보이스 상세 HTML
        st.markdown(f"""
        <div class="invoice-paper">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 40px;">
                <div style="flex: 1;">
                    <p style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY LTD</p>
                    <h1 style="font-size: 58px; font-weight: 900; font-style: italic; color: #1a4e8a; margin:0;">skycad</h1>
                </div>
                <div style="flex: 1; text-align: right;">
                    <h1 style="font-size:42px; font-weight:500; margin:0 0 15px 0;">INVOICE</h1>
                    <p style="margin:0;">No. {inv['Inv_No']}</p>
                    <p style="margin:0 0 20px 0;">{date.today().strftime('%-m/%-d/%Y')}</p>
                </div>
            </div>
            <div style="margin: 25px 0; padding: 15px 0; border-top: 2.5px solid black; border-bottom: 2.5px solid black; font-size: 20px; font-weight: bold;">
                Patient: &nbsp; {inv['Patient'].upper()}
            </div>
            <table style="width: 100%; border-collapse: collapse; flex-grow: 1;">
                <thead><tr><th style="text-align:left; border-bottom: 1.5px solid black;">Description</th><th style="text-align:right; border-bottom: 1.5px solid black;">Amount</th></tr></thead>
                <tbody><tr><td style="padding:25px 0;">Nightguard ({inv['Material']}) {inv['Arch']}</td><td style="text-align:right;">$180.00</td></tr></tbody>
            </table>
            <div style="margin-top: auto; display:flex; justify-content:space-between; font-weight:bold; font-size:20px; border-top:1px solid #eee; padding-top:10px;">
                <div>{inv['Case No']}</div><div>Total: $180.00</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
