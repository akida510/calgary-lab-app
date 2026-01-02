import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. 페이지 설정 및 제목
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

# 마감일 -> 출고일(-2일) 연동 함수
def update_shipping_date():
    st.session_state.ship_key = st.session_state.due_key - timedelta(days=2)

if 'due_key' not in st.session_state:
    st.session_state.due_key = datetime.now().date() + timedelta(days=7)
if 'ship_key' not in st.session_state:
    st.session_state.ship_key = st.session_state.due_key - timedelta(days=2)

def force_reset():
    st.session_state.iter_count += 1
    st.cache_data.clear()
    st.rerun()

# 💡 데이터 로드 함수 (정산/검색 안되는 문제 해결 핵심)
def get_full_data():
    try:
        # ttl=0으로 설정하여 캐시를 무시하고 구글 시트에서 즉시 가져옴
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 전처리: 모든 열의 양 끝 공백 제거 및 문자열화
        df = df.astype(str).apply(lambda x: x.str.strip())
        
        # 'Qty'와 'Total'은 숫자로 변환 (계산용)
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
        df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

m_df = get_full_data()
ref_df = conn.read(worksheet="Reference", ttl=300).astype(str)

t1, t2, t3 = st.tabs(["📝 케이스 등록", "💰 이번 달 정산", "🔍 케이스 검색"])

# --- [TAB 1: 케이스 등록] --- (기능 유지)
with t1:
    it = st.session_state.iter_count
    st.subheader("📋 새 케이스 정보 입력")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        case_no = st.text_input("Case # *", key=f"c_{it}")
        patient = st.text_input("Patient Name *", key=f"p_{it}")
    with c2:
        cl_list = sorted([c for c in ref_df.iloc[:, 1].unique() if c and str(c).lower() not in ['nan', 'clinic']])
        sel_cl = st.selectbox("Clinic *", ["선택"] + cl_list + ["➕ 직접"], key=f"cl_sel_{it}")
        f_cl = st.text_input("클리닉명 입력", key=f"fcl_{it}") if sel_cl == "➕ 직접" else sel_cl
    with c3:
        doc_opts = ["선택", "➕ 직접"]
        if sel_cl not in ["선택", "➕ 직접"]:
            docs = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[:, 2].unique()
            doc_opts += sorted([d for d in docs if d and str(d).lower() != 'nan'])
        sel_doc = st.selectbox("Doctor", doc_opts, key=f"doc_sel_{it}")
        f_doc = st.text_input("의사명 입력", key=f"fdoc_{it}") if sel_doc == "➕ 직접" else sel_doc

    with st.expander("⚙️ 작업 상세 및 날짜 연동", expanded=True):
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
            due_d = st.date_input("마감일 (Due Date)", key="due_key", on_change=update_shipping_date)
            ship_d = st.date_input("출고일 (Shipping)", key="ship_key")
            stat = st.selectbox("Status", ["Normal", "Hold", "Canceled"], index=0, key=f"st_{it}")

    with st.expander("✅ 체크리스트 / 📸 사진 / 📝 메모", expanded=True):
        all_vals = ref_df.iloc[:, 3:].values.flatten()
        chk_opts = sorted(list(set([str(i) for i in all_vals if i and str(i).lower() != 'nan'])))
        chks = st.multiselect("체크리스트 선택", chk_opts, key=f"chk_{it}")
        img = st.file_uploader("📸 사진 업로드", type=['jpg', 'png', 'jpeg'], key=f"img_{it}")
        memo = st.text_input("추가 메모 입력", key=f"mem_{it}")

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
            final_notes = ", ".join(chks) + (f" | {memo}" if memo else "")
            
            new_row = pd.DataFrame([{
                "Case #": str(case_no), "Clinic": f_cl, "Doctor": f_doc, "Patient": patient,
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u * qty,
                "Receipt Date": save_rd, "Receipt Time": save_rt,
                "Completed Date": comp_d.strftime('%Y-%m-%d'), 
                "Shipping Date": ship_d.strftime('%Y-%m-%d'), 
                "Due Date": due_d.strftime('%Y-%m-%d'),
                "Status": stat, "Notes": final_notes
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

# --- [TAB 2: 정산 로직 - 복구 완료] ---
with t2:
    cur_m, cur_y = datetime.now().month, datetime.now().year
    st.subheader(f"📊 {cur_y}년 {cur_m}월 정산 현황")
    
    if not m_df.empty:
        pdf = m_df.copy()
        # Shipping Date를 날짜로 강제 변환
        pdf['S_Date_Fixed'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        
        # 이번 달 & Normal 상태 필터링
        m_data = pdf[
            (pdf['S_Date_Fixed'].dt.month == cur_m) & 
            (pdf['S_Date_Fixed'].dt.year == cur_y) & 
            (pdf['Status'].str.lower() == 'normal')
        ]
        
        if not m_data.empty:
            st.dataframe(m_data[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status', 'Notes']], use_container_width=True)
            total_qty = m_data['Qty'].sum()
            c1, c2 = st.columns(2)
            c1.metric("이번 달 총 수량", f"{int(total_qty)} 개")
            c2.metric("세후 예상 수당", f"${total_qty * 19.505333:,.2f}")
        else:
            st.warning(f"{cur_m}월에 출고된 'Normal' 상태 데이터가 없습니다.")
    else:
        st.error("데이터를 불러오지 못했습니다. 구글 시트 연결을 확인하세요.")

# --- [TAB 3: 검색 - 복구 완료] ---
with t3:
    st.subheader("🔍 케이스 통합 검색")
    q = st.text_input("환자 이름 또는 Case #를 입력하세요", key="search_bar")
    
    if not m_df.empty:
        if q:
            # 대소문자 구분 없이 문자열 포함 여부로 검색
            res = m_df[
                m
