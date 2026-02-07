import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 디자인 설정 - 버튼 크기 및 다크톤 테마]
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #30363d !important;
    }
    input:disabled { background-color: #262730 !important; color: #aaaaaa !important; border: 1px solid #4a4a4a !important; }
    .stButton>button { 
        width: auto !important; min-width: 80px; height: 2.2em !important; 
        background-color: #21262d !important; color: #c9d1d9 !important; 
        border: 1px solid #30363d !important; font-size: 13px !important;
        font-weight: 500 !important; border-radius: 6px; 
    }
    .stButton>button:hover { background-color: #30363d !important; border-color: #8b949e !important; color: #fff !important; }
    .stat-card { background-color: #161b22; padding: 18px; border-radius: 8px; border: 1px solid #30363d; margin-top: 30px; }
    .inv-outer-container { display: flex; justify-content: center; padding: 20px 0; background-color: #0d1117; }
    .invoice-letter { background-color: white !important; color: black !important; width: 8.5in; min-height: 11in; padding: 0.6in; border: 1px solid #d0d7de; box-sizing: border-box; font-family: 'Arial', sans-serif; }
    .invoice-letter * { color: black !important; line-height: 1.2; }
    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider, .stat-card { display: none !important; }
        .inv-outer-container { padding: 0; background: white; }
        .invoice-letter { border: none; width: 100%; padding: 0; margin: 0; }
    }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 관리 및 양방향 연동 로직]
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084

# 원본 데이터 (Clinic - Doctor 매핑)
ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Address": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9", "Phone": "(403) 970-0600"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier", "Address": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9", "Phone": "(780) 455-6806"},
])

# 세션 상태 초기화 (자동 연동용)
if 'sel_clinic' not in st.session_state: st.session_state.sel_clinic = "선택"
if 'sel_doctor' not in st.session_state: st.session_state.sel_doctor = "선택"

def update_from_clinic():
    if st.session_state.clinic_val != "선택":
        doc = ref_data[ref_data['Clinic'] == st.session_state.clinic_val]['Doctor'].iloc[0]
        st.session_state.sel_doctor = doc
    else:
        st.session_state.sel_doctor = "선택"

def update_from_doctor():
    if st.session_state.doctor_val != "선택":
        cln = ref_data[ref_data['Doctor'] == st.session_state.doctor_val]['Clinic'].iloc[0]
        st.session_state.sel_clinic = cln
    else:
        st.session_state.sel_clinic = "선택"

def get_business_day(start_date, days_to_subtract):
    current_date = start_date
    while days_to_subtract > 0:
        current_date -= timedelta(days=1)
        if current_date.weekday() < 5: days_to_subtract -= 1
    return current_date

# [3. 메인 화면]
st.markdown(f'<div style="padding:15px 0;"><span style="font-size: 22px; font-weight: 700;">🦷 Skycad Lab Manager</span></div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트", "🔍 검색"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No")
        patient = st.text_input("Patient")
        
        # Clinic 선택 (Doctor 자동 연동)
        cln_list = ["선택"] + sorted(ref_data['Clinic'].tolist())
        st.selectbox("Clinic", cln_list, key="clinic_val", 
                     index=cln_list.index(st.session_state.sel_clinic) if st.session_state.sel_clinic in cln_list else 0,
                     on_change=update_from_clinic)
        
        # Doctor 선택 (Clinic 자동 연동)
        doc_list = ["선택"] + sorted(ref_data['Doctor'].tolist())
        st.selectbox("Doctor", doc_list, key="doctor_val",
                     index=doc_list.index(st.session_state.sel_doctor) if st.session_state.sel_doctor in doc_list else 0,
                     on_change=update_from_doctor)

    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        rec_date = st.date_input("접수일", value=today, disabled=is_3d)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

    st.markdown("### 📅 일정")
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("Due Date", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("Lab Done", today + timedelta(days=1))
    with col4:
        # 현재 선택된 clinic 기준으로 지역 판단
        current_cln = st.session_state.clinic_val
        reg = ref_data[ref_data['Clinic']==current_cln]['Region'].iloc[0] if current_cln != "선택" else "Local"
        ship_date = get_business_day(due_date, 1 if reg=="Local" else 2)
        st.date_input("Shipping Date", ship_date)

    if st.button("💾 저장하기"):
        if st.session_state.clinic_val == "선택" or not case_no:
            st.error("필수 입력 누락")
        else:
            c_info = ref_data[ref_data['Clinic'] == st.session_state.clinic_val].iloc[0]
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter, "Case No": case_no, "Patient": patient, 
                "Clinic": st.session_state.clinic_val, "Doctor": st.session_state.doctor_val, 
                "Material": material, "Arch": arch, "Status": "Pending",
                "Address": c_info.get("Address", ""), "City": c_info.get("City", ""), "Phone": c_info.get("Phone", ""),
                "Inv_Date": today.strftime('%m/%d/%Y'), "Due": due_date, "Month": today.strftime('%Y-%m')
            })
            st.session_state.inv_counter += 1
            st.rerun()

# --- Tab 2: 리스트 ---
with tab2:
    this_month = date.today().strftime('%Y-%m')
    monthly_cases = [r for r in st.session_state.db if r.get('Month') == this_month]
    total_count = len(monthly_cases)
    over_count = max(0, total_count - 320)

    for i, row in enumerate(st.session_state.db):
        c_info, c_btn = st.columns([6, 1])
        with c_info:
            st.markdown(f"**{'🟡' if row.get('Status')=='Pending' else '🟢'} {row.get('Case No')}** | {row.get('Patient')} | {row.get('Clinic')}")
        with c_btn:
            if row.get('Status') == "Pending":
                if st.button("완료", key=f"cp_{i}"):
                    st.session_state.db[i]['Status'] = "Completed"
                    st.session_state.selected_invoice = st.session_state.db[i]
                    st.rerun()
            else:
                if st.button("재출력", key=f"re_{i}"):
                    st.session_state.selected_invoice = st.session_state.db[i]
                    st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        c_close, c_print = st.columns([0.1, 1])
        with c_close: 
            if st.button("닫기"): st.session_state.selected_invoice = None; st.rerun()
        with c_print:
            if st.button("인쇄"): st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="inv-outer-container">
            <div class="invoice-letter">
                <div style="display: flex; justify-content: space-between;">
                    <div><span style="font-size:8px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br><span style="font-size:38px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-2px;">skycad</span></div>
                    <div style="text-align: right;"><h1 style="font-size:32px; font-weight:400; margin:0;">INVOICE</h1><p style="font-size:12px;">No. {inv.get('Inv_No','')}<br>{inv.get('Inv_Date','')}</p></div>
                </div>
                <div style="margin-top: 40px; padding: 10px 0; border-top: 1.5px solid black; border-bottom: 1.5px solid black;"><b>Patient:</b> {str(inv.get('Patient','')).upper()}</div>
                <div style="height: 400px; margin-top: 30px;"><table style="width: 100%;"><tr style="border-bottom: 1px solid black;"><th style="text-align:left;">Description</th><th style="text-align:right;">Amount</th></tr><tr><td style="padding:20px 0;">Nightguard ({inv.get('Material','')}) {inv.get('Arch','')}</td><td style="text-align:right; font-weight:bold;">$180.00</td></tr></table></div>
                <div style="border-top: 1.5px solid black; padding-top: 10px;"><div style="display:flex; justify-content:space-between; font-weight:bold;"><div>Case: {inv.get('Case No','')}</div><div>Total: $180.00</div></div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""<div class="stat-card"><div style="display: flex; gap: 50px;"><div><p style="margin:0; font-size:12px; color:#8b949e;">{this_month} 수량</p><p style="font-size:20px; font-weight:bold;">{total_count} / 320</p></div><div><p style="margin:0; font-size:12px; color:#8b949e;">초과</p><p style="font-size:20px; font-weight:bold; color:#f85149;">{over_count} 개</p></div><div><p style="margin:0; font-size:12px; color:#8b949e;">인센티브 ($19.5)</p><p style="font-size:20px; font-weight:bold; color:#3fb950;">${over_count * 19.5:,.1f}</p></div></div></div>""", unsafe_allow_html=True)

with tab3: st.write("🔍 검색 기능 구현 예정")
