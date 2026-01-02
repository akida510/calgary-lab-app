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
        <span style="font-size: 0.9rem; color: #888;">Designed by Alex Jung</span>
    </div>
    """, 
    unsafe_allow_html=True
)

# 2. 데이터 연결 함수
conn = st.connection("gsheets", type=GSheetsConnection)

def get_full_data():
    try:
        df = conn.read(ttl=60)
        if df is None or df.empty:
            return pd.DataFrame(columns=['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 'Material', 'Price', 'Qty', 'Total', 'Shipping Date', 'Due Date', 'Status', 'Notes'])
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
        df['Shipping Date'] = df['Shipping Date'].astype(str).str.strip()
        df['Status'] = df['Status'].astype(str).str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()

m_df = get_full_data()

try:
    ref_df = conn.read(worksheet="Reference", ttl=300).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
except:
    ref_df = pd.DataFrame()

if "iter_count" not in st.session_state:
    st.session_state.iter_count = 0

def force_reset():
    st.session_state.iter_count += 1
    st.cache_data.clear()
    st.rerun()

t1, t2, t3 = st.tabs(["📝 케이스 등록", "💰 이번 달 정산", "🔍 케이스 검색"])

# --- [TAB 1: 케이스 등록] ---
with t1:
    it = st.session_state.iter_count
    st.subheader("📋 새 케이스 정보 입력")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        case_no = st.text_input("Case # *", key=f"c_{it}")
        patient = st.text_input("Patient Name *", key=f"p_{it}")
    with c2:
        if not ref_df.empty:
            raw_cl = ref_df.iloc[:, 1].unique()
            cl_list = sorted([c for c in raw_cl if c and c.lower() not in ['nan', 'clinic']])
        else:
            cl_list = []
        sel_cl = st.selectbox("Clinic *", ["선택"] + cl_list + ["➕ 직접"], key=f"cl_{it}")
        f_cl = st.text_input("클리닉명 입력", key=f"fcl_{it}") if sel_cl == "➕ 직접" else sel_cl
    with c3:
        doc_opts = ["선택", "➕ 직접"]
        if not ref_df.empty and sel_cl not in ["선택", "➕ 직접"]:
            docs = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[:, 2].unique()
            doc_opts += sorted([d for d in docs if d and d.lower() != 'nan'])
        sel_doc = st.selectbox("Doctor", doc_opts, key=f"doc_{it}")
        f_doc = st.text_input("의사명 입력", key=f"fdoc_{it}") if sel_doc == "➕ 직접" else sel_doc

    with st.expander("⚙️ 작업 상세 및 날짜 연동", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            arch = st.radio("Arch", ["Max", "Mand"], horizontal=True, key=f"ar_{it}")
            mat = st.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key=f"mat_{it}")
            qty = st.number_input("Qty", min_value=1, value=1, key=f"q_{it}")
        with d2:
            comp_d = st.date_input("완료일", datetime.now() + timedelta(1), key=f"cd_{it}")
            due_v = st.date_input("마감일(Due Date)", datetime.now() + timedelta(7), key=f"due_{it}")
        with d3:
            ship_d = st.date_input("출고일(Shipping)", due_v - timedelta(2), key=f"sd_{it}")
            stat = st.selectbox("Status", ["Normal", "Hold", "Canceled"], index=0, key=f"st_{it}")

    memo = st.text_input("메모 / 체크리스트", key=f"mem_{it}")

    if st.button("🚀 데이터 저장", use_container_width=True):
        if not case_no or f_cl in ["선택", ""]:
            st.error("⚠️ 필수 항목을 입력해주세요.")
        else:
            # 이 부분이 에러가 났던 지점입니다. 들여쓰기를 정확히 맞췄습니다.
            final_note = str(memo)
            new_row = pd.DataFrame([{
                "Case #": str(case_no), "Clinic": f_cl, "Doctor": f_doc, 
                "Patient": patient, "Arch": arch, "Material": mat, 
                "Price": 180, "Qty": qty, "Total": 180 * qty, 
                "Shipping Date": ship_d.strftime('%Y-%m-%d'), 
                "Due Date": due_v.strftime('%Y-%m-%d'),
                "Status": stat, "Notes": final_note
            }])
            try:
                updated_df = pd.concat([m_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success("✅ 저장 성공!")
                time.sleep(1) 
                force_reset()
            except Exception as e:
                st.error(f"저장 중 오류 발생: {e}")

# --- [TAB 2: 이번 달 정산] ---
with t2:
    st.subheader(f"📊 {datetime.now().month}월 정산 (Status: Normal)")
    if not m_df.empty:
        pdf = m_df.copy()
        pdf['s_dt'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        cur_m, cur_y = datetime.now().month, datetime.now().year
        m_data = pdf[(pdf['s_dt'].dt.month == cur_m) & (pdf['s_dt'].dt.year == cur_y) & (pdf['Status'].str.strip().str.lower() == 'normal')]
        
        if not m_data.empty:
            st.dataframe(m_data[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status', 'Notes']], use_container_width=True)
            total_q = int(m_data['Qty'].sum())
            c1, c2 = st.columns(2)
            c1.metric("정산 수량", f"{total_q} 개")
            c2.metric("예상 수당", f"${total_q * 19.505333:,.2f}")
        else:
            st.warning("조건에 맞는 데이터가 없습니다.")

# --- [TAB 3: 검색] ---
with t3:
    q = st.text_input("검색 (환자명 또는 Case#)", key=f"search_{it}")
    if q and not m_df.empty:
        res = m_df[m_df['Patient'].str.contains(q, case=False, na=False) | m_df['Case #'].astype(str).str.contains(q)]
        st.dataframe(res, use_container_width=True)
