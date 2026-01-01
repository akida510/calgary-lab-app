import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.title("🦷 Skycad Lab Manager")

# 2. 데이터 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)

    # 필수 컬럼 체크
    cols = ['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 'Material', 'Price', 'Qty', 'Total', 'Receipt Date', 'Completed Date', 'Shipping Date', 'Due Date', 'Status', 'Notes']
    for c in cols:
        if c not in main_df.columns:
            main_df[c] = 0 if c in ['Price', 'Qty', 'Total'] else ""
    
    if not main_df.empty:
        main_df['Shipping Date'] = pd.to_datetime(main_df['Shipping Date'], errors='coerce')
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    with st.expander("1️⃣ 기본 정보 (필수)", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            case_no = st.text_input("Case # *", key="v_case")
            patient = st.text_input("Patient *", key="v_p")
        with c2:
            cl_list = sorted([c for c in ref_df.iloc[:, 1].unique() if c and c.lower() not in ['nan', 'clinic']])
            sel_cl = st.selectbox("Clinic *", ["선택"] + cl_list + ["➕ 직접입력"], key="v_cl")
            f_cl = st.text_input("클리닉명 입력", key="v_cl_d") if sel_cl == "➕ 직접입력" else sel_cl
        with c3:
            doc_list = ["선택", "➕ 직접입력"]
            if sel_cl not in ["선택", "➕ 직접입력"]:
                matched = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[:, 2].unique()
                doc_list += sorted([d for d in matched if d and d.lower() not in ['nan']])
            sel_doc = st.selectbox("Doctor", doc_list, key="v_doc")
            f_doc = st.text_input("의사명 입력", key="v_doc_d") if sel_doc == "➕ 직접입력" else sel_doc

    with st.expander("2️⃣ 상세 및 날짜 (자동연동)", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            arch = st.radio("Arch", ["Max", "Mand"], horizontal=True, key="v_arch")
            mat = st.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key="v_mat")
            qty = st.number_input("Qty", min_value=1, value=1, key="v_qty")
        with d2:
            is_3d = st.checkbox("3D 모델 (접수시간 없음)", value=True, key="v_3d")
            if not is_3d:
                r_d = st.date_input("접수일", datetime.now(), key="v_rd")
                r_t = st.time_input("시간", datetime.strptime("10:00", "%H:%M").time(), key="v_rt")
                r_str = f"{r_d} {r_t.strftime('%H:%M')}"
            else:
                r_str = "-"
            c_d = st.date_input("완료일(내일)", datetime.now()+timedelta(days=1), key="v_cd")
        with d3:
            # 알렉스 요청: 마감일 선택 시 출고일 자동 2일 전
            due_d = st.date_input("마감일(Due)", datetime.now()+timedelta(days=7), key="v_due")
            ship_d = st.date_input("출고일(자동)", due_d - timedelta(days=2), key="v_sd")
            stat = st.selectbox("Status", ["Normal", "Hold", "Canceled"], key="v_st")

    # 단가 계산
    u_p = 180
    if sel_cl not in ["선택", "➕ 직접입력"]:
        try:
            u_p = int(float(ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]))
        except: u_p = 180
    st.info(f"💰 단가: ${u_p} | 합계: ${u_p * qty}")

    with st.expander("3️⃣ 체크리스트 및 메모"):
        opts = sorted(list(set([i for i in ref_df.iloc[:, 3:].values.flatten() if i and i.lower() not in ['nan', 'none', '']])))
        checks = st.multiselect("체크리스트", opts, key="v_chk")
        memo = st.text_input("메모", key="v_memo")

    if st.button("🚀 최종 저장", use_container_width=True):
        if not case_no or f_cl == "선택" or not patient:
            st.error("⚠️ 필수 항목을 확인해줘!")
        else:
            note = ", ".join(checks) + (f" | {memo}" if memo else "")
            row = pd.DataFrame([{"Case #": case_no, "Clinic": f_cl, "Doctor": f_doc, "Patient": patient, "Arch": arch, "Material": mat, "Price": u_p, "Qty": qty, "Total": u_p*qty, "Receipt Date": r_str, "Completed Date": c_d.strftime('%Y-%m-%d'), "Shipping Date": ship_d.strftime('%Y-%m-%d'), "Due Date": due_d.strftime('%Y-%m-%d'), "Status": stat, "Notes": note}])
            try:
                conn.update(data=pd.concat([main_df, row], ignore_index=True))
                st.success("저장 완료!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e: st.error(f"실패: {e}")

# --- [TAB 2: 정산 (출고일 기준)] ---
with t2:
    v_df = main_df.dropna(subset=['Shipping Date'])
    if not v_df.empty:
        m = datetime.now().month
        m_df = v_df[pd.to_datetime(v_df['Shipping Date']).dt.month == m]
        pay_df = m_df[(m_df['Status'] == 'Normal') | ((m_df['Status'] == 'Canceled') &
