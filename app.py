import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [디자인 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    /* 인보이스 전용 (종이 느낌) */
    .invoice-paper {
        background-color: white !important; color: black !important;
        width: 100%; max-width: 800px; padding: 50px; border: 2px solid black;
        margin: 20px auto; font-family: 'Arial', sans-serif;
    }
    .invoice-paper * { color: black !important; }
    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown { display: none !important; }
        .invoice-paper { display: block !important; border: none !important; margin: 0 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# [데이터 관리] 
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084

# 기준 데이터 (추후 확장 가능)
ref_data = pd.DataFrame([
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Arshpreet Kaur", "Region": "Courier", "Address": "13510 127 St NW", "City": "Edmonton, Alberta T5L 1B9", "Phone": "(780) 455-6806"},
    {"Clinic": "Calgary Central Dental", "Doctor": "Dr. Lana Huynh", "Region": "Local", "Address": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9", "Phone": "(403) 970-0600"}
])

# [비즈니스 데이 계산 함수]
def get_business_day(start_date, days_to_subtract):
    current_date = start_date
    while days_to_subtract > 0:
        current_date -= timedelta(days=1)
        if current_date.weekday() < 5: days_to_subtract -= 1
    return current_date

# [메인 헤더]
st.markdown('<div class="header-container"><div style="font-size: 24px; font-weight: 800;">🦷 Skycad Lab Night Guard Manager</div><div style="font-size: 12px;">Heechul Jung Edition</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록 및 일정", "📊 리스트 및 완료", "🔍 검색"])

with tab1:
    st.markdown("### 📋 기본 정보 및 일정 입력")
    c1, c2 = st.columns(2)
    
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: ET33")
        patient = st.text_input("Patient(환자명)")
        
        # 병원명 직접 입력 통합
        clinics = sorted(ref_data['Clinic'].tolist())
        sel_clinic = st.selectbox("Clinic(병원명)", ["선택하세요", "직접 입력"] + clinics)
        final_clinic = st.text_input("병원명 직접 입력") if sel_clinic == "직접 입력" else (sel_clinic if sel_clinic != "선택하세요" else "")
        
        # 의사명 직접 입력 통합
        auto_doc = ""
        if final_clinic in ref_data['Clinic'].values:
            auto_doc = ref_data[ref_data['Clinic'] == final_clinic]['Doctor'].iloc[0]
        
        doctors = sorted(ref_data['Doctor'].tolist())
        sel_doc = st.selectbox("Doctor(의사명)", ["선택하세요", "직접 입력"] + doctors, 
                               index=doctors.index(auto_doc)+2 if auto_doc in doctors else 0)
        final_doc = st.text_input("의사명 직접 입력") if sel_doc == "직접 입력" else (sel_doc if sel_doc != "선택하세요" else "")

    with c2:
        is_3d = st.checkbox("3D 디지털 스캔 접수", value=True)
        today = date.today()
        rec_date = today if is_3d else st.date_input("모델 접수일", today)
        
        mat = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arc = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)
        
        st.markdown("---")
        # 일정 관리 로직
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            due_date = st.date_input("요청일 (Due Date)", today + timedelta(days=7))
            lab_done_date = st.date_input("완료일 (Lab Done)", today + timedelta(days=6))
        with col_d2:
            # 출고일 자동 계산
            region = "Local"
            if final_clinic in ref_data['Clinic'].values:
                region = ref_data[ref_data['Clinic']==final_clinic]['Region'].iloc[0]
            ship_day_offset = 1 if region == "Local" else 2
            ship_date_calc = get_business_day(due_date, ship_day_offset)
            ship_date = st.date_input("출고일 (Shipping Date)", ship_date_calc)

    if st.button("💾 케이스 저장 및 초기화", use_container_width=True):
        if not case_no or not final_clinic:
            st.error("Case No와 Clinic은 필수입니다.")
        else:
            # 병원 정보 가져오기 (인보이스용)
            c_info = ref_data[ref_data['Clinic'] == final_clinic].iloc[0] if final_clinic in ref_data['Clinic'].values else {}
            
            new_case = {
                "Inv_No": st.session_state.inv_counter,
                "Case No": case_no, "Patient": patient, "Clinic": final_clinic, "Doctor": final_doc,
                "Address": c_info.get("Address", ""), "City": c_info.get("City", ""), "Phone": c_info.get("Phone", ""),
                "Material": mat, "Arch": arc, "Received": rec_date, "Due": due_date, 
                "Lab Done": lab_done_date, "Ship": ship_date, "Status": "Pending",
                "Inv_Date": today.strftime('%m/%d/%Y')
            }
            st.session_state.db.append(new_case)
            st.session_state.inv_counter += 1
            st.success("저장되었습니다!")
            st.rerun()

with tab2:
    st.subheader("📊 작업 리스트")
    for i, row in enumerate(st.session_state.db):
        c_info, c_btn = st.columns([5, 1])
        with c_info:
            status_icon = "🟡" if row.get('Status') == "Pending" else "🟢"
            st.write(f"{status_icon} **{row.get('Case No')}** | {row.get('Patient')} ({row.get('Clinic')})")
            st.caption(f"요청일: {row.get('Due')} | 완료일: {row.get('Lab Done')} | 출고일: {row.get('Ship')}")
        with c_btn:
            btn_label = "완료/인보이스" if row.get('Status') == "Pending" else "재출력"
            if st.button(btn_label, key=f"inv_btn_{i}"):
                st.session_state.db[i]['Status'] = "Completed"
                st.session_state.selected_invoice = st.session_state.db[i]
                st.rerun()

    # 인보이스 출력 영역
    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        if st.button("❌ 닫기"):
            st.session_state.selected_invoice = None
            st.rerun()
            
        st.markdown(f"""
        <div class="invoice-paper">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <span style="font-size:38px; font-weight:900; color:#1a4e8a;">skycad</span><br>
                    <span style="font-size:11px;">205-7136 11 St NE, Calgary, AB T2E 4Y9<br>(403) 970-0600</span>
                </div>
                <div style="text-align: right;">
                    <h1 style="margin:0;">INVOICE</h1>
                    <p>No. {inv.get('Inv_No')}<br>{inv.get('Inv_Date')}</p>
                </div>
            </div>
            <hr style="border:1px solid black;">
            <p><strong>Ship To:</strong> {inv.get('Clinic')}<br>{inv.get('Doctor')}<br>{inv.get('Address')}<br>{inv.get('City')}</p>
            <div style="padding: 10px 0; border-top: 2px solid black; border-bottom: 2px solid black; margin: 20px 0;">
                <strong>Patient:</strong> {str(inv.get('Patient')).upper()}
            </div>
            <table style="width:100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid black;">
                    <th style="text-align:left;">Description</th>
                    <th style="text-align:right;">Amount</th>
                </tr>
                <tr>
                    <td style="padding:20px 0;">Nightguard ({inv.get('Material')}) - {inv.get('Arch')}</td>
                    <td style="text-align:right;">$180.00</td>
                </tr>
            </table>
            <div style="margin-top:50px; text-align:right; font-weight:bold; font-size:1.2rem;">Total: $180.00</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ 인쇄 (Print PDF)"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3:
    st.write("🔍 검색 기능 구현 예정")
