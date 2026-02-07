import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [페이지 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    /* 제목 디자인 */
    .main-title {
        font-size: 50px !important; font-weight: 900 !important; color: #4c6ef5 !important;
        margin-bottom: 0px; letter-spacing: -2px;
    }
    .sub-title { font-size: 16px; color: #888; margin-bottom: 40px; font-weight: 500; }

    /* 버튼 스타일 (슬림 & 세련) */
    .stButton>button {
        width: auto !important; min-width: 140px; padding: 8px 25px !important;
        background-color: #3b5bdb !important; color: white !important;
        border-radius: 6px !important; border: none !important; font-weight: 600 !important;
        transition: 0.2s;
    }
    .stButton>button:hover { background-color: #4c6ef5 !important; transform: translateY(-1px); }

    /* 리스트 카드 */
    .case-card {
        background-color: #1a1c24; padding: 20px; border-radius: 12px;
        border: 1px solid #30363d; margin-bottom: 15px; display: flex; 
        justify-content: space-between; align-items: center;
    }

    /* 인보이스 깨짐 방지 레이아웃 (핵심 수정부) */
    .invoice-paper {
        background-color: white !important; color: black !important;
        padding: 60px; font-family: 'Arial', sans-serif;
        width: 210mm; min-height: 297mm; margin: 0 auto; box-shadow: 0 0 20px rgba(0,0,0,0.5);
    }
    .invoice-paper * { color: black !important; }
    
    /* 설명칸 강제 높이 확보 */
    .description-box {
        border-top: 2px solid black; border-bottom: 2px solid black;
        margin: 20px 0; min-height: 450px; /* 여기서 높이 강제 고정 */
        display: flex; flex-direction: column;
    }
    .desc-header { border-bottom: 1px solid black; display: flex; font-weight: bold; padding: 10px 0; }
    .desc-content { display: flex; flex-grow: 1; padding: 20px 0; font-size: 18px; }

    @media print {
        .no-print, .stButton, .main-title, .sub-title, .stTabs, [data-testid="stSidebar"] { display: none !important; }
        .invoice-paper { display: block !important; border: none !important; padding: 0 !important; width: 100% !important; box-shadow: none !important; }
        .description-box { min-height: 550px !important; } /* 인쇄 시 높이 더 확보 */
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [데이터 관리]
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'view_mode' not in st.session_state: st.session_state.view_mode = "list"
if 'target_inv' not in st.session_state: st.session_state.target_inv = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Addr": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier", "Addr": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9"},
])

def get_business_day(start_date, days_to_subtract):
    current_date = start_date
    while days_to_subtract > 0:
        current_date -= timedelta(days=1)
        if current_date.weekday() < 5: days_to_subtract -= 1
    return current_date

# 타이틀 디자인
st.markdown('<div class="main-title">🦷 Skycad Lab Manager</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Designed by Heechul Jung V1.0.4</div>', unsafe_allow_html=True)

# 인보이스 보기 모드가 아닐 때만 탭 표시
if st.session_state.view_mode == "list":
    tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 작업 리스트", "🔍 검색"])

    with tab1:
        st.markdown("### 📋 기본정보입력")
        c1, c2 = st.columns(2)
        with c1:
            case_no = st.text_input("Case No(팬번호)", placeholder="예: ET33")
            patient = st.text_input("Patient(환자명)")
            clinics = sorted(list(set(ref_data['Clinic'].tolist())))
            sel_clinic = st.selectbox("Clinic(병원명)", ["선택"] + clinics)
        with c2:
            filtered_docs = ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "선택" else []
            sel_doctor = st.selectbox("Doctor(의사명)", ["선택"] + filtered_docs)
            material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
            arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

        st.markdown("### 📅 일정 관리")
        col3, col4, col5 = st.columns(3)
        today = date.today()
        with col5: due_date = st.date_input("Due Date", today + timedelta(days=7))
        with col3: lab_done_date = st.date_input("Lab Done", today + timedelta(days=1))
        with col4:
            ship_date = get_business_day(due_date, 1 if (sel_clinic != "선택" and ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0]=="Local") else 2)
            st.date_input("Shipping Date", ship_date)

        if st.button("💾 케이스 저장"):
            if sel_clinic == "선택" or not case_no: st.error("필수 항목을 확인하세요.")
            else:
                c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
                st.session_state.db.append({
                    "id": len(st.session_state.db),
                    "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                    "Doctor": sel_doctor, "Material": material, "Arch": arch,
                    "Due": due_date, "Lab Done": lab_done_date, "Status": "Pending",
                    "Addr": c_info['Addr'], "City": c_info['City']
                })
                st.success("등록 완료!")

    with tab2:
        for i, row in enumerate(st.session_state.db):
            st.markdown(f"""<div class="case-card">
                <div><b>{row['Case No']}</b> | {row['Patient']} | {row['Clinic']}</div>
                <div style="color:{'#fcc419' if row['Status']=='Pending' else '#40c057'}">{row['Status']}</div>
            </div>""", unsafe_allow_html=True)
            
            bc1, bc2 = st.columns([1, 1])
            with bc1:
                # 버튼 명칭 변경 및 기능 통합
                if st.button(f"📄 완료/인보이스 출력", key=f"print_{i}"):
                    st.session_state.db[i]['Status'] = "Completed"
                    st.session_state.target_inv = st.session_state.db[i]
                    st.session_state.view_mode = "invoice"
                    st.rerun()
            with bc2:
                if row['Status'] == "Completed":
                    if st.button(f"🔄 완료 취소", key=f"undo_{i}"):
                        st.session_state.db[i]['Status'] = "Pending"
                        st.rerun()

# --- 인보이스 출력 화면 ---
else:
    inv = st.session_state.target_inv
    st.markdown('<div class="no-print">', unsafe_allow_html=True)
    if st.button("⬅️ 리스트로 돌아가기"):
        st.session_state.view_mode = "list"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 실제 인보이스 종이 레이아웃
    st.markdown(f"""
    <div class="invoice-paper">
        <div style="display:flex; justify-content:space-between;">
            <div>
                <span style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                <span style="font-size:65px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-4px; line-height:0.8;">skycad</span><br>
                <div style="margin-top:20px; font-size:13px;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</div>
            </div>
            <div style="text-align:right;">
                <h1 style="font-size:50px; margin:0; font-weight:400; letter-spacing:8px;">INVOICE</h1>
                <p style="font-size:16px; margin:5px 0;">No. {inv['Case No'].replace('ET','')}<br>{inv['Lab Done'].strftime('%d/%m/%Y')}</p>
                <div style="text-align:left; border:1.5px solid #000; padding:15px; width:240px; margin-top:15px; font-size:14px; display:inline-block;">
                    <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}
                </div>
            </div>
        </div>

        <div style="margin: 50px 0 20px 0; font-size:22px;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>

        <div class="description-box">
            <div class="desc-header">
                <div style="flex:4;">Description</div>
                <div style="flex:1; text-align:right;">Amount</div>
            </div>
            <div class="desc-content">
                <div style="flex:4;">Nightguard ({inv['Material']}) - {inv['Arch']}</div>
                <div style="flex:1; text-align:right;">$180.00</div>
            </div>
        </div>

        <div style="display:flex; justify-content:space-between; font-size:22px; font-weight:bold; margin-bottom:60px;">
            <div>{inv['Case No']}</div>
            <div>Total: $180.00</div>
        </div>

        <div style="text-align:center;">
            <div style="font-size:19px; font-weight:bold; text-decoration:underline; margin-bottom:25px;">All dental products we offer are custom made in Canada.</div>
            <p style="font-size:12px; line-height:1.8; padding:0 40px; color:#333 !important;">Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.</p>
        </div>
        
        <div style="margin-top:80px; border-top:1.5px solid black; width:240px; padding-top:10px; font-size:14px;">Authorized Signature</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="no-print" style="text-align:center; margin-top:30px;">', unsafe_allow_html=True)
    if st.button("🖨️ 인쇄하기 (Print)"):
        st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab3 if st.session_state.view_mode == "list" else st.empty(): st.write("검색 기능")
