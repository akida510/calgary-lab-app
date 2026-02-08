import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# 1. 페이지 설정 (레이아웃 고정)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

# 2. CSS: 폰에서 "절대 안 잘리는" 가변 너비 설정
st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    /* 인보이스 컨테이너: 여백 제거 */
    .invoice-container {
        width: 100%;
        display: flex;
        justify-content: center;
        background-color: #222;
        padding: 5px 0;
    }

    /* [핵심] 폰 너비에 따라 종이 크기가 100% 변하는 설정 */
    .invoice-paper {
        background-color: white !important;
        color: black !important;
        width: 98%;            /* 폰 화면 좌우 꽉 차게 */
        max-width: 800px;      /* PC에서는 이 크기 이상 안 커짐 */
        aspect-ratio: 8.5 / 11; /* 레터지 비율 유지 */
        padding: 4% !important; /* 패딩도 비율로 설정 */
        box-sizing: border-box;
        box-shadow: 0 0 15px rgba(0,0,0,0.5);
        display: flex;
        flex-direction: column;
    }

    /* 텍스트가 종이 밖으로 나가지 않게 조절 */
    .invoice-paper div, .invoice-paper td, .invoice-paper span {
        color: black !important;
        word-break: keep-all;
    }
    
    .skycad-logo-text {
        font-size: clamp(30px, 12vw, 65px); /* 화면 크기에 따라 로고 크기 자동 조절 */
        font-weight: 900;
        font-style: italic;
        color: #1a4e8a !important;
        line-height: 0.8;
        letter-spacing: -2px;
    }

    @media print {
        @page { size: letter; margin: 0; }
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-container { background-color: white; padding: 0; }
        .invoice-paper { width: 100% !important; max-width: none !important; box-shadow: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로직 (원본 유지)
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Addr": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9", "Phone": "(403) 970-0600"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier", "Addr": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9", "Phone": "(780) 455-6806"},
])

def get_business_day(start_date, days_to_subtract):
    current_date = start_date
    while days_to_subtract > 0:
        current_date -= timedelta(days=1)
        if current_date.weekday() < 5: days_to_subtract -= 1
    return current_date

# 4. 상단 헤더
st.markdown('<div class="header-container" style="background-color: #1a1c24; padding: 20px; border-radius: 10px; margin-bottom: 25px; border: 1px solid #30363d;">'
            '<div style="font-size: 24px; font-weight: 800;">實 Skycad Lab Night Guard Manager</div>'
            '<div style="font-size: 12px;">Designed By Heechul Jung</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료", "🔍 검색"])

# --- Tab 1: 등록 (원본 100% 유지) ---
with tab1:
    st.markdown("### 📋 기본정보입력")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: ET33")
        patient = st.text_input("Patient(환자명)", placeholder="환자 성함")
        clinics = sorted(list(set(ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic(병원명)", ["선택"] + clinics)
        docs = ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "선택" else []
        sel_doctor = st.selectbox("Doctor(의사명)", ["선택"] + docs)
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        rec_date = today if is_3d else st.date_input("접수일", today)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)
    
    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("요청일 (Due Date)", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("완료일 (Lab Done)", today + timedelta(days=1))
    with col4:
        ship_days = 1 if (sel_clinic != "선택" and ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0]=="Local") else 2
        ship_date = get_business_day(due_date, ship_days)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("💾 케이스 저장"):
        if sel_clinic != "선택" and case_no:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, "Doctor": sel_doctor, 
                "Material": material, "Arch": arch, "Lab Done": lab_done_date, "Status": "Pending",
                "Addr": c_info['Addr'], "City": c_info['City'], "Phone": c_info['Phone']
            })
            st.success("등록 완료!")

# --- Tab 2: 리스트 & 인보이스 (완료/취소 기능 복구) ---
with tab2:
    for i, row in enumerate(st.session_state.db):
        c_info, c_btn1, c_btn2 = st.columns([3, 1.5, 1])
        with c_info:
            st.write(f"{'🟡' if row['Status']=='Pending' else '🟢'} **{row['Case No']}** | {row['Patient']}")
        with c_btn1:
            if st.button("완료/인보이스", key=f"inv_{i}"):
                st.session_state.db[i]['Status'] = "Completed"
                st.session_state.selected_invoice = st.session_state.db[i]
                st.rerun()
        with c_btn2:
            if row['Status'] == "Completed":
                if st.button("취소", key=f"undo_{i}"):
                    st.session_state.db[i]['Status'] = "Pending"
                    st.session_state.selected_invoice = None
                    st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        st.markdown(f"""
        <div class="invoice-container">
            <div class="invoice-paper">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <div style="font-size: 8px; font-weight: bold; color: #1a4e8a !important;">DENTAL TECHNOLOGY Ltd</div>
                        <div class="skycad-logo-text">skycad</div>
                        <div style="font-size: 11px; margin-top: 5px;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: clamp(20px, 6vw, 32px); font-weight: bold;">INVOICE</div>
                        <div style="font-size: 12px; font-weight: bold;">No. 162{inv['Case No'].replace('ET', '')}<br>{inv['Lab Done'].strftime('%m/%d/%Y')}</div>
                        <div style="margin-top: 10px; text-align: left; font-size: 11px; border: 1.5px solid black; padding: 8px; width: 180px; display: inline-block;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>Dr. {inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}
                        </div>
                    </div>
                </div>
                <div style="margin: 25px 0 10px 0; font-size: 16px; border-bottom: 2px solid black; padding-bottom: 5px;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <tr style="border-bottom: 1.5px solid black; font-weight: bold; font-size: 12px;">
                        <td style="padding: 5px 0;">Description</td>
                        <td style="padding: 5px 0; text-align: right;">Amount</td>
                    </tr>
                    <tr>
                        <td style="padding: 15px 0; height: 200px; vertical-align: top; font-size: 13px;">Nightguard ({inv['Material']}) {inv['Arch'].upper()}</td>
                        <td style="padding: 15px 0; text-align: right; vertical-align: top; font-size: 13px;">$180.00</td>
                    </tr>
                </table>
                <div style="border-top: 2px solid black; padding-top: 10px; display: flex; justify-content: space-between; font-weight: bold; font-size: 15px;">
                    <span>{inv['Case No']}</span><span>Total: $180.00</span>
                </div>
                <div style="margin-top: auto; text-align: center; padding-bottom: 10px;">
                    <div style="font-size: 10px; font-weight: bold; text-decoration: underline;">All dental products we offer are custom made in Canada.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ 인쇄하기"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3: st.write("🔍 검색 기능")
