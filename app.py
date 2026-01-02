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

# 세션 상태 관리 (날짜 연동용)
if "iter_count" not in st.session_state:
    st.session_state.iter_count = 0
if "due_date" not in st.session_state:
    st.session_state.due_date = datetime.now().date() + timedelta(days=7)
if "ship_date" not in st.session_state:
    st.session_state.ship_date = st.session_state.due_date - timedelta(days=2)

def sync_dates():
    st.session_state.ship_date = st.session_state.due_date - timedelta(days=2)

def force_reset():
    st.session_state.iter_count += 1
    st.session_state.due_date = datetime.now().date() + timedelta(days=7)
    st.session_state.ship_date = st.session_state.due_date - timedelta(days=2)
    st.cache_data.clear()
    st.rerun()

# 💡 데이터를 가져올 때 날짜 형식을 전처리하는 함수
def get_cleaned_data():
    try:
        df = conn.read(ttl=0) # 실시간성 확보
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 'Shipping Date' 열에서 ' 00:00:00' 문자열을 강제로 제거
        if 'Shipping Date' in df.columns:
            df['Shipping Date'] = df['Shipping Date'].astype(str).str.replace(' 00:00:00', '', regex=False).str.strip()
        
        return df
    except:
        return pd.DataFrame()

m_df = get_cleaned_data()
ref_df = conn.read(worksheet="Reference", ttl=300).astype(str)

t1, t2, t3 = st.tabs(["📝 케이스 등록", "💰 이번 달 정산", "🔍 케이스 검색"])

# --- [TAB 1: 케이스 등록] ---
with t1:
    it = st.session_state.iter_count
    st.subheader("📋 새 케이스 정보 입력")
    
    # ... (입력 위젯 부분은 기존과 동일하게 유지) ...
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

    with st.expander("⚙️ 작업 상세 및 날짜/시간 연동", expanded=True):
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
            st.date_input("마감일 (Due Date)", key="due_date", on_change=sync_dates)
            st.date_input("출고일 (Shipping)", key="ship_date")
            stat = st.selectbox("Status", ["Normal", "Hold", "Canceled"], index=0, key=f"st_{it}")

    if st.button("🚀 최종 데이터 저장하기", use_container_width=True):
        if not case_no or f_cl in ["선택", ""]:
            st.error("⚠️ Case #와 Clinic은 필수입니다.")
        else:
            save_rd = "-" if is_3d else rd.strftime('%Y-%m-%d')
            save_rt = "-" if is_3d else rt.strftime('%H:%M')
            
            new_row = pd.DataFrame([{
                "Case #": str(case_no), "Clinic": f_cl, "Doctor": f_doc, "Patient": patient,
                "Arch": arch, "Material": mat, "Price": 180, "Qty": qty, "Total": 180 * qty,
                "Receipt Date": save_rd, "Receipt Time": save_rt,
                "Completed Date": comp_d.strftime('%Y-%m-%d'), 
                "Shipping Date": st.session_state.ship_date.strftime('%Y-%m-%d'), 
                "Due Date": st.session_state.due_date.strftime('%Y-%m-%d'),
                "Status": stat, "Notes": ""
            }])
            try:
                updated_df = pd.concat([m_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.balloons()
                force_reset()
            except Exception as e:
                st.error(f"저장 오류: {e}")

# --- [TAB 2: 정산 로직 - 00:00:00 완벽 제거 및 필터링] ---
with t2:
    st.subheader(f"📊 {datetime.now().year}년 {datetime.now().month}월 정산")
    if not m_df.empty:
        pdf = m_df.copy()
        
        # 💡 해결책: 'Shipping Date'를 날짜 형식으로 강제 변환 (문자열 찌꺼기 제거)
        pdf['S_Date_Fixed'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        
        cur_m = datetime.now().month
        cur_y = datetime.now().year
        
        # 필터링: 이번 달 + 이번 연도 + Status가 Normal인 경우
        m_data = pdf[
            (pdf['S_Date_Fixed'].dt.month == cur_m) & 
            (pdf['S_Date_Fixed'].dt.year == cur_y) & 
            (pdf['Status'].str.strip().str.lower() == 'normal')
        ]
        
        if not m_data.empty:
            st.dataframe(m_data[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status']], use_container_width=True)
            total_qty = pd.to_numeric(m_data['Qty'], errors='coerce').sum()
            c1, c2 = st.columns(2)
            c1.metric("총 수량", f"{int(total_qty)} 개")
            c2.metric("예상 수당", f"${total_qty * 19.505333:,.2f}")
        else:
            st.warning("조건에 맞는 데이터가 없습니다. 시트의 Shipping Date가 이번 달인지 확인해주세요.")

# --- [TAB 3: 검색] ---
with t3:
    q = st.text_input("검색 (환자명 또는 Case#)")
    if q and not m_df.empty:
        res = m_df[m_df['Patient'].str.contains(q, case=False, na=False) | m_df['Case #'].astype(str).str.contains(q)]
        st.dataframe(res, use_container_width=True)
