import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 디자인 설정 및 테마 강제 고정]
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="wide")

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
    
    /* 버튼 사이즈 조정 (지나치게 큰 버튼 방지) */
    .stButton>button { 
        width: 100%; height: 2.8em !important; background-color: #4c6ef5 !important; 
        color: white !important; font-weight: bold; border-radius: 5px; 
    }
    
    /* 인센티브 현황판 스타일 */
    .stat-card {
        background-color: #1a1c24; padding: 20px; border-radius: 10px;
        border: 1px solid #30363d; margin-top: 20px;
    }

    /* 인보이스 디자인 - 레터지 비율 및 박스 */
    .inv-outer-container {
        display: flex; justify-content: center; padding: 20px 0; background-color: #333;
    }
    .invoice-letter {
        background-color: white !important; color: black !important;
        width: 8.5in; min-height: 11in; padding: 0.6in;
        border: 1.5px solid black; box-sizing: border-box;
        font-family: 'Arial', sans-serif;
    }
    .invoice-letter * { color: black !important; line-height: 1.2; }
    
    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider, .stat-card { display: none !important; }
        .inv-outer-container { padding: 0; background: white; }
        .invoice-letter { border: none; width: 100%; padding: 0; margin: 0; }
    }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 관리]
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Address": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9", "Phone": "(403) 970-0600"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier", "Address": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9", "Phone": "(780) 455-6806"},
])

def get_business_day(start_date, days_to_subtract):
    current_date = start_date
    while days_to_subtract > 0:
        current_date -= timedelta(days=1)
        if current_date.weekday() < 5: days_to_subtract -= 1
    return current_date

# [3. 메인 화면]
st.markdown(f'<div class="header-container"><div style="font-size: 24px; font-weight: 800;">🦷 Skycad Lab Night Guard Manager</div><div style="font-size: 12px;">Heechul Jung Edition</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료", "🔍 검색"])

# --- Tab 1: 케이스 등록 (기존 로직 100% 유지) ---
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
        if is_3d:
            st.text_input("접수일", value=today.strftime("%Y-%m-%d"), disabled=True)
            rec_date = today
        else:
            rec_date = st.date_input("접수일", today)
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
            st.error("Case No와 Clinic은 필수입니다.")
        else:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter, "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Material": material, "Arch": arch, "Status": "Pending",
                "Address": c_info.get("Address", ""), "City": c_info.get("City", ""), "Phone": c_info.get("Phone", ""),
                "Inv_Date": today.strftime('%m/%d/%Y'), "Due": due_date, "Month": today.strftime('%Y-%m')
            })
            st.session_state.inv_counter += 1
            st.success(f"{case_no}번 저장 완료!")

# --- Tab 2: 리스트 및 수량 관리 ---
with tab2:
    st.subheader("📊 작업 진행 리스트")
    
    # 작업 통계 계산 (이번 달 기준)
    this_month = date.today().strftime('%Y-%m')
    monthly_cases = [r for r in st.session_state.db if r.get('Month') == this_month]
    total_count = len(monthly_cases)
    over_count = max(0, total_count - 320)
    extra_pre_tax = over_count * 30
    extra_post_tax = over_count * 19.5

    for i, row in enumerate(st.session_state.db):
        c_info, c_btn = st.columns([4, 1.2]) # 버튼 컬럼 살짝 조절
        with c_info:
            curr_status = row.get('Status', 'Pending')
            st.markdown(f"**{'🟡' if curr_status=='Pending' else '🟢'} {row.get('Case No','-')}** | {row.get('Patient','-')} | {row.get('Clinic','-')} | Due: {row.get('Due','-')}")
        with c_btn:
            if curr_status == "Pending":
                if st.button("완료/인보이스", key=f"cp_{i}"):
                    st.session_state.db[i]['Status'] = "Completed"
                    st.session_state.selected_invoice = st.session_state.db[i]
                    st.rerun()
            else:
                # 버튼 크기를 적절하게 조절 (st.button 기본 스타일 사용)
                if st.button("재출력", key=f"re_{i}"):
                    st.session_state.selected_invoice = st.session_state.db[i]
                    st.rerun()

    # 인보이스 출력 영역
    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        if st.button("닫기 (Close Invoice)", use_container_width=False):
            st.session_state.selected_invoice = None
            st.rerun()
        
        # [인보이스 디자인 - 사진 기준 재현]
        st.markdown(f"""
        <div class="inv-outer-container">
            <div class="invoice-letter">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <div style="line-height:1;">
                            <span style="font-size:8px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                            <span style="font-size:38px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-2px;">skycad</span>
                        </div>
                        <div style="font-size:11px; margin-top:15px; line-height:1.4;">
                            <b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600
                        </div>
                    </div>
                    <div style="text-align: right; line-height:1.2;">
                        <h1 style="font-size:32px; font-weight:400; margin:0; letter-spacing:1px;">INVOICE</h1>
                        <p style="font-size:12px; margin:8px 0;">No. {inv.get('Inv_No','')}<br>{inv.get('Inv_Date','')}</p>
                        <div style="text-align:left; font-size:11px; margin-top:20px; line-height:1.4;">
                            <b>Ship To:</b><br>{inv.get('Clinic','')}<br>{inv.get('Doctor','')}<br>{inv.get('Address','')}<br>{inv.get('City','')}
                        </div>
                    </div>
                </div>
                <div style="margin-top: 45px; padding: 12px 0; border-top: 1.5px solid black; border-bottom: 1.5px solid black; font-size: 14px;">
                    <b>Patient:</b> {str(inv.get('Patient','')).upper()}
                </div>
                <div style="height: 380px; margin-top: 30px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead><tr style="border-bottom: 1px solid black;">
                            <th style="text-align:left; padding-bottom: 8px; font-size:12px; text-decoration:underline;">Description</th>
                            <th style="text-align:right; padding-bottom: 8px; font-size:12px; text-decoration:underline;">Amount</th>
                        </tr></thead>
                        <tbody><tr>
                            <td style="padding:25px 0; font-size: 14px;">Nightguard ({inv.get('Material','')}) {inv.get('Arch','')}</td>
                            <td style="text-align:right; font-size: 14px; font-weight:bold;">$180.00</td>
                        </tr></tbody>
                    </table>
                </div>
                <div style="border-top: 1.5px solid black; padding-top: 15px;">
                    <div style="display:flex; justify-content:space-between; font-size:13px; font-weight:bold;">
                        <div>Case: {inv.get('Case No','')}</div><div style="font-size:15px;">Total: $180.00</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("인쇄 (Print)", use_container_width=False):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

    # [수량 및 인센티브 현황판]
    st.markdown(f"""
    <div class="stat-card">
        <h4 style="margin-top:0; color:#4c6ef5;">📅 {this_month} 작업 현황</h4>
        <div style="display: flex; gap: 40px;">
            <div><p style="margin:0; font-size:12px; color:#aaa;">총 수량</p><p style="font-size:24px; font-weight:bold;">{total_count} / 320</p></div>
            <div><p style="margin:0; font-size:12px; color:#aaa;">초과 수량</p><p style="font-size:24px; font-weight:bold; color:#f03e3e;">{over_count} 개</p></div>
            <div><p style="margin:0; font-size:12px; color:#aaa;">추가 인센티브 (Pre-tax / Post-tax)</p>
                 <p style="font-size:24px; font-weight:bold; color:#37b24d;">${extra_pre_tax:,.1f} / <span style="font-size:18px;">${extra_post_tax:,.1f}</span></p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with tab3: st.write("🔍 검색 기능 구현 예정")
