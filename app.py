import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Manager", layout="wide")
st.title("🦷 Skycad Lab Manager")

# 2. 데이터 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)

    # 필수 컬럼 보정
    cols = ['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 
            'Material', 'Price', 'Qty', 'Total', 'Receipt Date', 
            'Completed Date', 'Shipping Date', 'Due Date', 'Status', 'Notes']
    for c in cols:
        if c not in main_df.columns:
            main_df[c] = 0 if c in ['Price', 'Qty', 'Total'] else ""
    
    if not main_df.empty:
        main_df['Shipping Date'] = pd.to_datetime(main_df['Shipping Date'], errors='coerce')
except Exception as e:
    st.error(f"연결 오류: {e}")
    st.stop()

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("새 케이스 등록")
    with st.expander("1️⃣ 기본 정보", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            case_no = st.text_input("Case # *", key="v_case")
            patient = st.text_input("Patient *", key="v_p")
        with c2:
            cl_list = sorted([c for c in ref_df.iloc[:, 1].unique() if c and c.lower() not in ['nan', 'clinic']])
            sel_cl = st.selectbox("Clinic *", ["선택"] + cl_list + ["➕ 직접"], key="v_cl")
            f_cl = st.text_input("클리닉명", key="v_cl_d") if sel_cl == "➕ 직접" else sel_cl
        with c3:
            doc_list = ["선택", "➕ 직접"]
            if sel_cl not in ["선택", "➕ 직접"]:
                matched = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[:, 2].unique()
                doc_list += sorted([d for d in matched if d and d.lower() not in ['nan']])
            sel_doc = st.selectbox("Doctor", doc_list, key="v_doc")
            f_doc = st.text_input("의사명", key="v_doc_d") if sel_doc == "➕ 직접" else sel_doc

    with st.expander("2️⃣ 상세 및 날짜", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            arch = st.radio("Arch", ["Max", "Mand"], horizontal=True, key="v_arch")
            mat = st.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key="v_mat")
            qty = st.number_input("Qty", min_value=1, value=1, key="v_qty")
        with d2:
            is_3d = st.checkbox("3D 모델", value=True, key="v_3d")
            r_str = "-"
            if is_3d == False:
                r_d = st.date_input("접수일", datetime.now(), key="v_rd")
                r_t = st.time_input("시간", datetime.now(), key="v_rt")
                r_str = f"{r_d} {r_t.strftime('%H:%M')}"
            c_d = st.date_input("완료일", datetime.now()+timedelta(days=1), key="v_cd")
        with d3:
            due_d = st.date_input("마감일", datetime.now()+timedelta(days=7), key="v_due")
            # 마감일에서 2일 자동 차감
            ship_d = st.date_input("출고일", due_d - timedelta(days=2), key="v_sd
