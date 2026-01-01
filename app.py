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

    with st.expander("2️⃣ 상세 및 날짜 (출고일 자동연동)", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            arch = st.radio("Arch", ["Max", "Mand"], horizontal=True, key="v_arch")
            mat = st.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key="v_mat")
            qty = st.number_input("Qty", min_value=1, value=1, key="v_qty")
        with d2:
            is_3d = st.checkbox("3D 모델", value=True, key="v_3d")
            r_str = "-"
            if not is_3d:
                r_d = st.date_input("접수일", datetime.now(), key="v_rd")
                r_t = st.time_input("시간", datetime.now(), key="v_rt")
                r_str = f"{r_d} {r_t.strftime('%H:%M')}"
            c_d = st.date_input("완료일", datetime.now()+timedelta(days=1), key="v_cd")
        with d3:
            # 알렉스 요청: 마감일 선택 시 출고일 자동 2일 전
            due_d = st.date_input("마감일(Due)", datetime.now()+timedelta(days=7), key="v_due")
            ship_d = st.date_input("출고일(Ship)", due_d - timedelta(days=2), key="v_sd")
            stat = st.selectbox("Status", ["Normal", "Hold", "Canceled"], key="v_st")

    # 단가
    u_p = 180
    if sel_cl not in ["선택", "➕ 직접"]:
        try:
            u_p = int(float(ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]))
        except: u_p = 180
    st.info(f"💰 단가: ${u_p} | 합계: ${u_p * qty}")

    with st.expander("3️⃣ 체크리스트 & 사진 & 메모", expanded=True):
        opts = sorted(list(set([i for i in ref_df.iloc[:, 3:].values.flatten() if i and i.lower() not in ['nan', 'none', '']])))
        checks = st.multiselect("체크리스트", opts, key="v_chk")
        # [복구] 사진 입력창
        up_img = st.file_uploader("📸 사진 업로드", type=['jpg','png','jpeg'], key="v_img")
        memo = st.text_input("메모 (예: 60% 작업)", key="v_memo")

    if st.button("🚀 최종 저장", use_container_width=True):
        if not case_no or f_cl == "선택" or not patient:
            st.error("⚠️ 필수 항목을 입력해주세요!")
        else:
            note = ", ".join(checks) + (f" | {memo}" if memo else "")
            row = pd.DataFrame([{"Case #": case_no, "Clinic": f_cl, "Doctor": f_doc, "Patient": patient, "Arch": arch, "Material": mat, "Price": u_p, "Qty": qty, "Total": u_p*qty, "Receipt Date": r_str, "Completed Date": c_d.strftime('%Y-%m-%d'), "Shipping Date": ship_d.strftime('%Y-%m-%d'), "Due Date": due_d.strftime('%Y-%m-%d'), "Status": stat, "Notes": note}])
            try:
                conn.update(data=pd.concat([main_df, row], ignore_index=True))
                st.success("저장 완료!")
                st.balloons()
                st.cache_data.clear()
                st.rerun()
            except Exception as e: st.error(f"저장 실패: {e}")

# --- [TAB 2: 정산 (출고일 기준)] ---
with t2:
    st.subheader("💵 이번 달 수당 요약")
    if not main_df.empty:
        # 출고일 기준 필터링
        m_df = main_df.copy()
        m_df['Shipping Date'] = pd.to_datetime(m_df['Shipping Date'], errors='coerce')
        cur_m = datetime.now().month
        this_m = m_df[m_df['Shipping Date'].dt.month == cur_m]
        
        # 정산 조건: Normal 상태 혹은 메모에 60%가 포함된 Canceled 상태
        c1 = (this_m['Status'] == 'Normal')
        c2 = (this_m['Status'] == 'Canceled') & (this_m['Notes'].str.contains('60%', na=False))
        pay_df = this_m[c1 | c2]
        
        t_qty = int(pay_df['Qty'].sum())
        col1, col2 = st.columns(2)
        col1.metric("이번달 총 출고", f"{t_qty} 개")
        col2.metric("예상 수당 (세후)", f"${t_qty * 19.505333:,.2f}")
        
        st.write("---")
        st.write("📋 이번 달 정산 리스트")
        st.dataframe(pay_df[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status', 'Notes']], use_container_width=True)
    else:
        st.info("등록된 데이터가 없습니다.")

# --- [TAB 3: 검색] ---
with t3:
    st.subheader("🔍 케이스 검색")
    q = st.text_input("검색어 (환자명 또는 번호)", key="v_search")
    if q
