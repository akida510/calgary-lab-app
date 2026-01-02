import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.title("🦷 Skycad Lab Manager")

# 2. 데이터 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
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

# 💡 [핵심] 입력창을 싹 비우는 가장 강력한 함수
def clear_form():
    for key in list(st.session_state.keys()):
        # 모든 위젯 키를 삭제
        del st.session_state[key]
    st.rerun()

t1, t2, t3 = st.tabs(["📝 케이스 등록", "💰 이번 달 정산", "🔍 케이스 검색"])

# --- [TAB 1: 케이스 등록] ---
with t1:
    st.subheader("📋 새 케이스 정보 입력")
    
    # st.container를 사용하여 레이아웃 그룹화
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            case_no = st.text_input("Case # *", key="v_case")
            patient = st.text_input("Patient Name *", key="v_p")
        with c2:
            raw_c = ref_df.iloc[:, 1].unique()
            cl_list = sorted([c for c in raw_c if c and c.lower() not in ['nan', 'clinic']])
            sel_cl = st.selectbox("Clinic *", ["선택"] + cl_list + ["➕ 직접 입력"], key="v_cl")
            f_cl = st.text_input("클리닉명 입력", key="v_cl_d") if sel_cl == "➕ 직접 입력" else sel_cl
        with c3:
            doc_opts = ["선택", "➕ 직접 입력"]
            if sel_cl not in ["선택", "➕ 직접 입력"]:
                matched = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[:, 2].unique()
                doc_opts += sorted([d for d in matched if d and d.lower() != 'nan'])
            sel_doc = st.selectbox("Doctor", doc_opts, key="v_doc")
            f_doc = st.text_input("의사명 입력", key="v_doc_d") if sel_doc == "➕ 직접 입력" else sel_doc

    with st.expander("⚙️ 작업 상세 및 날짜 연동", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            arch = st.radio("Arch", ["Max", "Mand"], horizontal=True, key="v_arch")
            mat = st.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key="v_mat")
            qty = st.number_input("Qty", min_value=1, value=1, key="v_qty")
        with d2:
            is_3d = st.checkbox("3D 모델 기반", value=True, key="v_3d")
            r_str = "-"
            if not is_3d:
                rd = st.date_input("접수일", datetime.now(), key="v_rd")
                r_str = rd.strftime('%Y-%m-%d')
            comp_d = st.date_input("완료일", datetime.now() + timedelta(days=1), key="v_cd")
        with d3:
            due_v = st.date_input("마감일(Due Date)", datetime.now() + timedelta(days=7), key="v_due_input")
            # 동적 키를 사용하여 마감일 변경 시 리프레시 유도
            ship_d = st.date_input("출고일(Shipping)", value=due_v - timedelta(days=2), key=f"v_sd_{due_v}")
            stat = st.selectbox("Status", ["Normal", "Hold", "Canceled"], index=0, key="v_stat")

    with st.expander("✅ 체크리스트 / 📸 사진 / 📝 메모", expanded=True):
        opts = sorted(list(set([i for i in ref_df.iloc[:, 3:].values.flatten() if i and i.lower() != 'nan'])))
        chks = st.multiselect("체크리스트", opts, key="v_chk")
        img = st.file_uploader("📸 사진 업로드", type=['jpg', 'png', 'jpeg'], key="v_img")
        memo = st.text_input("추가 메모 입력", key="v_memo")

    p_u = 180
    if sel_cl not in ["선택", "➕ 직접 입력"]:
        try:
            p_val = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]
            p_u = int(float(p_val))
        except: p_u = 180
    
    st.info(f"💰 현재 단가: ${p_u} | 합계: ${p_u * qty}")

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
                st.success("✅ 저장 성공! 입력창을 초기화합니다.")
                # 💡 저장 직후 모든 세션 상태를 날려버림
                clear_form()
            except Exception as e:
                st.error(f"저장 중 오류 발생: {e}")

# --- [TAB 2: 정산 (60% 로직 제거 버전)] ---
with t2:
    st.subheader(f"📊 {datetime.now().month}월 수당 현황")
    if not m_df.empty:
        pdf = m_df.copy()
        pdf['s_dt'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        cur_m, cur_y = datetime.now().month, datetime.now().year
        m_data = pdf[(pdf['s_dt'].dt.month == cur_m) & (pdf['s_dt'].dt.year == cur_y)]
        
        if not m_data.empty:
            # 💡 [요청 반영] 60% 로직 제거: 오직 'Normal' 상태만 수당으로 인정
            m_data['인정여부'] = m_data['Status'].apply(lambda x: "✅ 인정" if str(x).strip().lower() == 'normal' else "❌ 제외")
            
            st.dataframe(m_data[['Shipping Date', 'Patient', 'Qty', 'Status', 'Notes', '인정여부']], use_container_width=True)
            
            pay_df = m_data[m_data['인정여부'] == "✅ 인정"]
            total_qty = int(pay_df['Qty'].sum())
            
            c1, c2 = st.columns(2)
            c1.metric("수당 인정 수량 (Normal 기준)", f"{total_qty} 개")
            c2.metric("세후 예상 수당", f"${total_qty * 19.505333:,.2f}")
        else:
            st.info("이번 달 데이터가 없습니다.")

# --- [TAB 3: 검색] ---
with t3:
    query = st.text_input("환자 이름 검색", key="v_search_query")
    if query:
        search_res = m_df[m_df['Patient'].str.contains(query, case=False, na=False)]
        st.dataframe(search_res, use_container_width=True)
