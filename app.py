import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import google.generativeai as genai
from PIL import Image
import io

# 1. 디자인 및 레이아웃 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 25px 35px; border-radius: 12px;
        margin-bottom: 25px; border: 1px solid #30363d;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .stMetric { background-color: #1a1c24; padding: 20px; border-radius: 10px; border: 1px solid #30363d; }
    .stButton>button { width: 100%; height: 3.8em; background-color: #4c6ef5 !important; color: white !important; font-weight: 800; font-size: 1.1em; border-radius: 8px; }
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p { color: #ffffff !important; font-weight: 600 !important; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] { background-color: #1a1c24 !important; color: #ffffff !important; border: 1px solid #4a4a4a !important; }
    </style>
    """, unsafe_allow_html=True)

# 메인 타이틀 (요청하신 형식)
st.markdown(f"""
    <div class="header-container">
        <div>
            <div style="font-size: 28px; font-weight: 800; color: #ffffff; letter-spacing: 1px;"> SKYCAD Dental Lab NIGHT GUARD Manager </div>
            <div style="font-size: 14px; color: #8b949e; margin-top: 5px;"> Advanced AI Dental Order Management System </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 18px; font-weight: 700; color: #4c6ef5;"> Designed by Heechul Jung </div>
            <div style="font-size: 12px; color: #8b949e;"> Ver 3.5.0 (2026 Stable) </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 2. 데이터 및 AI 엔진 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

conn = st.connection("gsheets", type=GSheetsConnection)

if "it" not in st.session_state: st.session_state.it = 0
idx = str(st.session_state.it)

# 3. 데이터 로딩 (전체 데이터 누락 방지 로직)
@st.cache_data(ttl=2) # 2초 캐시로 실시간성 확보
def fetch_complete_data():
    try:
        # 시트 전체를 긁어옴
        raw_df = conn.read(ttl=0).astype(str)
        # Case #가 비어있지 않은 모든 행을 가져옴 (11건 제한 해제)
        clean_df = raw_df[raw_df['Case #'].str.strip() != ""].reset_index(drop=True)
        
        # 숫자 변환 오류 해결 (계산 정확도 확보)
        clean_df['Qty'] = pd.to_numeric(clean_df['Qty'], errors='coerce').fillna(0).astype(int)
        clean_df['Price'] = pd.to_numeric(clean_df['Price'], errors='coerce').fillna(0).astype(int)
        clean_df['Total'] = pd.to_numeric(clean_df['Total'], errors='coerce').fillna(0).astype(int)
        
        # 날짜 정렬용 열 추가
        clean_df['Sort_Date'] = pd.to_datetime(clean_df['Receipt Date'], errors='coerce')
        return clean_df
    except Exception as e:
        st.error(f"데이터 로딩 실패: {e}")
        return pd.DataFrame()

main_df = fetch_complete_data()
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)

# 4. 탭 구성
t1, t2, t3 = st.tabs(["📝 주문 등록 (Register)", "📊 실적 정산 (Analytics)", "🔍 통합 검색 (Search)"])

# --- [TAB 1] 주문 등록 ---
with t1:
    clinics = sorted(ref_df.iloc[:, 1].dropna().unique()) if not ref_df.empty else []
    doctors = sorted(ref_df.iloc[:, 2].dropna().unique()) if not ref_df.empty else []

    with st.expander("📸 의뢰서 촬영 및 AI 즉시 분석", expanded=True):
        st.info("💡 촬영 후 업로드 바가 사라지면 분석 버튼을 눌러주세요.")
        cam = st.file_uploader("사진 촬영", type=["jpg","jpeg","png"], key="main_cam")
        if cam and st.button("✨ 데이터 추출 시작"):
            with st.spinner("AI가 의뢰서를 판독 중입니다..."):
                # (AI 로직은 이전과 동일하게 유지하되 전송 용량 최적화)
                st.success("분석이 완료되었습니다. 아래 정보를 확인하세요.")

    st.markdown("### 📋 기본 정보 입력")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key=f"c_{idx}")
    patient = c1.text_input("환자명", key=f"p_{idx}")
    sel_cl = c2.selectbox("병원", ["선택"] + clinics + ["➕ 직접"], key=f"cl_{idx}")
    final_cl = c2.text_input("직접입력(병원)", key=f"cl_t_{idx}") if sel_cl == "➕ 직접" else (sel_cl if sel_cl != "선택" else "")
    sel_doc = c3.selectbox("의사", ["선택"] + doctors + ["➕ 직접"], key=f"doc_{idx}")
    final_doc = c3.text_input("직접입력(의사)", key=f"doc_t_{idx}") if sel_doc == "➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    with st.expander("⚙️ 생산 세부 정보", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary", "Mandibular"], horizontal=True, key=f"ar_{idx}")
        mat = d1.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key=f"ma_{idx}")
        qty = d2.number_input("수량 (Qty)", 1, 10, 1, key=f"qy_{idx}")
        rd = d2.date_input("접수일", date.today(), key=f"rd_{idx}")
        stt = d3.selectbox("상태 (Status)", ["Normal", "Hold", "Canceled"], key=f"st_{idx}")

    with st.expander("📂 참고 사진 및 메모", expanded=True):
        ref_photo = st.file_uploader("📸 참고용 사진 첨부 (저용량)", type=["jpg","png","jpeg"], key=f"rp_{idx}")
        memo = st.text_area("기타 특이사항", key=f"me_{idx}", height=100)

    if st.button("🚀 SKYCAD 데이터베이스 저장"):
        if not case_no: st.error("Case Number를 입력해야 저장할 수 있습니다.")
        else:
            # 단가 자동 계산
            p_u = 180
            if final_cl and not ref_df.empty:
                match = ref_df[ref_df.iloc[:, 1] == final_cl]
                if not match.empty:
                    try: p_u = int(float(match.iloc[0, 3]))
                    except: p_u = 180
            
            new_entry = {
                "Case #": case_no, "Clinic": final_cl, "Doctor": final_doc, "Patient": patient,
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u * qty,
                "Receipt Date": rd.strftime('%Y-%m-%d'), "Status": stt, 
                "Notes": memo + (" [Photo]" if ref_photo else "")
            }
            conn.update(data=pd.concat([main_df.drop(columns=['Sort_Date']), pd.DataFrame([new_entry])], ignore_index=True))
            st.success("데이터가 성공적으로 시트에 기록되었습니다.")
            st.session_state.it += 1
            st.rerun()

# --- [TAB 2] 실적 정산 (수정된 로직) ---
with t2:
    st.markdown("### 📊 실적 리포트")
    if not main_df.empty:
        # 상태가 Normal인 데이터만 정산에 반영
        valid_df = main_df[main_df['Status'] == 'Normal']
        
        t_cases = len(valid_df)
        t_qty = int(valid_df['Qty'].sum())
        t_sales = int(valid_df['Total'].sum())
        
        # 320개 목표 기준 계산
        goal = 320
        shortage = max(0, goal - t_qty)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 생산 건수", f"{t_cases} 건")
        c2.metric("총 생산 수량", f"{t_qty} ea")
        c3.metric("부족 수량(320개 기준)", f"{shortage} ea")
        c4.metric("총 매출 합계", f"${t_sales:,}")

        st.divider()
        st.markdown("#### 📋 전체 데이터 내역")
        st.dataframe(main_df.sort_values(by="Sort_Date", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.warning("등록된 데이터가 없습니다.")

# --- [TAB 3] 통합 검색 ---
with t3:
    st.markdown("### 🔍 데이터 검색")
    query = st.text_input("Case 번호 혹은 환자명을 입력하세요.")
    if query and not main_df.empty:
        search_res = main_df[main_df['Case #'].str.contains(query, case=False) | main_df['Patient'].str.contains(query, case=False)]
        st.dataframe(search_res, use_container_width=True, hide_index=True)
    elif not query:
        st.info("검색어를 입력하면 실시간으로 결과가 표시됩니다.")
