import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.title("🦷 Skycad Lab Manager")

# 2. 데이터 연결 및 로드
conn = st.connection("gsheets", type=GSheetsConnection)

def get_full_data():
    # 메인 시트 데이터 로드
    df = conn.read(ttl=0)
    if not df.empty:
        # 데이터 정제: 수량은 숫자, 날짜는 문자열 공백 제거
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
        df['Shipping Date'] = df['Shipping Date'].astype(str).str.strip()
        df['Status'] = df['Status'].astype(str).str.strip()
    return df

m_df = get_full_data()
ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
ref_df = ref_df.apply(lambda x: x.str.strip())

# 💡 [핵심] 입력창 초기화를 위한 세션 카운터
if "iter_count" not in st.session_state:
    st.session_state.iter_count = 0

def force_reset():
    # 카운터를 올려서 모든 위젯의 Key를 변경 (화면 백지화)
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
        raw_cl = ref_df.iloc[:, 1].unique()
        cl_list = sorted([c for c in raw_cl if c and c.lower() not in ['nan', 'clinic']])
        sel_cl = st.selectbox("Clinic *", ["선택"] + cl_list + ["➕ 직접"], key=f"cl_{it}")
        f_cl = st.text_input("클리닉명 입력", key=f"fcl_{it}") if sel_cl == "➕ 직접" else sel_cl
    with c3:
        doc_opts = ["선택", "➕ 직접"]
        if sel_cl not in ["선택", "➕ 직접"]:
            docs = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[:, 2].unique()
            doc_opts += sorted([d for d in docs if d and d.lower() != 'nan'])
        sel_doc = st.selectbox("Doctor", doc_opts, key=f"doc_{it}")
        f_doc = st.text_input("의사명 입력", key=f"fdoc_{it}") if sel_doc == "➕ 직접" else sel_doc

    with st.expander("⚙️ 작업 상세 및 날짜 (마감일 선택 시 출고일 자동 연동)", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            arch = st.radio("Arch", ["Max", "Mand"], horizontal=True, key=f"ar_{it}")
            mat = st.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key=f"mat_{it}")
            qty = st.number_input("Qty", min_value=1, value=1, key=f"q_{it}")
        with d2:
            is_3d = st.checkbox("3D 모델 기반", value=True, key=f"3d_{it}")
            comp_d = st.date_input("완료일", datetime.now() + timedelta(1), key=f"cd_{it}")
        with d3:
            due_v = st.date_input("마감일(Due Date)", datetime.now() + timedelta(7), key=f"due_{it}")
            # 출고일은 마감일에서 2일 전으로 자동 설정
            ship_d = st.date_input("출고일(Shipping)", due_v - timedelta(2), key=f"sd_{it}")
            stat = st.selectbox("Status", ["Normal", "Hold", "Canceled"], index=0, key=f"st_{it}")

    with st.expander("✅ 체크리스트 / 📸 사진 / 📝 메모", expanded=True):
        opts = sorted(list(set([i for i in ref_df.iloc[:, 3:].values.flatten() if i and i.lower() != 'nan'])))
        chks = st.multiselect("체크리스트 선택", opts, key=f"chk_{it}")
        img = st.file_uploader("사진 업로드", type=['jpg', 'png', 'jpeg'], key=f"img_{it}")
        memo = st.text_input("추가 메모", key=f"mem_{it}")

    # 단가 계산 (기본 $180)
    p_u = 180
    if sel_cl not in ["선택", "➕ 직접"]:
        try:
            p_val = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]
            p_u = int(float(p_val))
        except: p_u = 180

    if st.button("🚀 최종 데이터 저장하기", use_container_width=True):
        if not case_no or not f_cl or f_cl == "선택":
            st.error("⚠️ 필수 항목(Case#, Clinic)을 확인해주세요.")
        else:
            final_note = ", ".join(chks) + (f" | {memo}" if memo else "")
            new_row = pd.DataFrame([{
                "Case #": str(case_no), "Clinic": f_cl, "Doctor": f_doc, 
                "Patient": patient, "Arch": arch, "Material": mat, 
                "Price": p_u, "Qty": qty, "Total": p_u * qty, 
                "Shipping Date": ship_d.strftime('%Y-%m-%d'), 
                "Due Date": due_v.strftime('%Y-%m-%d'),
                "Status": stat, "Notes": final_note
            }])
            
            try:
                updated_df = pd.concat([m_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.balloons()
                st.success("✅ 저장 성공!")
                force_reset() # 입력창 싹 비우기
            except Exception as e:
                st.error(f"저장 실패: {e}")

# --- [TAB 2: 이번 달 정산] ---
with t2:
    st.subheader(f"📊 {datetime.now().month}월 정산 (Status: Normal 기준)")
    if not m_df.empty:
        pdf = m_df.copy()
        # 날짜 인식 강화
        pdf['s_dt'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        
        cur_m, cur_y = datetime.now().month, datetime.now().year
        # 이번 달 + Normal 케이스만 필터링
        m_data = pdf[
            (pdf['s_dt'].dt.month == cur_m) & 
            (pdf['s_dt'].dt.year == cur_y) & 
            (pdf['Status'].str.strip().str.lower() == 'normal')
        ].copy()
        
        if not m_data.empty:
            st.dataframe(m_data[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status', 'Notes']], use_container_width=True)
            total_q = int(m_data['Qty'].sum())
            c1, c2 = st.columns(2)
            c1.metric("정산 수량", f"{total_q} 개")
            c2.metric("예상 수당", f"${total_q * 19.505333:,.2f}")
        else:
            st.warning("⚠️ 이번 달 출고(Normal) 데이터가 없습니다. 날짜나 Status를 확인하세요.")
            # 디버깅용: 1월 데이터가 있는데 왜 안 나오는지 확인용 (Normal이 아닐 경우 등)
            with st.expander("참고: 이번 달 모든 상태의 데이터 보기"):
                all_m = pdf[(pdf['s_dt'].dt.month == cur_m) & (pdf['s_dt'].dt.year == cur_y)]
                st.write(all_m[['Shipping Date', 'Patient', 'Status']])
    else:
        st.info("데이터가 비어있습니다.")

# --- [TAB 3: 케이스 검색] ---
with t3:
    st.subheader("🔍 검색")
    q = st.text_input("환자 이름 또는 Case # 검색", key=f"search_{it}")
    if q:
        res = m_df[m_df['Patient'].str.contains(q, case=False, na=False) | 
                   m_df['Case #'].astype(str).str.contains(q)]
        st.dataframe(res, use_container_width=True)
