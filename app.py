import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.title("🦷 Skycad Lab Manager")

# 2. 데이터 연결 (ttl=0으로 실시간 데이터 로드)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 레퍼런스 시트 로드
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    # 메인 케이스 시트 로드
    m_df = conn.read(ttl=0)

    # 필수 컬럼 보정 (데이터가 없을 경우 대비)
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

# 3. 저장 성공 후 모든 입력 위젯 초기화 함수
def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 탭 구성
t1, t2, t3 = st.tabs(["📝 케이스 등록", "💰 이번 달 정산", "🔍 케이스 검색"])

# --- [TAB 1: 케이스 등록] ---
with t1:
    st.subheader("📋 새 케이스 정보 입력")
    
    # 상단 기본 정보
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

    # 중간 날짜 및 상세 정보 (확장 섹션)
    with st.expander("⚙️ 작업 상세 및 날짜 연동 (마감일 선택 시 출고일 자동 계산)", expanded=True):
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
            # [중요] 마감일 변경 시 출고일 강제 연동 키 적용
            due_v = st.date_input("마감일(Due Date)", datetime.now() + timedelta(days=7), key="due_input")
            ship_d = st.date_input("출고일(Shipping)", value=due_v - timedelta(days=2), key=f"sd_{due_v}")
            stat = st.selectbox("Status", ["Normal", "Hold", "Canceled"], key="in_stat")

    # 하단 추가 정보 (체크리스트, 사진, 메모)
    with st.expander("✅ 체크리스트 / 📸 사진 / 📝 메모", expanded=True):
        opts = sorted(list(set([i for i in ref_df.iloc[:, 3:].values.flatten() if i and i.lower() != 'nan'])))
        chks = st.multiselect("체크리스트 (중복 선택 가능)", opts, key="in_chk")
        img = st.file_uploader("📸 사진 파일 업로드", type=['jpg', 'png', 'jpeg'], key="in_img")
        memo = st.text_input("추가 메모 입력 (예: 60% 작업 등)", key="in_memo")

    # 단가 계산 로직
    p_u = 180
    if sel_cl not in ["선택", "➕ 직접 입력"]:
        try:
            p_val = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]
            p_u = int(float(p_val))
        except: p_u = 180
    
    st.info(f"💰 현재 단가: ${p_u} | 합계 금액: ${p_u * qty}")

    # 저장 버튼
    if st.button("🚀 최종 데이터 저장하기", use_container_width=True):
        if not case_no or f_cl == "선택" or not patient:
            st.error("⚠️ 필수 항목(Case#, Clinic, Patient)을 모두 입력해주세요!")
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
                # m_df 변수 사용하여 저장
                updated_df = pd.concat([m_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.cache_data.clear()
                st.balloons()
                st.success("✅ 저장이 완료되었습니다! 입력창을 초기화합니다.")
                reset_all() # 페이지 리셋 및 입력창 비우기
            except Exception as e:
                st.error(f"저장 중 오류 발생: {e}")

# --- [TAB 2: 정산 (반영 오류 수정 버전)] ---
with t2:
    cur_m = datetime.now().month
    st.subheader(f"📊 {cur_m}월 정산 내역 및 수당 현황")
    
    if not m_df.empty:
        pdf = m_df.copy()
        # [수정] 날짜 형식이 섞여 있어도(시간 포함 등) 날짜만 정확히 추출하도록 변환
        pdf['s_dt'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        
        this_y = datetime.now().year
        # 이번 달 데이터 필터링
        m_data = pdf[(pdf['s_dt'].dt.month == cur_m) & (pdf['s_dt'].dt.year == this_y)]
        
        if not m_data.empty:
            # 사용자가 보기 편하게 날짜 형식 통일하여 출력
            disp_df = m_data.copy()
            disp_df['Shipping Date'] = disp_df['s_dt'].dt.strftime('%Y-%m-%d')
            
            st.write("✅ 이번 달 전체 출고 리스트:")
            st.dataframe(disp_df[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status', 'Notes']], use_container_width=True)
            
            # 수당 합계 계산 (Normal 상태거나 메모에 60% 포함 시)
            c_normal = (m_data['Status'] == 'Normal')
            c_60 = (m_data['Notes'].str.contains('60%', na=False))
            pay_df = m_data[c_normal | c_60]
            
            total_qty = int(pay_df['Qty'].sum())
            
            col1, col2 = st.columns(2)
            col1.metric("이번 달 수당 인정 수량", f"{total_qty} 개")
            col2.metric("세후 예상 수당 합계", f"${total_qty * 19.505333:,.2f}")
        else:
            st.warning(f"이번 달({cur_m}월)로 등록된 출고 데이터가 없습니다. 'Shipping Date'를 확인해주세요.")
    else:
        st.info("시트에 등록된 데이터가 없습니다.")

# --- [TAB 3: 검색] ---
with t3:
    st.subheader("🔍 케이스 통합 검색")
    query = st.text_input("환자 이름 또는 Case #를 입력하세요", key="search_query")
    if query:
        search_res = m_df[
            m_df['Patient'].str.contains(query, case=False, na=False) | 
            m_df['Case #'].astype(str).str.contains(query)
        ]
        if not search_res.empty:
            st.dataframe(search_res, use_container_width=True)
        else:
            st.info("검색 결과가 없습니다.")
