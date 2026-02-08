import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [수정 금지] 디자인 설정 및 테마 강제 고정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 고정 */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    input:disabled { background-color: #262730 !important; color: #aaaaaa !important; }

    /* 리스트 가독성 (요청하신 세부 내용 포함) */
    .case-row {
        background-color: #1a1c24; padding: 12px; border-radius: 8px;
        border-left: 6px solid #4c6ef5; margin-bottom: 8px;
    }

    /* [핵심] 폰에서 레터지 모양 그대로 보이게 하는 마법의 코드 */
    .invoice-viewport {
        width: 100%;
        overflow-x: auto; /* 폰에서 안 잘리게 스크롤 혹은 축소 허용 */
        background-color: #222;
        padding: 10px 0;
        display: flex; justify-content: center;
    }

    .invoice-paper {
        background-color: white !important;
        color: black !important;
        width: 816px !important;   /* 북미 Letter 가로 8.5in */
        height: 1056px !important;  /* 북미 Letter 세로 11in */
        padding: 40px !important;
        box-sizing: border-box !important;
        position: relative !important;
        flex-shrink: 0; /* 너비 유지 */
        box-shadow: 0 0 20px rgba(0,0,0,0.5);
    }

    /* 폰 화면이 816px보다 작으면 종이 전체를 비율에 맞춰 축소 */
    @media screen and (max-width: 816px) {
        .invoice-viewport { padding: 0; overflow: hidden; }
        .invoice-paper {
            transform: scale(calc(100vw / 850)); 
            transform-origin: top center;
            margin-bottom: calc(-1056px * (1 - (100vw / 850)));
        }
    }

    .invoice-paper * { color: black !important; border-color: black !important; white-space: nowrap; }

    @media print {
        @page { size: letter; margin: 0; }
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-viewport { background-color: white; padding: 0; }
        .invoice-paper { transform: none !important; box-shadow: none !important; margin: 0 !important; width: 100% !important; }
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

# --- 메인 화면 ---
st.title("實 Skycad Lab Night Guard")
tab1, tab2 = st.tabs(["📝 등록", "📊 리스트"])

with tab1:
    # (희철님 원본 등록 로직 그대로 유지)
    st.markdown("### 📋 기본정보입력")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No", placeholder="예: ET33")
        patient = st.text_input("Patient", placeholder="환자명")
        sel_clinic = st.selectbox("Clinic", ["선택"] + sorted(ref_data['Clinic'].tolist()))
        docs = ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "선택" else []
        sel_doctor = st.selectbox("Doctor", ["선택"] + docs)
    with c2:
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)
        due_date = st.date_input("Due Date", date.today() + timedelta(days=7))

    if st.button("💾 케이스 저장"):
        if sel_clinic != "선택" and case_no:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, "Doctor": sel_doctor,
                "Material": material, "Arch": arch, "Due": due_date, "Status": "Pending",
                "Addr": c_info['Addr'], "City": c_info['City'], "Phone": c_info['Phone'], "Done": date.today()
            })
            st.success("저장 완료!")

with tab2:
    # 리스트 세부 내용 보강
    for i, row in enumerate(st.session_state.db):
        col_text, col_btn = st.columns([4, 1.2])
        with col_text:
            status = "🟡 [대기]" if row['Status'] == "Pending" else "🟢 [완료]"
            st.markdown(f"""<div class="case-row">
                <b>{status} {row['Case No']} | {row['Patient']}</b><br>
                <small>{row['Clinic']} | {row['Material']} | <b>Due: {row['Due']}</b></small>
            </div>""", unsafe_allow_html=True)
        with col_btn:
            if st.button("출력", key=f"p_{i}"):
                st.session_state.db[i]['Status'] = "Completed"
                st.session_state.selected_invoice = st.session_state.db[i]
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        # [수정] 폰에서도 강제로 816px 레터지 비율 유지
        st.markdown(f"""
        <div class="invoice-viewport">
            <div class="invoice-paper">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <div style="font-size: 11px; font-weight: bold; color: #1a4e8a;">DENTAL TECHNOLOGY Ltd</div>
                        <div style="font-size: 70px; font-weight: 900; font-style: italic; color: #1a4e8a; line-height: 0.8; letter-spacing: -4px;">skycad</div>
                        <div style="margin-top: 20px; font-size: 14px;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 40px; font-weight: bold; letter-spacing: 5px;">INVOICE</div>
                        <div style="font-size: 16px; font-weight: bold;">No. 162{inv['Case No'].replace('ET', '')}<br>{inv['Done'].strftime('%m/%d/%Y')}</div>
                        <div style="margin-top: 30px; text-align: left; font-size: 14px; border: 1.5px solid black; padding: 15px; width: 250px; display: inline-block; white-space: normal;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>Dr. {inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}<br>{inv['Phone']}
                        </div>
                    </div>
                </div>
                <div style="margin: 60px 0 10px 0; font-size: 20px; border-bottom: 2.5px solid black; padding-bottom: 5px;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <tr style="border-bottom: 2px solid black; font-weight: bold; font-size: 16px;">
                        <td style="padding: 12px 0; text-decoration: underline;">Description</td>
                        <td style="padding: 12px 0; text-align: right; text-decoration: underline;">Amount</td>
                    </tr>
                    <tr>
                        <td style="padding: 30px 0; height: 400px; vertical-align: top; font-size: 18px;">Nightguard ({inv['Material']}) {inv['Arch'].upper()}</td>
                        <td style="padding: 30px 0; text-align: right; vertical-align: top; font-size: 18px;">$180.00</td>
                    </tr>
                </table>
                <div style="border-top: 2px solid black; padding-top: 15px; display: flex; justify-content: space-between; font-weight: bold; font-size: 22px;">
                    <span>{inv['Case No']}</span><span>Total: $180.00</span>
                </div>
                <div style="position: absolute; bottom: 40px; left: 40px; right: 40px; text-align: center;">
                    <div style="font-size: 14px; font-weight: bold; text-decoration: underline; margin-bottom: 10px;">All dental products we offer are custom made in Canada.</div>
                    <div style="font-size: 9px; line-height: 1.4; color: #444;">
                        Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ 인쇄 실행"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
