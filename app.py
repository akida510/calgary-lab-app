import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad", layout="wide")
st.title("🦷 Skycad Lab Manager")

# 2. 데이터 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    r_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    r_df = r_df.apply(lambda x: x.str.strip())
    m_df = conn.read(ttl=0)

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

# 저장 후 초기화 함수
def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("새 케이스 등록")
    
    # 세션 상태로 기본값 관리
    c1, c2, c3 = st.columns(3)
    with c1:
        case_no = st.text_input("Case # *", key="in_case")
        patient = st.text_input("Patient *", key="in_p")
    with c2:
        raw_c = r_df.iloc[:, 1].unique()
        cl_list = sorted([c for c in raw_c if c and c != 'nan' and c != 'Clinic'])
        sel_cl = st.selectbox("Clinic *", ["선택"] + cl_list + ["➕직접"], key="in_cl")
        f_cl = st.text_input("클리닉명", key="in_cl_d") if sel_cl == "➕직접" else sel_cl
    with c3:
        doc_opts = ["선택", "➕직접"]
        if sel_cl not in ["선택", "➕직접"]:
            m_doc = r_df[r_df.iloc[:, 1] == sel_cl].iloc[:, 2].unique()
            doc_opts += sorted([d for d in m_doc if d and d != 'nan'])
        sel_doc = st.selectbox("Doctor", doc_opts, key="in_doc")
        f_doc = st.text_input("의사명", key="in_doc_d") if sel_doc == "➕직접" else sel_doc

    with st.expander("작업 상세 및 날짜 연동", expanded=True):
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
                r_str = rd.strftime('%Y-%m-%d')
            comp_d = st.date_input("완료일", datetime.now()+timedelta(1), key="in_cd")
        with d3:
            due_v = st.date_input("마감일(Due)", datetime.now()+timedelta(7), key="due_input")
            # [핵심] 날짜 강제 연동 키
            ship_d = st.date_input("출고일", value=due_v - timedelta(2), key=f"sd_{due_v}")
            stat = st.selectbox("Status", ["Normal", "Hold", "Canceled"], key="in_stat")

    # [복구] 하단 체크리스트, 사진, 메모 섹션
    with st.expander("✅ 체크리스트 & 📸 사진 & 📝 메모", expanded=True):
        # 레퍼런스 시트에서 체크리스트 옵션 추출
        opts = sorted(list(set([i for i in r_df.iloc[:, 3:].values.flatten() if i and i != 'nan'])))
        chks = st.multiselect("체크리스트 선택", opts, key="in_chk")
        # 사진 업로드 칸
        img = st.file_uploader("📸 사진 업로드 (JPG, PNG)", type=['jpg','png','jpeg'], key="in_img")
        memo = st.text_input("추가 메모 (예: 60% 작업 등)", key="in_memo")

    # 단가 계산
    p_u = 180
    if sel_cl not in ["선택", "➕직접"]:
        try:
            p_val = r_df[r_df.iloc[:, 1] == sel_cl].iloc[0, 3]
            p_u = int(float(p_val))
        except: p_u = 180
    st.info(f"💰 현재 단가: ${p_u} | 합계: ${p_u * qty}")

    if st.button("🚀 최종 저장", use_container_width=True):
        if not case_no or f_cl == "선택" or not patient:
            st.error("⚠️ 필수 항목(Case#, Clinic, Patient)을 입력해주세요!")
        else:
            final_note = ", ".join(chks) + (f" | {memo}" if memo else "")
            row = pd.DataFrame([{
                "Case #": case_no, "Clinic": f_cl, "Doctor": f_doc, 
                "Patient": patient, "Arch": arch, "Material": mat, 
                "Price": p_u, "Qty": qty, "Total": p_u*qty, 
                "Receipt Date": r_str, "Completed Date": comp_d.strftime('%Y-%m-%d'), 
                "Shipping Date": ship_d.strftime('%Y-%m-%d'), 
                "Due Date": due_v.strftime('%Y-%m-%d'), 
                "Status": stat, "Notes": final_note
            }])
            try:
                conn.update(data=pd.concat([main_df, row], ignore_index=True))
                st.cache_data.clear()
                st.success("✅ 저장 성공! 입력창을 초기화합니다.")
                reset_all() # 페이지 새로고침 및 비우기
            except Exception as e: st.error(f"저장 실패: {e}")

# --- [TAB 2: 정산] ---
with t2:
    st.subheader("📊 이번 달 정산 리스트 (출고일 기준)")
    if not m_df.empty:
        pdf = m_df.copy()
        pdf['s_dt'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        this_m, this_y = datetime.now().month, datetime.now().year
        m_data = pdf[(pdf['s_dt'].dt.month == this_m) & (pdf['s_dt'].dt.year == this_y)]
        
        if not m_data.empty:
            st.write("✅ 전체 리스트:")
            st.dataframe(m_data[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status', 'Notes']], use_container_width=True)
            
            # 수당 계산 logic
            c_norm = (m_data['Status'] == 'Normal')
            c_60 = (m_data['Notes'].str.contains('60%', na=False))
            pay_d = m_data[c_norm | c_60]
            t_q = int(pay_d['Qty'].sum())
            c1, c2 = st.columns(2)
            c1.metric("수당 인정 수량", f"{t_q} 개")
            c2.metric("세후 수당 합계", f"${t_q * 19.505333:,.2f}")
        else: st.warning("이번 달 출고 데이터가 없습니다.")

# --- [TAB 3: 검색] ---
with t3:
    q = st.text_input("검색", key="k_search")
    if q:
        res = m_df[m_df['Patient'].str.contains(q, case=False, na=False) | 
                   m_df['Case #'].astype(str).str.contains(q)]
        st.dataframe(res, use_container_width=True)
