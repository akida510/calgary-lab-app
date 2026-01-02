import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. 페이지 설정 및 제목/제작자 표기
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

# 2. 데이터 연결 및 초기화
conn = st.connection("gsheets", type=GSheetsConnection)

# 세션 상태 설정
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

def get_full_data():
    try:
        # ttl을 0으로 설정하여 캐시 없이 실시간 데이터를 읽어옵니다.
        df = conn.read(ttl=0)
        if df is None or df.empty:
            cols = ['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 'Material', 'Price', 'Qty', 'Total', 'Receipt Date', 'Receipt Time', 'Completed Date', 'Shipping Date', 'Due Date', 'Status', 'Notes']
            return pd.DataFrame(columns=cols)
        return df
    except:
        return pd.DataFrame()

m_df = get_full_data()
ref_df = conn.read(worksheet="Reference", ttl=300).astype(str)

t1, t2, t3 = st.tabs(["📝 케이스 등록", "💰 이번 달 정산", "🔍 케이스 검색"])

# --- [TAB 1: 케이스 등록 (기존 기능 완벽 유지)] ---
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

    # 저장 로직
    if st.button("🚀 최종 데이터 저장하기", use_container_width=True):
        if not case_no or f_cl in ["선택", ""]:
            st.error("⚠️ Case #와 Clinic은 필수입니다.")
        else:
            p_u = 180
            if sel_cl not in ["선택", "➕ 직접"]:
                try: p_u = int(float(ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]))
                except: p_u = 180
            
            save_rd = "-" if is_3d else rd.strftime('%Y-%m-%d')
            save_rt = "-" if is_3d else rt.strftime('%H:%M')
            
            new_row = pd.DataFrame([{
                "Case #": str(case_no), "Clinic": f_cl, "Doctor": f_doc, "Patient": patient,
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u * qty,
                "Receipt Date": save_rd, "Receipt Time": save_rt,
                "Completed Date": comp_d.strftime('%Y-%m-%d'), 
                "Shipping Date": st.session_state.ship_date.strftime('%Y-%m-%d'), 
                "Due Date": st.session_state.due_date.strftime('%Y-%m-%d'),
                "Status": stat, "Notes": ", ".join(st.session_state.get(f"chk_{it}", [])) + f" | {memo}" if 'memo' in locals() else ""
            }])
            try:
                updated_df = pd.concat([m_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.balloons()
                force_reset()
            except Exception as e:
                st.error(f"저장 오류: {e}")

# --- [TAB 2: 정산 로직 (가장 강력한 변환 적용)] ---
with t2:
    st.subheader(f"📊 {datetime.now().year}년 {datetime.now().month}월 정산 현황")
    if not m_df.empty:
        pdf = m_df.copy()
        
        # 💡 해결책: 'Shipping Date'를 문자열로 변환 후 날짜 형식이 아닌 데이터는 제거하고 날짜로 강제 변환
        pdf['Shipping Date'] = pdf['Shipping Date'].astype(str).str.replace(' 00:00:00', '')
        pdf['S_Date_Converted'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        
        # 현재 날짜 정보
        cur_m = datetime.now().month
        cur_y = datetime.now().year
        
        # 필터링: 변환된 날짜가 유효하고, 월/년이 일치하며, 상태가 Normal인 데이터
        m_data = pdf[
            (pdf['S_Date_Converted'].dt.month == cur_m) & 
            (pdf['S_Date_Converted'].dt.year == cur_y) & 
            (pdf['Status'].str.strip().str.lower() == 'normal')
        ]
        
        if not m_data.empty:
            st.dataframe(m_data[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status', 'Notes']], use_container_width=True)
            total_qty = pd.to_numeric(m_data['Qty']).sum()
            c1, c2 = st.columns(2)
            c1.metric("이번 달 총 수량", f"{int(total_qty)} 개")
            c2.metric("세후 예상 수당", f"${total_qty * 19.505333:,.2f}")
        else:
            st.warning(f"이번 달({cur_m}월) 'Normal' 상태의 데이터가 없습니다. (구글 시트의 Shipping Date를 확인해 주세요)")

# --- [TAB 3: 검색] ---
with t3:
    q = st.text_input("검색 (환자명 또는 Case#)", key="search_input")
    if q and not m_df.empty:
        res = m_df[m_df['Patient'].str.contains(q, case=False, na=False) | m_df
