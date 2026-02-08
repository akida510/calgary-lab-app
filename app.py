import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [수정 금지] 디자인 및 테마 고정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 및 기본 스타일 */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
    }
    
    /* [핵심] 폰에서 짤림 방지: 가로 스크롤 허용 */
    .invoice-container {
        width: 100%;
        overflow-x: auto; /* 폰에서 양옆이 짤리면 손가락으로 밀어서 볼 수 있게 함 */
        background-color: #222;
        padding: 10px;
        display: block;
    }

    .invoice-paper {
        background-color: white !important;
        color: black !important;
        width: 794px !important;    /* A4/Letter 근사치 픽셀 고정 */
        min-height: 1056px;
        padding: 40px !important;
        margin: 0 auto;             /* 중앙 정렬 */
        box-sizing: border-box;
        box-shadow: 0 0 15px rgba(0,0,0,0.5);
    }

    /* 텍스트 줄바꿈 방지 및 색상 강제 */
    .invoice-paper * { 
        color: black !important; 
        border-color: black !important; 
        white-space: nowrap; 
    }

    @media print {
        @page { size: letter; margin: 0; }
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-container { background-color: white; padding: 0; overflow: visible; }
        .invoice-paper { width: 100% !important; box-shadow: none !important; margin: 0 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 데이터 로직 (사장님 원본) ---
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

# --- 메인 헤더 ---
st.markdown('<div style="background-color: #1a1c24; padding: 20px; border-radius: 10px; margin-bottom: 25px; border: 1px solid #30363d;">'
            '<div style="font-size: 24px; font-weight: 800;">實 Skycad Lab Night Guard Manager</div>'
            '<div style="font-size: 12px;">Designed By Heechul Jung</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료", "🔍 검색"])

# --- Tab 1: 케이스 등록 (희철님 원본 로직 100% 복구) ---
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
        ship_date = get_business_day(due_date, 1 if (sel_clinic != "선택" and ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0]=="Local") else 2)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("💾 케이스 저장 (접수 완료)"):
        if sel_clinic != "선택" and case_no:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Material": material, "Arch": arch,
                "Lab Done": lab_done_date, "Status": "Pending",
                "Addr": c_info['Addr'], "City": c_info['City'], "Phone": c_info['Phone']
            })
            st.success(f"{case_no}번 등록 완료!")

# --- Tab 2: 리스트 및 인보이스 ---
with tab2:
    for i, row in enumerate(st.session_state.db):
        c_info, c_btn = st.columns([4, 1.5])
        with c_info: st.write(f"**{row['Case No']}** | {row['Patient']} | {row['Clinic']}")
        with c_btn:
            if st.button("인보이스 보기", key=f"btn_{i}"):
                st.session_state.selected_invoice = row

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        # [핵심] 가로 스크롤 컨테이너 적용
        st.markdown(f"""
        <div class="invoice-container">
            <div class="invoice-paper">
                <div style="display: flex; justify-content: space-between;">
                    <div style="text-align: left;">
                        <div style="font-size: 10px; font-weight: bold; color: #1a4e8a !important;">DENTAL TECHNOLOGY Ltd</div>
                        <div style="font-size: 65px; font-weight: 900; font-style: italic; color: #1a4e8a !important; line-height: 0.8; letter-spacing: -3px;">skycad</div>
                        <div style="margin-top: 15px; font-size: 13px;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 32px; font-weight: bold; letter-spacing: 4px;">INVOICE</div>
                        <div style="font-size: 14px; font-weight: bold;">No. 162{inv['Case No'].replace('ET', '')}<br>{inv['Lab Done'].strftime('%m/%d/%Y')}</div>
                        <div style="margin-top: 20px; text-align: left; font-size: 13px; border: 1.5px solid black; padding: 12px; width: 230px; display: inline-block; white-space: normal;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>Dr. {inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}
                        </div>
                    </div>
                </div>
                <div style="margin: 50px 0 10px 0; font-size: 20px; border-bottom: 2.5px solid black; padding-bottom: 5px;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <tr style="border-bottom: 2px solid black; font-weight: bold;">
                        <td style="padding: 10px 0; text-decoration: underline;">Description</td>
                        <td style="padding: 10px 0; text-align: right; text-decoration: underline;">Amount</td>
                    </tr>
                    <tr>
                        <td style="padding: 30px 0; height: 350px; vertical-align: top; font-size: 16px;">Nightguard ({inv['Material']}) {inv['Arch'].upper()}</td>
                        <td style="padding: 30px 0; text-align: right; vertical-align: top; font-size: 16px;">$180.00</td>
                    </tr>
                </table>
                <div style="border-top: 2px solid black; padding-top: 15px; display: flex; justify-content: space-between; font-weight: bold; font-size: 20px;">
                    <span>{inv['Case No']}</span><span>Total: $180.00</span>
                </div>
                <div style="margin-top: 100px; text-align: center;">
                    <div style="font-size: 13px; font-weight: bold; text-decoration: underline; margin-bottom: 5px;">All dental products we offer are custom made in Canada.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ 인쇄하기"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3: st.write("🔍 검색 기능")
