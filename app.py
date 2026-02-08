import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [수정 금지] 디자인 설정 및 테마 강제 고정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 1. 기본 테마 및 배경 */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    input:disabled { background-color: #262730 !important; color: #aaaaaa !important; }
    label p, .stMarkdown p, .stMetric p, .stTabs [data-baseweb="tab"] p { 
        color: #ffffff !important; font-weight: 600 !important; 
    }

    /* 2. 인보이스 외곽 컨테이너 (회색 배경) */
    .invoice-wrapper {
        width: 100%;
        display: flex;
        justify-content: center;
        background-color: #222;
        padding: 20px 0;
        overflow: hidden;
    }

    /* 3. [핵심] 레터지 비율 고정 및 가변 리사이징 */
    .invoice-paper {
        background-color: white !important;
        color: black !important;
        
        /* 북미 Letter지 8.5 x 11 비율 */
        aspect-ratio: 8.5 / 11;
        width: 95%;           /* 화면 너비의 95%까지 차지 */
        max-width: 816px;      /* 최대 크기는 실제 레터지 픽셀값 */
        
        padding: 5% !important; /* 내부 여백도 비율로 조정 */
        box-sizing: border-box;
        box-shadow: 0 0 20px rgba(0,0,0,0.5);
        display: flex;
        flex-direction: column;
        position: relative;
    }

    /* 4. 내부 텍스트 및 로고 강제 고정 (줄바꿈 방지) */
    .invoice-paper * { 
        color: black !important; 
        border-color: black !important;
        font-family: 'Arial', sans-serif;
    }
    
    .skycad-logo {
        font-size: clamp(30px, 8vw, 70px); /* 화면 크기에 따라 로고 크기 자동 조절 */
        font-weight: 900;
        font-style: italic;
        color: #1a4e8a !important;
        line-height: 0.8;
        letter-spacing: -2px;
    }

    .invoice-header-title {
        font-size: clamp(20px, 4vw, 40px);
        font-weight: bold;
        letter-spacing: 4px;
    }

    /* 인쇄 시에는 꽉 차게 */
    @media print {
        @page { size: letter; margin: 0; }
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-wrapper { background-color: white; padding: 0; }
        .invoice-paper { width: 100% !important; max-width: none !important; box-shadow: none !important; border: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 데이터 로직 ---
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

# --- 메인 화면 ---
st.markdown(f'<div class="header-container" style="display: flex; justify-content: space-between; align-items: center; background-color: #1a1c24; padding: 20px 30px; border-radius: 10px; margin-bottom: 25px; border: 1px solid #30363d;"><div style="font-size: 24px; font-weight: 800;">實 Skycad Lab Night Guard Manager</div><div style="font-size: 12px;">Designed By Heechul Jung</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료", "🔍 검색"])

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
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)
        lab_done_date = st.date_input("완료일 (Lab Done)", date.today())

    if st.button("💾 케이스 저장"):
        if sel_clinic != "선택" and case_no:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Material": material, "Arch": arch,
                "Lab Done": lab_done_date, "Status": "Pending",
                "Addr": c_info['Addr'], "City": c_info['City'], "Phone": c_info['Phone']
            })
            st.success("저장 완료!")

with tab2:
    for i, row in enumerate(st.session_state.db):
        col_txt, col_btn = st.columns([4, 1.5])
        with col_txt: st.write(f"**{row['Case No']}** | {row['Patient']} | {row['Clinic']}")
        with col_btn:
            if st.button("인보이스 보기", key=f"inv_{i}"):
                st.session_state.selected_invoice = row

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        st.markdown(f"""
        <div class="invoice-wrapper">
            <div class="invoice-paper">
                <div style="display: flex; justify-content: space-between; width: 100%;">
                    <div>
                        <div style="font-size: 10px; font-weight: bold; color: #1a4e8a !important;">DENTAL TECHNOLOGY Ltd</div>
                        <div class="skycad-logo">skycad</div>
                        <div style="margin-top: 10px; font-size: 12px; line-height: 1.2;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</div>
                    </div>
                    <div style="text-align: right;">
                        <div class="invoice-header-title">INVOICE</div>
                        <div style="font-size: 14px; font-weight: bold;">No. 162{inv['Case No'].replace('ET', '')}<br>{inv['Lab Done'].strftime('%m/%d/%Y')}</div>
                        <div style="margin-top: 15px; text-align: left; font-size: 12px; border: 1.5px solid black; padding: 10px; width: 200px; display: inline-block;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>Dr. {inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}
                        </div>
                    </div>
                </div>
                
                <div style="margin: 40px 0 10px 0; font-size: 18px; border-bottom: 2px solid black; padding-bottom: 5px; width: 100%;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <tr style="border-bottom: 1.5px solid black; font-weight: bold; font-size: 14px;">
                        <td style="padding: 10px 0;">Description</td>
                        <td style="padding: 10px 0; text-align: right;">Amount</td>
                    </tr>
                    <tr>
                        <td style="padding: 20px 0; height: 300px; vertical-align: top; font-size: 14px;">Nightguard ({inv['Material']}) {inv['Arch'].upper()}</td>
                        <td style="padding: 20px 0; text-align: right; vertical-align: top; font-size: 14px;">$180.00</td>
                    </tr>
                </table>
                
                <div style="border-top: 2px solid black; padding-top: 10px; display: flex; justify-content: space-between; font-weight: bold; font-size: 18px; width: 100%;">
                    <span>{inv['Case No']}</span><span>Total: $180.00</span>
                </div>
                
                <div style="margin-top: auto; text-align: center; width: 100%;">
                    <div style="font-size: 12px; font-weight: bold; text-decoration: underline; margin-bottom: 5px;">All dental products we offer are custom made in Canada.</div>
                    <div style="font-size: 8px; line-height: 1.2; color: #666 !important;">
                        Please ensure your monthly payment is made within 30 days of receiving your statement.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ 인쇄하기"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
