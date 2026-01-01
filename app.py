import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.title("🦷 Skycad Lab Manager")

# 2. 데이터 연결 (ttl=0)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    # 최신 데이터 강제 로드
    m_df = conn.read(ttl=0)

    cols = ['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 
            'Material', 'Price', 'Qty', 'Total', 'Receipt Date', 
            'Completed Date', 'Shipping Date', 'Due Date', 
            'Status', 'Notes']
    for c in cols:
        if c not in m_df.columns:
            m_df[c] = 0 if c in ['Price', 'Qty', 'Total'] else ""
except Exception as e:
    st.error(f"데이터 연결 오류: {e}")
    st.stop()

def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

t1, t2, t3 = st.tabs(["📝 케이스 등록", "💰 이번 달 정산", "🔍 케이스 검색"])

# --- [TAB 1: 케이스 등록] ---
with t1:
    st.subheader("📋 새 케이스 정보 입력")
    c1, c2, c3 = st.columns(3)
    with c1:
        case_no = st.text_input("Case # *", key="in_case")
        patient = st.text_input("Patient Name *", key="in_p")
    with c2:
        raw_c = ref_df.iloc[:, 1].unique()
        cl_list = sorted([c for c in raw_c if c and c.lower() not in ['nan', 'clinic']])
        sel_cl = st.selectbox("Clinic *", ["선택"] + cl_list + ["➕ 직접 입력"], key="in_cl")
        f_cl = st.text_input("클리닉명 입력", key="in_cl_d") if sel_cl == "➕ 직접 입력" else sel_cl
    with c3:
        doc_opts = ["선택", "➕ 직접 입력"]
        if sel_cl not in ["선택", "➕ 직접 입력"]:
            matched = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[:, 2].unique()
            doc_opts += sorted([d for d in matched if d and d.lower() != 'nan'])
        sel_doc = st.selectbox("Doctor", doc_opts, key="in_doc")
        f_doc = st.text_input("의사명 입력", key="in_doc_d") if sel_doc == "➕ 직접 입력" else sel_doc

    with st.expander("⚙️ 작업 상세 및 날짜 연동", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            arch = st.radio("Arch", ["Max", "Mand"], horizontal=True, key="in_arch")
            mat = st.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key="in_mat")
            qty = st.number_input("Qty", min_value=1, value=1, key="in_qty")
        with d2:
            is_3d = st.checkbox("3D 모델 기반", value=True, key="in_3d")
            r_str = "-"
            if not is_3d:
                rd = st.date_input("접수일", datetime.now(), key="in_rd")
                r_str = rd.strftime('%Y-%m-%d')
            comp_d = st.date_input("완료일", datetime.now() + timedelta(days=1), key="in_cd")
        with d3:
            due_v = st.date_input("마감일(Due Date)", datetime.now() + timedelta(days=7), key="due_input")
            ship_d = st.date_input("출고일(Shipping)", value=due_v - timedelta(days=2), key=f"sd_{due_v}")
            stat = st.selectbox("Status", ["Normal", "Hold", "Canceled"], key="in_stat")

    with st.expander("✅ 체크리스트 / 📸 사진 / 📝 메모", expanded=True):
        opts = sorted(list(set([i for i in ref_df.iloc[:, 3:].values.flatten() if i and i.lower() != 'nan'])))
        chks = st.multiselect("체크리스트 (중복 선택 가능)", opts, key="in_chk")
        img = st.file_uploader("📸 사진 파일 업로드", type=['jpg', 'png', 'jpeg'], key="in_img")
        memo = st.text_input("추가 메모 입력 (예: 60% 작업 등)", key="in_memo")

    p_u = 180
    if sel_cl not in ["선택", "➕ 직접 입력"]:
        try:
            p_val = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]
            p_u = int(float(p_val))
        except: p_u = 180
    
    if st.button("🚀 최종 데이터 저장하기", use_container_width=True):
        if not case_no or not f_cl or not patient:
            st.error("⚠️ 필수 항목을 입력해주세요!")
        else:
            final_note = ", ".join(chks) + (f" | {memo}" if memo else "")
            new_row = pd.DataFrame([{
                "Case #": case_no, "Clinic": f_cl, "Doctor": f_doc, 
                "Patient": patient, "Arch": arch, "Material": mat, 
                "Price": p_u, "Qty": qty, "Total": p_u * qty, 
                "Receipt Date": r_str, 
                "Completed Date": comp_d.strftime('%Y-%m-%d'), 
                "Shipping Date": ship_d.strftime('%Y-%m-%d'), 
                "Due Date": due_v.strftime('%Y-%m-%d'), 
                "Status": stat, "Notes": final_note
            }])
            try:
                updated_df = pd.concat([m_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.cache_data.clear()
                st.success("✅ 저장 성공!")
                reset_all()
            except Exception as e:
                st.error(f"저장 중 오류 발생: {e}")

# --- [TAB 2: 정산 (디버깅 모드)] ---
with t2:
    st.subheader(f"📊 이번 달 정산 현황")
    
    if not m_df.empty:
        pdf = m_df.copy()
        # 모든 날짜를 비교 가능한 형태로 변환
        pdf['s_dt'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        
        # 💡 [해결 포인트 1] 필터링 조건 완화
        # 이번 달 데이터만 일단 다 가져와봅니다.
        cur_m, cur_y = datetime.now().month, datetime.now().year
        m_data = pdf[(pdf['s_dt'].dt.month == cur_m) & (pdf['s_dt'].dt.year == cur_y)]
        
        if not m_data.empty:
            st.write("✅ 이번 달 출고 리스트 (전체)")
            # 전체 데이터를 먼저 보여줘서 시각적으로 확인하게 함
            st.dataframe(m_data[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status', 'Notes']], use_container_width=True)
            
            # 💡 [해결 포인트 2] 수당 합계 로직 수정
            # 'Status'가 'Normal'인 것만 합산하거나, 메모에 '60%'가 있는 경우 합산
            pay_condition = (m_data['Status'] == 'Normal') | (m_data['Notes'].str.contains('60%', na=False))
            pay_df = m_data[pay_condition]
            
            total_qty = int(pay_df['Qty'].sum())
            
            c1, c2 = st.columns(2)
            c1.metric("수당 인정 수량", f"{total_qty} 개")
            c2.metric("세후 예상 수당", f"${total_qty * 19.505333:,.2f}")
            
            if pay_df.empty:
                st.info("💡 리스트에는 데이터가 있지만, Status가 'Normal'이 아니어서 수당 합계에는 포함되지 않았습니다.")
        else:
            st.warning("⚠️ 이번 달(1월) 출고 데이터가 검색되지 않습니다. 시트에서 'Shipping Date' 열의 연도와 월을 확인해주세요!")
            # 데이터가 아예 안 나올 경우를 대비해 시트 전체 데이터를 살짝 보여줌 (디버깅용)
            with st.expander("🔍 시트 전체 데이터 확인 (날짜 오류 확인용)"):
                st.write(m_df[['Shipping Date', 'Patient', 'Status']].tail(10))
    else:
        st.info("데이터가 없습니다.")

# --- [TAB 3: 검색] ---
with t3:
    query = st.text_input("환자 이름 검색", key="search_query")
    if query:
        search_res = m_df[m_df['Patient'].str.contains(query, case=False, na=False)]
        st.dataframe(search_res, use_container_width=True)
