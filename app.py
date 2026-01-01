import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad", layout="wide")
st.title("🦷 Skycad Lab Manager")

# 2. 데이터 연결 및 로드
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    r_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    r_df = r_df.apply(lambda x: x.str.strip())
    m_df = conn.read(ttl=0)

    # 필수 컬럼 설정
    cols = ['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 
            'Material', 'Price', 'Qty', 'Total', 'Receipt Date', 
            'Completed Date', 'Shipping Date', 'Due Date', 
            'Status', 'Notes']
    for c in cols:
        if c not in m_df.columns:
            m_df[c] = 0 if c in ['Price', 'Qty', 'Total'] else ""
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

# 3. 저장 후 초기화 함수 (모든 키 삭제)
def reset_form_state():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("새 케이스 등록")
    
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            case_no = st.text_input("Case # *", key="in_case")
            patient = st.text_input("Patient *", key="in_p")
        with c2:
            raw_c = r_df.iloc[:, 1].unique()
            c_list = sorted([c for c in raw_c if c and c != 'nan' and c != 'Clinic'])
            sel_cl = st.selectbox("Clinic *", ["선택"] + c_list + ["➕직접"], key="in_cl")
            f_cl = st.text_input("클리닉명 입력", key="in_cl_d") if sel_cl == "➕직접" else sel_cl
        with c3:
            doc_opts = ["선택", "➕직접"]
            if sel_cl not in ["선택", "➕직접"]:
                m_doc = r_df[r_df.iloc[:, 1] == sel_cl].iloc[:, 2].unique()
                doc_opts += sorted([d for d in m_doc if d and d != 'nan'])
            sel_doc = st.selectbox("Doctor", doc_opts, key="in_doc")
            f_doc = st.text_input("의사명 입력", key="in_doc_d") if sel_doc == "➕직접" else sel_doc

    with st.expander(" 작업 상세 및 날짜 연동", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            arch = st.radio("Arch", ["Max", "Mand"], horizontal=True, key="in_arch")
            mat = st.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key="in_mat")
            qty = st.number_input("Qty", min_value=1, value=1, key="in_qty")
        with d2:
            is_3d = st.checkbox("3D 모델", value=True, key="in_3d")
            r_str = "-"
            if not is_3d:
                rd = st.date_input("접수일", datetime.now(), key="in_rd")
                rt = st.time_input("시간", datetime.now(), key="in_rt")
                r_str = f"{rd} {rt.strftime('%H:%M')}"
            comp_d = st.date_input("완료일", datetime.now()+timedelta(1), key="in_cd")
        with d3:
            # 💡 [핵심] 날짜 연동 로직
            due_val = st.date_input("마감일(Due Date)", 
                                    value=datetime.now() + timedelta(days=7), 
                                    key="due_input")
            
            # 동적 키(f"in_sd_{due_val}")를 사용하여 마감일 변경 시 즉시 -2일 반영
            ship_date = st.date_input("출고일(Ship Date)", 
                                     value=due_val - timedelta(days=2), 
                                     key=f"in_sd_{due_val}")
            
            stat = st.selectbox("Status", ["Normal", "Hold", "Canceled"], key="in_stat")

    with st.expander(" 체크리스트 & 사진 & 메모"):
        opts = sorted(list(set([i for i in r_df.iloc[:, 3:].values.flatten() if i and i != 'nan'])))
        chks = st.multiselect("체크리스트", opts, key="in_chk")
        img = st.file_uploader("📸 사진 업로드", type=['jpg','png'], key="in_img")
        memo = st.text_input("추가 메모", key="in_memo")

    # 단가 계산
    p_u = 180
    if sel_cl not in ["선택", "➕직접"]:
        try:
            p_v = r_df[r_df.iloc[:, 1] == sel_cl].iloc[0, 3]
            p_u = int(float(p_v))
        except: p_u = 180
    st.info(f"💰 현재 단가: ${p_u} | 합계: ${p_u * qty}")

    if st.button("🚀 최종 저장", use_container_width=True):
        if not
