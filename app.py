import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 디자인 설정 - 제목, 제작자 정보, 섹션 가독성 강화]
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #30363d !important;
    }
    input:disabled { background-color: #21262d !important; color: #8b949e !important; }

    .header-box {
        display: flex; justify-content: space-between; align-items: flex-end;
        padding-bottom: 15px; border-bottom: 2px solid #30363d; margin-bottom: 25px;
    }
    .main-title { font-size: 36px !important; font-weight: 800 !important; color: #ffffff !important; }
    .creator-info { font-size: 14px !important; color: #8b949e !important; font-style: italic; }

    .section-header {
        font-size: 22px !important; font-weight: 700 !important; color: #4c6ef5 !important;
        margin-top: 30px !important; margin-bottom: 15px !important; display: block;
    }

    .stButton>button { 
        width: auto !important; min-width: 100px !important; height: 2.4em !important; 
        background-color: #21262d !important; color: #c9d1d9 !important; 
        border: 1px solid #30363d !important; font-size: 14px !important;
        font-weight: 600 !important; border-radius: 6px !important; 
    }
    .stButton>button:hover { background-color: #30363d !important; border-color: #8b949e !important; color: #fff !important; }

    .stat-card { background-color: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-top: 30px; }
    
    .inv-outer-container { display: flex; justify-content: center; padding: 20px 0; background-color: #0d1117; }
    .invoice-letter { background-color: white !important; color: black !important; width: 8.5in; min-height: 11in; padding: 0.6in; border: 1px solid #d0d7de; box-sizing: border-box; font-family: 'Arial', sans-serif; }
    .invoice-letter * { color: black !important; line-height: 1.2; }
    
    @media print {
        .stButton, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider, .stat-card { display: none !important; }
        .inv-outer-container { padding: 0; background: white; }
        .invoice-letter { border: none; width: 100%; padding: 0; margin: 0; }
    }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 및 세션 관리]
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084

# 마스터 데이터 (병원-의사 매핑)
ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Address": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier", "Address": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9"},
])

# 양방향 연동을 위한 세션 변수
if 'cur_cln' not in st.session_state: st.session_state.cur_cln = "선택"
if 'cur_doc' not in st.session_state: st.session_state.cur_doc = "선택"

def on_cln_change():
    val = st.session_state.cln_select
    if val != "선택":
        st.session_state.cur_cln = val
        st.session_state.cur_doc = ref_data[ref_data['Clinic'] == val]['Doctor'].iloc[0]
    else:
        st.session_state.cur_cln = "선택"; st.session_state.cur_doc = "선택"

def on_doc_change():
    val = st.session_state.doc_select
    if val != "선택":
        st.session_state.cur_doc = val
        st.session_state.cur_cln = ref_data[ref_data['Doctor'] == val]['Clinic'].iloc[0]
    else:
        st.session_state.cur_cln = "선택"; st.session_state.cur_doc = "선택"

def get_business_day(start_date, days_to_subtract):
    curr = start_date
    while days_to_subtract > 0:
        curr -= timedelta(days=1)
        if curr.weekday() < 5: days_to_subtract -= 1
    return curr

# [3. 메인 화면]
st.markdown('<div class="header-box"><div class="main-title">🦷 Skycad Lab Manager</div><div class="creator-info">Created by Heechul Jung</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료", "🔍 검색"])

# --- Tab 1: 케이스 등록 ---
with tab1:
    st.markdown('<span class="section-header">📋 기본정보입력</span>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No (팬번호)")
        patient = st.text_input("Patient (환자명)")
        
        clns = ["선택"] + sorted(ref_data['Clinic'].tolist())
        st.selectbox("Clinic (병원명)", clns, key="cln_select", 
                     index=clns.index(st.session_state.cur_cln), on_change=on_cln_change)
        
        docs = ["선택"] + sorted(ref_data['Doctor'].tolist())
        st.selectbox("Doctor (의사명)", docs, key="doc_select", 
                     index=docs.index(st.session_state.cur_doc), on_change=on_doc_change)
                     
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        rec_date = st.date_input("접수일", value=today, disabled=is_3d)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

    st.markdown('<span class="section-header">📅 일정 관리</span>', unsafe_allow_html=True)
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("Due Date (요청일)", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("Lab Done (완료일)", today + timedelta(days=1))
    with col4:
        reg = ref_data[ref_data['Clinic']==st.session_state.cur_cln]['Region'].iloc[0] if st.session_state.cur_cln != "선택" else "Local"
        ship_date = get_business_day(due_date, 1 if reg=="Local" else 2)
        st.date_input("Shipping Date (출고일)", ship_date)

    if st.button("💾 케이스 저장하기"):
        if st.session_state.cur_cln == "선택" or not case_no:
            st.error("Case No와 Clinic을 확인하세요.")
        else:
            c_info = ref_data[ref_data['Clinic'] == st.session_state.cur_cln].iloc[0]
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter, "Case No": case_no, "Patient": patient, 
                "Clinic": st.session_state.cur_cln, "Doctor": st.session_state.cur_doc, 
                "Material": material, "Arch": arch, "Status": "Pending",
                "Address": c_info.get("Address", ""), "City": c_info.get("City", ""),
                "Inv_Date": today.strftime('%m/%d/%Y'), "Due": due_date, "Month": today.strftime('%Y-%m')
            })
            st.session_state.inv_counter += 1
            st.success(f"{case_no}번 저장 완료!")
            st.rerun()

# --- Tab 2: 리스트 및 수량 관리 ---
with tab2:
    st.markdown('<span class="section-header">📊 작업 진행 리스트</span>', unsafe_allow_html=True)
    this_month = date.today().strftime('%Y-%m')
    monthly_cases = [r for r in st.session_state.db if r.get('Month') == this_month]
    total_count = len(monthly_cases)
    over_count = max(0, total_count - 320)

    for i, row in enumerate(st.session_state.db):
        c_info, c_btn = st.columns([6, 1])
        with c_info:
            icon = "🟢" if row.get('Status')=="Completed" else "🟡"
            st.markdown(f"**{icon} {row.get('Case No')}** | {row.get('Patient')} | {row.get('Clinic')} | Due: {row.get('Due')}")
        with c_btn:
            lbl = "완료" if row.get('Status') == "Pending" else "재출력"
            if st.button(lbl, key=f"btn_{i}"):
                st.session_state.db[i]['Status'] = "Completed"
                st.session_state.selected_invoice = st.session_state.db[i]
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        c_cl, c_pr = st.columns([0.1, 1])
        with c_cl: 
            if st.button("닫기"): st.session_state.selected_invoice = None; st.rerun()
        with c_pr:
            if st.button("인쇄"): st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="inv-outer-container">
            <div class="invoice-letter">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <span style="font-size:8px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                        <span style="font-size:38px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-2px;">skycad</span>
                        <div style="font-size:11px; margin-top:15px;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9</div>
                    </div>
                    <div style="text-align: right;">
                        <h1 style="font-size:32px; font-weight:400; margin:0;">INVOICE</h1>
                        <p style="font-size:12px;">No. {inv.get('Inv_No','')}<br>{inv.get('Inv_Date','')}</p>
                    </div>
                </div>
                <div style="margin-top: 40px; padding: 10px 0; border-top: 1.5px solid black; border-bottom: 1.5px solid black;"><b>Patient:</b> {str(inv.get('Patient','')).upper()}</div>
                <div style="height: 400px; margin-top: 30px;"><table style="width:100%;"><tr style="border-bottom:1px solid black;"><th style="text-align:left;">Description</th><th style="text-align:right;">Amount</th></tr><tr><td style="padding:20px 0;">Nightguard ({inv.get('Material','')}) {inv.get('Arch','')}</td><td style="text-align:right; font-weight:bold;">$180.00</td></tr></table></div>
                <div style="border-top: 1.5px solid black; padding-top: 10px;"><div style="display:flex; justify-content:space-between; font-weight:bold;"><div>Case: {inv.get('Case No','')}</div><div>Total: $180.00</div></div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="stat-card">
        <div style="display: flex; gap: 50px;">
            <div><p style="margin:0; font-size:12px; color:#8b949e;">{this_month} 수량</p><p style="font-size:20px; font-weight:bold;">{total_count} / 320</p></div>
            <div><p style="margin:0; font-size:12px; color:#8b949e;">초과분</p><p style="font-size:20px; font-weight:bold; color:#f85149;">{over_count} 개</p></div>
            <div><p style="margin:0; font-size:12px; color:#8b949e;">인센티브 ($19.5)</p><p style="font-size:20px; font-weight:bold; color:#3fb950;">${over_count * 19.5:,.1f}</p></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with tab3: st.write("🔍 검색 기능 구현 예정")
