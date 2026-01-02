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
        df = conn.read(ttl=5)
        if df is None or df.empty:
            cols = ['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 'Material', 'Price', 'Qty', 'Total', 'Receipt Date', 'Receipt Time', 'Completed Date', 'Shipping Date', 'Due Date', 'Status', 'Notes']
            return pd.DataFrame(columns=cols)
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

m_df = get_full_data()
ref_df = conn.read(worksheet="Reference", ttl=300).astype(str)

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

    with st.expander("✅ 체크리스트 / 📸 사진 / 📝 메모", expanded=True):
        chk_opts = sorted(list(set([i for i in ref_df.iloc[:, 3:].values.flatten() if i and str(i).lower() != 'nan'])))
        chks = st.multiselect("체크리스트 선택", chk_opts, key=f"chk_{it}")
        img = st.file_uploader("📸 사진 업로드", type=['jpg', 'png', 'jpeg'], key=f"img_{it}")
        memo = st.text_input("추가 메모 입력", key=f"mem_{it}")

    p_u = 180
    if sel_cl not in ["선택", "➕ 직접"]:
        try:
            p_val = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]
            p_u = int(float(p_val))
        except: p_u = 180

    if st.button("🚀 최종 데이터 저장하기", use_container_width=True):
        if not case_no or f_cl in ["선택", ""]:
            st.error("⚠️ Case #와 Clinic은 필수입니다.")
        else:
            final_note = ", ".join(chks) + (f" | {memo}" if memo else "")
            save_rd = "-" if is_3d else rd.strftime('%Y-%m-%d')
            save_rt = "-" if is_3d else rt.strftime('%H:%M')
            
            new_row = pd.DataFrame([{
                "Case #": str(case_no), "Clinic": f_cl, "Doctor": f_doc, 
                "Patient": patient, "Arch": arch, "Material": mat, 
                "Price": p_u, "Qty": qty, "Total": p_u * qty, 
                "Receipt Date": save_rd, "Receipt Time": save_rt,
                "Completed Date": comp_d.strftime('%Y-%m-%d'), 
                "Shipping Date": st.session_state.ship_date.strftime('%Y-%m-%d'), 
                "Due Date": st.session_state.due_date.strftime('%Y-%m-%d'),
                "Status": stat, "Notes": final_note
            }])
            try:
                updated_df = pd.concat([m_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.balloons()
                st.success("✅ 저장 성공!")
                time.sleep(1) 
                force_reset()
            except Exception as e:
                st.error(f"저장 오류: {e}")

# --- [TAB 2: 정산 로직 대폭 강화] ---
with t2:
    st.subheader(f"📊 {datetime.now().month}월 정산 내역")
    if not m_df.empty:
        pdf = m_df.copy()
        
        # 💡 핵심: 어떤 형식이든(00:00:00 포함 여부 무관) 날짜로 강제 변환
        pdf['Shipping Date'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        
        cur_m, cur_y = datetime.now().month, datetime.now().year
        
        # 💡 필터링 조건 강화: 연도와 월이 일치하고 Status가 Normal인 데이터
        m_data = pdf[
            (pdf['Shipping Date'].dt.month == cur_m) & 
            (pdf['Shipping Date'].dt.year == cur_y) & 
            (pdf['Status'].str.strip().str.capitalize() == 'Normal')
        ]
        
        if not m_data.empty:
            # 출력용 날짜 포맷 정리
            display_df = m_data.copy()
            display_df['Shipping Date'] = display_df['Shipping Date'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status', 'Notes']], use_container_width=True)
            
            total_q = int(m_data['Qty'].sum())
            c1, c2 = st.columns(2)
            c1.metric("이번 달 총 수량", f"{total_q} 개")
            c2.metric("예상 수당 (Tax 포함)", f"${total_q * 19.505333:,.2f}")
        else:
            st.warning(f"현재 {cur_m}월에 출고(Shipping)된 'Normal' 상태의 케이스가 없습니다.")

with t3:
    q = st.text_input("검색 (환자명 또는 Case#)", key="search_input")
    if q and not m_df.empty:
        res = m_df[m_df['Patient'].str.contains(q, case=False, na=False) | m_df['Case #'].astype(str).str.contains(q)]
        st.dataframe(res, use_container_width=True)
