import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. 페이지 설정 및 제작자 표기
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="wide")

st.markdown(
    """
    <div style="display: flex; align-items: baseline;">
        <h1 style="margin-right: 15px;">🦷 Skycad Lab Night Guard Manager</h1>
        <span style="font-size: 0.9rem; color: #888;">Designed by Heechul Jung</span>
    </div>
    """, 
    unsafe_allow_html=True
)

# 2. 데이터 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 💡 세션 상태 초기화 (날짜 연동의 핵심)
if "iter_count" not in st.session_state:
    st.session_state.iter_count = 0

# 마감일이 바뀔 때 출고일을 -2일로 자동 계산하는 콜백 함수
def update_shipping_date():
    # 위젯의 key인 'due_key' 값을 가져와서 'ship_key' 값을 업데이트
    st.session_state.ship_key = st.session_state.due_key - timedelta(days=2)

# 초기 로드 시 날짜 세션 값 설정
if 'due_key' not in st.session_state:
    st.session_state.due_key = datetime.now().date() + timedelta(days=7)
if 'ship_key' not in st.session_state:
    st.session_state.ship_key = st.session_state.due_key - timedelta(days=2)

def force_reset():
    st.session_state.iter_count += 1
    # 날짜 리셋
    st.session_state.due_key = datetime.now().date() + timedelta(days=7)
    st.session_state.ship_key = st.session_state.due_key - timedelta(days=2)
    st.cache_data.clear()
    st.rerun()

def get_full_data():
    try:
        df = conn.read(ttl=0)
        if df is None or df.empty:
            cols = ['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 'Material', 'Price', 'Qty', 'Total', 'Receipt Date', 'Receipt Time', 'Completed Date', 'Shipping Date', 'Due Date', 'Status', 'Notes']
            return pd.DataFrame(columns=cols)
        if 'Shipping Date' in df.columns:
            df['Shipping Date'] = df['Shipping Date'].astype(str).str.replace(' 00:00:00', '', regex=False).str.strip()
        return df
    except:
        return pd.DataFrame()

m_df = get_full_data()
ref_df = conn.read(worksheet="Reference", ttl=300).astype(str)

t1, t2, t3 = st.tabs(["📝 케이스 등록", "💰 이번 달 정산", "🔍 케이스 검색"])

# --- [TAB 1: 케이스 등록] ---
with t1:
    it = st.session_state.iter_count
    st.subheader("📋 새 케이스 정보 입력")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        case_no = st.text_input("Case # *", key=f"c_{it}")
        patient = st.text_input("Patient Name *", key=f"p_{it}")
    with c2:
        cl_list = sorted([c for c in ref_df.iloc[:, 1].unique() if c and str(c).lower() not in ['nan', 'clinic']])
        sel_cl = st.selectbox("Clinic *", ["선택"] + cl_list + ["➕ 직접"], key=f"cl_{it}")
        f_cl = st.text_input("클리닉명 입력", key=f"fcl_{it}") if sel_cl == "➕ 직접" else sel_cl
    with c3:
        doc_opts = ["선택", "➕ 직접"]
        if sel_cl not in ["선택", "➕ 직접"]:
            docs = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[:, 2].unique()
            doc_opts += sorted([d for d in docs if d and str(d).lower() != 'nan'])
        sel_doc = st.selectbox("Doctor", doc_opts, key=f"doc_{it}")
        f_doc = st.text_input("의사명 입력", key=f"fdoc_{it}") if sel_doc == "➕ 직접" else sel_doc

    with st.expander("⚙️ 작업 상세 및 날짜 연동", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            arch = st.radio("Arch", ["Max", "Mand"], horizontal=True, key=f"ar_{it}")
            mat = st.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key=f"mat_{it}")
            qty = st.number_input("Qty", min_value=1, value=1, key=f"q_{it}")
        with d2:
            is_3d = st.checkbox("3D 모델 기반 (스캔)", value=True, key=f"3d_{it}")
            rd = st.date_input("접수일", datetime.now(), key=f"rd_{it}", disabled=is_3d)
            rt = st.time_input("접수 시간", datetime.now(), key=f"rt_{it}", disabled=is_3d)
            comp_d = st.date_input("완료일", datetime.now() + timedelta(1), key=f"cd_{it}")
        with d3:
            # 💡 [핵심] 마감일을 바꾸면 on_change가 실행되어 출고일을 즉시 바꿈
            due_d = st.date_input("마감일 (Due Date)", key="due_key", on_change=update_shipping_date)
            # 💡 [핵심] 출고일 위젯은 세션의 ship_key 값을 추종함
            ship_d = st.date_input("출고일 (Shipping)", key="ship_key")
            stat = st.selectbox("Status", ["Normal", "Hold", "Canceled"], index=0, key=f"st_{it}")

    # 💡 누락되었던 체크리스트, 사진, 메모 기능 100% 유지
    with st.expander("✅ 체크리스트 / 📸 사진 / 📝 메모", expanded=True):
        chk_opts = sorted(list(set([str(i) for i in
