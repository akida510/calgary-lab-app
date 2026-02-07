import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 기본 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

# 현재 월 및 단가 설정
now = datetime.now()
current_month_name = now.strftime('%m월')
PRE_TAX_UNIT = 30.0
POST_TAX_UNIT = 19.505333

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; }
    .metric-card {
        background: linear-gradient(135deg, #1e2130 0%, #11141d 100%);
        padding: 25px; border-radius: 15px; border: 1px solid #3498db;
        text-align: center; margin-bottom: 25px;
    }
    .metric-title { font-size: 1.1rem; color: #94a3b8; margin-bottom: 8px; }
    .metric-value { font-size: 2.2rem; font-weight: bold; color: #ffffff; margin-bottom: 5px; }
    .metric-delta { font-size: 1.3rem; color: #ef4444; font-weight: bold; margin-bottom: 15px; }
    .money-grid { display: flex; justify-content: center; gap: 20px; border-top: 1px solid #334155; padding-top: 15px; }
    .money-item { text-align: center; }
    .money-label { font-size: 0.8rem; color: #94a3b8; }
    .money-amount { font-size: 1.2rem; font-weight: bold; color: #10b981; }
    
    .invoice-overlay { background-color: rgba(0,0,0,0.85); padding: 30px; border-radius: 10px; border: 1px solid #444; }
    .invoice-paper {
        background-color: #ffffff !important; width: 100%; max-width: 800px; 
        aspect-ratio: 8.5 / 11; padding: 50px; border: 1px solid #000; margin: 0 auto;
    }
    .invoice-paper * { color: #000000 !important; -webkit-text-fill-color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 초기화]
if 'db' not in st.session_state: st.session_state.db = []
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084
if 'active_invoice' not in st.session_state: st.session_state.active_invoice = None

# [3. 메인 로직 - 탭 구성]
tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 실적 및 리스트", "🔍 검색"])

with tab1:
    # (등록 화면 코드는 이전 버전과 동일)
    st.markdown("### 📋 케이스 등록")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)")
        patient = st.text_input("Patient(환자명)")
        st.selectbox("Clinic(병원명)", ["선택", "My Smile Family Dental", "Calgary Central Dental"], key="ck")
        st.selectbox("Doctor(의사명)", ["선택", "Dr. Amhipreat Kaur", "Dr. Lana Huynh"], key="dk")
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        f_rec_date = "-" if is_3d else st.date_input("접수일", value=date.today())
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    if st.button("💾 케이스 저장"):
        if st.session_state.ck != "선택" and case_no:
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter, "Case No": case_no, "Patient": patient, 
                "Clinic": st.session_state.ck, "Status": "진행중", "Date": f_rec_date
            })
            st.session_state.inv_counter += 1
            st.rerun()

with tab2:
    # [수정 핵심] 정산 및 금액 표시 섹션
    total_count = len(st.session_state.db)
    target = 320
    remaining = total_count - target
    
    # 금액 계산 (현재까지 작업한 모든 수량 기준)
    total_pre_tax = total_count * PRE_TAX_UNIT
    total_post_tax = total_count * POST_TAX_UNIT

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">📅 {current_month_name} 작업 현황 및 정산</div>
        <div class="metric-value">{total_count} / {target}개</div>
        <div class="metric-delta">({remaining:+}개)</div>
        <div class="money-grid">
            <div class="money-item">
                <div class="money-label">세전 총액 (Pre-tax)</div>
                <div class="money-amount">${total_pre_tax:,.2f}</div>
            </div>
            <div style="border-left: 1px solid #334155; height: 40px; margin-top: 5px;"></div>
            <div class="money-item">
                <div class="money-label">세후 총액 (After-tax)</div>
                <div class="money-amount" style="color: #3498db;">${total_post_tax:,.2f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 리스트 출력
    st.markdown("### 📋 작업 리스트")
    if not st.session_state.db:
        st.info("데이터가 없습니다.")
    else:
        for i, row in enumerate(st.session_state.db):
            l_col, b_col1, b_col2 = st.columns([3, 1, 1])
            with l_col: st.write(f"{'🟢' if row['Status'] == '완료' else '🟡'} **{row['Case No']}** | {row['Patient']}")
            with b_col1:
                if st.button("완료/복구", key=f"d_{i}"):
                    st.session_state.db[i]['Status'] = "완료" if row['Status']=="진행중" else "진행중"
                    st.rerun()
            with b_col2:
                if st.button("🔍 인보이스", key=f"v_{i}"):
                    st.session_state.active_invoice = row

    # 인보이스 미리보기 팝업 (열려있을 때만 표시)
    if st.session_state.active_invoice:
        st.markdown('---')
        if st.button("❌ 미리보기 닫기"):
            st.session_state.active_invoice = None
            st.rerun()
        
        inv = st.session_state.active_invoice
        st.markdown('<div class="invoice-overlay">', unsafe_allow_html=True)
        # 인보이스 상세 HTML 생략 (동일 유지)
        st.markdown(f'<div class="invoice-paper"><h3>Invoice No. {inv["Inv_No"]}</h3><p>Patient: {inv["Patient"]}</p></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
