import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 기본 설정 및 디자인]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

now = datetime.now()
current_month = now.strftime('%m월')
PRE_TAX_UNIT = 30.0
POST_TAX_UNIT = 19.505333

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; }
    
    /* 슬림 대시보드 */
    .slim-dashboard {
        background: #1e212b; padding: 12px 20px; border-radius: 12px;
        border: 1px solid #3d414d; display: flex; justify-content: space-between;
        align-items: center; margin-bottom: 20px;
    }
    .stat-group { display: flex; align-items: baseline; gap: 8px; }
    .stat-label { color: #94a3b8; font-size: 0.8rem; font-weight: 500; }
    .stat-value { color: #ffffff; font-size: 1.2rem; font-weight: 700; }
    .stat-delta { color: #ff4b4b; font-size: 0.9rem; font-weight: 600; }
    .money-badge {
        background: #2d323e; padding: 4px 10px; border-radius: 6px;
        border: 1px solid #4ade80; margin-left: 8px; display: flex;
        flex-direction: column; align-items: center;
    }
    .money-text { color: #4ade80; font-weight: 600; font-size: 0.9rem; }
    .money-label-sub { font-size: 0.65rem; color: #94a3b8; }

    /* 인보이스 팝업 및 세련된 폰트 조절 */
    .invoice-overlay { 
        background-color: rgba(0,0,0,0.9); padding: 30px; 
        border-radius: 15px; border: 1px solid #444; margin-top: 20px;
    }
    .invoice-paper {
        background-color: #ffffff !important; width: 100%; max-width: 780px; 
        min-height: 950px; padding: 50px; border: 1px solid #000; margin: 0 auto;
        display: flex; flex-direction: column; color: #000 !important;
    }
    .invoice-paper * { 
        color: #000000 !important; -webkit-text-fill-color: #000000 !important; 
        font-family: 'Helvetica', 'Arial', sans-serif !important; 
    }
    
    /* 하단 공지 박스 글자 크기 축소 */
    .notice-box { 
        border: 1px solid black; padding: 12px; text-align: center; 
        margin-top: 25px; font-size: 10px; line-height: 1.4; color: #333 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 초기화]
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

# [3. 대시보드 출력]
total_count = len(st.session_state.db)
target = 320
remaining = total_count - target
total_pre_tax = total_count * PRE_TAX_UNIT
total_post_tax = total_count * POST_TAX_UNIT

st.markdown(f"""
    <div class="slim-dashboard">
        <div class="stat-group">
            <span class="stat-label">{current_month} 실적</span>
            <span class="stat-value">{total_count} / {target}</span>
            <span class="stat-delta">({remaining:+}개)</span>
        </div>
        <div style="display: flex;">
            <div class="money-badge" style="border-color: #555;">
                <span class="money-label-sub">PRE-TAX</span>
                <span class="money-text" style="color: #eee;">${total_pre_tax:,.2f}</span>
            </div>
            <div class="money-badge">
                <span class="money-label-sub" style="color: #4ade80;">AFTER-TAX</span>
                <span class="money-text">${total_post_tax:,.2f}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# [4. 탭 구성]
tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트", "🔍 검색"])

with tab1:
    st.markdown("### 📋 케이스 정보")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)")
        patient = st.text_input("Patient(환자명)")
        cln_list = ["선택"] + sorted(ref_data["Clinic"].tolist())
        def sync_c():
            if st.session_state.ck != "선택":
                st.session_state.dk = ref_data[ref_data["Clinic"] == st.session_state.ck]["Doctor"].iloc[0]
        st.selectbox("Clinic(병원명)", cln_list, key="ck", on_change=sync_c)
        st.selectbox("Doctor(의사명)", ["선택"] + sorted(ref_data["Doctor"].tolist()), key="dk")

    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        f_rec_date = "-" if is_3d else st.date_input("접수일", value=date.today())
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    clinic_reg = "Courier"
    if st.session_state.ck != "선택":
        clinic_reg = ref_data[ref_data["Clinic"] == st.session_state.ck]["Region"].iloc[0]

    with col5: due_date = st.date_input("요청일 (Due Date)", date.today() + timedelta(days=7))
    with col3: lab_done_date = st.date_input("완료일 (Lab Done)", date.today() + timedelta(days=1))
    with col4:
        ship_days = 1 if clinic_reg == "Local" else 2
        ship_date = get_business_day(due_date, ship_days)
        st.date_input("출고일 (Shipping Date)", value=ship_date)

    if st.button("💾 케이스 저장 및 등록"):
        if st.session_state.ck != "선택" and case_no:
            info = ref_data[ref_data["Clinic"] == st.session_state.ck].iloc[0]
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter, "Case No": case_no, "Patient": patient, 
                "Clinic": st.session_state.ck, "Doctor": st.session_state.dk, "Address": info["Address"], 
                "Phone": info["Phone"], "Material": material, "Arch": arch, "Status": "진행중",
                "Received Date": f_rec_date, "Lab Done": lab_done_date, "Due Date": due_date
            })
            st.session_state.inv_counter += 1
            st.rerun()

with tab2:
    st.markdown("### 📊 작업 리스트")
    for i, row in enumerate(st.session_state.db):
        l_col, b_col1, b_col2 = st.columns([3, 1, 1])
        with l_col: st.write(f"{'🟢' if row['Status'] == '완료' else '🟡'} **{row['Case No']}** | {row['Patient']} ({row['Clinic']})")
        with b_col1:
            if st.button("완료/복구", key=f"d_{i}"):
                st.session_state.db[i]['Status'] = "완료" if row['Status']=="진행중" else "진행중"
                st.rerun()
        with b_col2:
            if st.button("🔍 인보이스", key=f"v_{i}"): st.session_state.active_invoice = row

    if st.session_state.active_invoice:
        st.markdown('---')
        if st.button("❌ 미리보기 닫기"):
            st.session_state.active_invoice = None
            st.rerun()
        inv = st.session_state.active_invoice
        st.markdown(f"""
        <div class="invoice-overlay">
            <div class="invoice-paper">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 40px;">
                    <div>
                        <p style="font-size:9px; font-weight:bold; margin-bottom:4px;">DENTAL TECHNOLOGY LTD</p>
                        <h1 style="font-size: 48px; font-weight: 900; font-style: italic; color: #1a4e8a; margin:0; line-height:1;">skycad</h1>
                        <p style="font-size:12px; line-height:1.4; margin-top:8px;">Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</p>
                    </div>
                    <div style="text-align: right;">
                        <h1 style="font-size:38px; font-weight:400; margin:0 0 12px 0; letter-spacing:1px;">INVOICE</h1>
                        <p style="margin:0; font-size:13px;">No. {inv['Inv_No']}</p>
                        <p style="margin:0 0 20px 0; font-size:13px;">{date.today().strftime('%-m/%-d/%Y')}</p>
                        <div style="text-align:left; display:inline-block; font-size:12px; line-height:1.4; border-top:1px solid #000; padding-top:8px;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Address']}<br>{inv['Phone']}
                        </div>
                    </div>
                </div>
                <div style="margin: 20px 0; padding: 10px 0; border-top: 1.5px solid black; border-bottom: 1.5px solid black; font-size: 16px; font-weight: bold; letter-spacing:0.5px;">
                    Patient: &nbsp; {inv['Patient'].upper()}
                </div>
                <table style="width: 100%; border-collapse: collapse; flex-grow: 1;">
                    <thead><tr><th style="text-align:left; border-bottom: 1px solid black; padding: 8px 0; font-size:13px;">Description</th><th style="text-align:right; border-bottom: 1px solid black; padding: 8px 0; font-size:13px;">Amount</th></tr></thead>
                    <tbody><tr><td style="padding:20px 0; font-size: 15px;">Nightguard ({inv['Material']}) {inv['Arch']}</td><td style="text-align:right; font-size: 15px;">$180.00</td></tr></tbody>
                </table>
                <div style="margin-top: auto;">
                    <div style="display:flex; justify-content:space-between; font-weight:500; font-size:16px; border-top:1px solid #ddd; padding-top:10px; margin-bottom:15px;">
                        <div style="color:#555 !important;">{inv['Case No']}</div><div>Total: $180.00</div>
                    </div>
                    <div class="notice-box">
                        <u style="font-weight:bold; display:block; margin-bottom:5px; font-size:11px;">All dental products we offer are custom made in Canada.</u>
                        Please ensure your monthly payment is made within 30 days of receiving your statement. 
                        Any balances remaining after 30 days will be automatically charged to the credit card on file. 
                        Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month (19.552% APR). Thank you.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
