import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 설정
st.set_page_config(page_title="Skycad", layout="wide")
st.title("🦷 Skycad Lab Manager")

# 2. 데이터 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    r_df = conn.read(worksheet="Reference", ttl=0, header=None)
    r_df = r_df.astype(str).apply(lambda x: x.str.strip())
    m_df = conn.read(ttl=0)

    # 필수 컬럼 생성
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

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    with st.expander("1️⃣ 기본 정보", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            case_no = st.text_input("Case # *", key="k1")
            patient = st.text_input("Patient *", key="k2")
        with c2:
            raw_c = r_df.iloc[:, 1].unique()
            c_list = sorted([c for c in raw_c if c and c != 'nan'])
            s_cl = st.selectbox("Clinic *", ["선택"]+c_list+["➕직접"], key="k3")
            f_cl = st.text_input("직접입력", key="k4") if s_cl == "➕직접" else s_cl
        with c3:
            d_list = ["선택", "➕직접"]
            if s_cl not in ["선택", "➕직접"]:
                m_d = r_df[r_df.iloc[:, 1] == s_cl].iloc[:, 2].unique()
                d_list += sorted([d for d in m_d if d and d != 'nan'])
            s_doc = st.selectbox("Doctor", d_list, key="k5")
            f_doc = st.text_input("의사명", key="k6") if s_doc == "➕직접" else s_doc

    with st.expander("2️⃣ 날짜 연동", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            arch = st.radio("Arch", ["Max", "Mand"], horizontal=True, key="k7")
            mat = st.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key="k8")
            qty = st.number_input("Qty", min_value=1, value=1, key="k9")
        with d2:
            is_3d = st.checkbox("3D 모델", value=True, key="k10")
            r_str = "-"
            if not is_3d:
                rd = st.date_input("접수일", datetime.now(), key="k11")
                rt = st.time_input("시간", datetime.now(), key="k12")
                r_str = f"{rd} {rt.strftime('%H:%M')}"
            cd = st.date_input("완료일", datetime.now()+timedelta(1), key="k13")
        with d3:
            # 알렉스 요청: 마감일 선택 시 출고일 자동 계산
            due = st.date_input("마감일", datetime.now()+timedelta(7), key="k14")
            # 69라인 에러 방지를 위해 수식을 쪼개서 선언
            calc_ship = due - timedelta(days=2)
            ship = st.date_input("출고일", value=calc_ship, key="k15")
            stat = st.selectbox("Status", ["Normal", "Hold", "Canceled"], key="k16")

    with st.expander("3️⃣ 사진 & 메모"):
        opts = sorted(list(set([i for i in r_df.iloc[:, 3:].values.flatten() if i and i != 'nan'])))
        chks = st.multiselect("체크리스트", opts, key="k17")
        img = st.file_uploader("📸 사진", type=['jpg','png'], key="k18")
        memo = st.text_input("메모", key="k19")

    # 단가
    p_u = 180
    if s_cl not in ["선택", "➕직접"]:
        try:
            p_val = r_df[r_df.iloc[:, 1] == s_cl].iloc[0, 3]
            p_u = int(float(p_val))
        except: p_u = 180
    st.info(f"💰 단가: ${p_u} | 합계: ${p_u * qty}")

    if st.button("🚀 저장", use_container_width=True):
        if not case_no or f_cl == "선택" or not patient:
            st.error("⚠️ 필수 항목 부족!")
        else:
            note = ", ".join(chks) + (f" | {memo}" if memo else "")
            row = pd.DataFrame([{
                "Case #": case_no, "Clinic": f_cl, "Doctor": f_doc, 
                "Patient": patient, "Arch": arch, "Material": mat, 
                "Price": p_u, "Qty": qty, "Total": p_u*qty, 
                "Receipt Date": r_str, "Completed Date": cd, 
                "Shipping Date": ship, "Due Date": due, 
                "Status": stat, "Notes": note
            }])
            try:
                up_df = pd.concat([m_df, row], ignore_index=True)
                conn.update(data=up_df)
                st.success("저장 완료!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e: st.error(f"실패: {e}")

# --- [TAB 2: 정산] ---
with t2:
    if not m_df.empty:
        df = m_df.copy()
        df['s_dt'] = pd.to_datetime(df['Shipping Date'], errors='coerce')
        now_m = datetime.now().month
        m_data = df[df['s_dt'].dt.month == now_m]
        # 조건 분리해서 에러 방지
        c_n = (m_data['Status'] == 'Normal')
        c_6 = (m_data['Status'] == 'Canceled') & (m_data['Notes'].str.contains('60%'))
        p_df = m_data[c_n | c_6]
        
        t_q = int(p_df['Qty'].sum())
        st.metric("이번달 출고", f"{t_q} 개")
        st.metric("세후 수당", f"${t_q * 19.505333:,.2f}")
        st.dataframe(p_df[['Shipping Date', 'Clinic', 'Patient', 'Status', 'Notes']], use_container_width=True)

# --- [TAB 3: 검색] ---
with t3:
    q = st.text_input("검색어", key="k20")
    if q:
        res = m_df[m_df['Patient'].str.contains(q, case=False) | 
                   m_df['Case #'].astype(str).str.contains(q)]
        st.dataframe(res, use_container_width=True)
