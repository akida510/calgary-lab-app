import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad", layout="wide")
st.title("🦷 Skycad Lab Manager")

# 2. 데이터 연결 (ttl=0으로 실시간성 확보)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 레퍼런스 시트
    r_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    # 메인 데이터 시트 (항상 최신 데이터를 읽어옴)
    m_df = conn.read(ttl=0)

    # 필수 컬럼 보정
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

# 3. 입력창 초기화 함수
def reset_form():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("새 케이스 등록")
    c1, c2, c3 = st.columns(3)
    with c1:
        case_no = st.text_input("Case # *", key="in_case")
        patient = st.text_input("Patient *", key="in_p")
    with c2:
        raw_c = r_df.iloc[:, 1].unique()
        c_list = sorted([c for c in raw_c if c and c != 'nan' and c != 'Clinic'])
        sel_cl = st.selectbox("Clinic *", ["선택"] + c_list + ["➕직접"], key="in_cl")
        f_cl = st.text_input("클리닉명", key="in_cl_d") if sel_cl == "➕직접" else sel_cl
    with c3:
        doc_opts = ["선택", "➕직접"]
        if sel_cl not in ["선택", "➕직접"]:
            m_doc = r_df[r_df.iloc[:, 1] == sel_cl].iloc[:, 2].unique()
            doc_opts += sorted([d for d in m_doc if d and d != 'nan'])
        sel_doc = st.selectbox("Doctor", doc_opts, key="in_doc")
        f_doc = st.text_input("의사명", key="in_doc_d") if sel_doc == "➕직접" else sel_doc

    with st.expander("작업 상세 및 날짜", expanded=True):
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
            due_v = st.date_input("마감일", datetime.now()+timedelta(7), key="due_input")
            # 날짜 강제 연동 키
            ship_d = st.date_input("출고일", value=due_v - timedelta(2), key=f"sd_{due_v}")
            stat = st.selectbox("Status", ["Normal", "Hold", "Canceled"], key="in_stat")

    # 단가 자동 계산
    p_u = 180
    if sel_cl not in ["선택", "➕직접"]:
        try:
            p_val = r_df[r_df.iloc[:, 1] == sel_cl].iloc[0, 3]
            p_u = int(float(p_val))
        except: p_u = 180

    if st.button("🚀 최종 저장", use_container_width=True):
        if not case_no or f_cl == "선택" or not patient:
            st.error("필수 항목 입력 누락!")
        else:
            row = pd.DataFrame([{
                "Case #": case_no, "Clinic": f_cl, "Doctor": f_doc, 
                "Patient": patient, "Arch": arch, "Material": mat, 
                "Price": p_u, "Qty": qty, "Total": p_u*qty, 
                "Receipt Date": r_str, "Completed Date": comp_d.strftime('%Y-%m-%d'), 
                "Shipping Date": ship_d.strftime('%Y-%m-%d'), 
                "Due Date": due_v.strftime('%Y-%m-%d'), 
                "Status": stat, "Notes": ""
            }])
            try:
                conn.update(data=pd.concat([m_df, row], ignore_index=True))
                st.cache_data.clear()
                st.success("저장 성공!")
                reset_form() # 여기서 페이지 새로고침
            except Exception as e: st.error(f"실패: {e}")

# --- [TAB 2: 정산 (강제 출력 모드)] ---
with t2:
    st.subheader("📊 이번 달 출고 리스트")
    if not m_df.empty:
        # 데이터 복사 후 날짜 변환
        pdf = m_df.copy()
        pdf['s_dt'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        
        # [수정] 이번 달(1월) 데이터만 추출 (Status 조건 없이 일단 다 보여줌)
        this_m = datetime.now().month
        this_y = datetime.now().year
        m_data = pdf[(pdf['s_dt'].dt.month == this_m) & (pdf['s_dt'].dt.year == this_y)]
        
        if not m_data.empty:
            # 1. 전체 리스트 먼저 보여주기 (여기서 4개가 들어있는지 확인 가능)
            st.write("✅ 이번 달에 출고일이 잡힌 모든 케이스:")
            st.dataframe(m_data[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status']], use_container_width=True)
            
            # 2. 수당 계산 (Normal 혹은 60% 메모 있는 것만 별도로 계산)
            c_norm = (m_data['Status'] == 'Normal')
            c_60 = (m_data['Notes'].str.contains('60%', na=False))
            pay_data = m_data[c_norm | c_60]
            
            t_q = int(pay_data['Qty'].sum())
            c1, c2 = st.columns(2)
            c1.metric("수당 인정 수량", f"{t_q} 개")
            c2.metric("세후 수당 합계", f"${t_q * 19.505333:,.2f}")
        else:
            st.warning("이번 달 출고일로 등록된 데이터가 없습니다. 검색 탭에서 날짜를 확인해 보세요!")
    else:
        st.info("데이터가 비어있습니다.")

# --- [TAB 3: 검색] ---
with t3:
    q = st.text_input("검색", key="k_search")
    if q:
        res = m_df[m_df['Patient'].str.contains(q, case=False, na=False) | 
                   m_df['Case #'].astype(str).str.contains(q)]
        st.dataframe(res, use_container_width=True)
