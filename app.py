import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Manager", layout="wide")
st.title("🦷 Skycad Lab Manager")

# 2. 데이터 로드
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)

    # 컬럼 설정
    cols = ['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 
            'Material', 'Price', 'Qty', 'Total', 'Receipt Date', 
            'Completed Date', 'Shipping Date', 'Due Date', 
            'Status', 'Notes']
    for c in cols:
        if c not in main_df.columns:
            main_df[c] = 0 if c in ['Price', 'Qty', 'Total'] else ""
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    with st.expander("1️⃣ 기본 정보", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            case_no = st.text_input("Case # *", key="k1")
            patient = st.text_input("Patient *", key="k2")
        with c2:
            raw_cl = ref_df.iloc[:, 1].unique()
            cl_list = sorted([c for c in raw_cl if c and c != 'nan'])
            sel_cl = st.selectbox("Clinic *", ["선택"] + cl_list + ["➕직접"], key="k3")
            f_cl = st.text_input("직접입력", key="k4") if sel_cl == "➕직접" else sel_cl
        with c3:
            doc_list = ["선택", "➕직접"]
            if sel_cl not in ["선택", "➕직접"]:
                m_doc = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[:, 2].unique()
                doc_list += sorted([d for d in m_doc if d and d != 'nan'])
            sel_doc = st.selectbox("Doctor", doc_list, key="k5")
            f_doc = st.text_input("의사명", key="k6") if sel_doc == "➕직접" else sel_doc

    with st.expander("2️⃣ 상세 및 날짜 (자동연동)", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            arch = st.radio("Arch", ["Max", "Mand"], horizontal=True, key="k7")
            mat = st.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key="k8")
            qty = st.number_input("Qty", min_value=1, value=1, key="k9")
        with d2:
            is_3d = st.checkbox("3D 모델", value=True, key="k10")
            r_str = "-"
            if not is_3d:
                r_d = st.date_input("접수일", datetime.now(), key="k11")
                r_t = st.time_input("시간", datetime.now(), key="k12")
                r_str = f"{r_d} {r_t.strftime('%H:%M')}"
            comp_d = st.date_input("완료일", datetime.now()+timedelta(1), key="k13")
        with d3:
            # 알렉스 요청: 마감일 선택 -> 출고일 자동 2일 전
            due_d = st.date_input("마감일", datetime.now()+timedelta(7), key="k14")
            # 긴 줄을 여러 줄로 쪼갬 (잘림 방지)
            ship_val
