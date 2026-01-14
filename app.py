import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import io

# 1. 디자인 및 시스템 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 5px; }
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p, .stMetric p { color: #ffffff !important; font-weight: 600 !important; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] { background-color: #1a1c24 !important; color: #ffffff !important; border: 1px solid #4a4a4a !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;"> SKYCAD Dental Lab NIGHT GUARD Manager </div>
        <div style="text-align: right; color: #ffffff;"><span style="font-size: 18px; font-weight: 600;">Designed by Heechul Jung</span></div>
    </div>
    """, unsafe_allow_html=True)

# 2. 연결 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

conn = st.connection("gsheets", type=GSheetsConnection)

# 세션 상태 초기화
if "it" not in st.session_state: st.session_state.it = 0
idx = str(st.session_state.it)

# 3. 데이터 로딩 (캐시를 무시하고 전체 로드)
def load_all_data():
    try:
        # ttl=0으로 설정하여 캐시 문제 해결 (정산 항목 누락 방지)
        df = conn.read(ttl=0).astype(str)
        df = df[df['Case #'].str.strip() != ""].reset_index(drop=True)
        # 숫자형 강제 변환
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

def load_ref():
    try: return conn.read(worksheet="Reference", ttl=600).astype(str)
    except: return pd.DataFrame()

main_df = load_all_data()
ref_df = load_ref()

# 4. AI 분석 (최적화 버전)
def run_ai_logic(img_file):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(img_file)
        img.thumbnail((500, 500))
        prompt = "OCR Dental Order: Case, Patient, Clinic, Doctor. Answer strictly like 'Case: 123, Patient: Kim, Clinic: Sky, Doctor: Jung'"
        response = model.generate_content([prompt, img])
        res_text = response.text.lower()
        extracted = {}
        for part in res_text.split(','):
            if ':' in part:
                k, v = part.split(':', 1)
                extracted[k.strip()] = v.strip()
        return extracted
    except: return None

# 5. 메인 탭
t1, t2, t3 = st.tabs(["📝 등록", "📊 정산", "🔍 검색"])

with t1:
    clinics = sorted(ref_df.iloc[:, 1].dropna().unique()) if not ref_df.empty else []
    doctors = sorted(ref_df.iloc[:, 2].dropna().unique()) if not ref_df.empty else []

    with st.expander("📸 의뢰서 분석 (한 번에 안 찍힐 때 대처법)", expanded=True):
        st.caption("⚠️ 사진 아래 '업로드 바'가 완전히 사라진 후 버튼을 눌러주세요.")
        cam_file = st.file_uploader("카메라 촬영", type=["jpg", "png", "jpeg"], key="ai_cam_final")
        
        # 업로드가 완료되어야만 분석 버튼이 활성화되도록 유도
        if cam_file is not None:
            if st.button("✨ 데이터 추출 시작"):
                with st.spinner("AI 분석 중..."):
                    res = run_ai_logic(cam_file)
                    if res:
                        st.session_state[f"c_{idx}"] = res.get('case', '')
                        st.session_state[f"p_{idx}"] = res.get('patient', '')
                        if res.get('clinic') in clinics: st.session_state[f"cl_{idx}"] = res.get('clinic')
                        if res.get('doctor') in doctors: st.session_state[f"doc_{idx}"] = res.get('doctor')
                        st.success("추출 완료!")
                        st.rerun()
        else:
            st.warning("사진을 촬영하거나 선택하면 분석 버튼이 나타납니다.")

    # 입력 폼
    st.markdown("### 📋 정보 확인")
    col1, col2, col3 = st.columns(3)
    case_no = col1.text_input("Case Number", key=f"c_{idx}")
    patient = col1.text_input("환자명", key=f"p_{idx}")
    
    sel_cl = col2.selectbox("병원", ["선택"] + clinics + ["➕ 직접"], key=f"cl_{idx}")
    final_cl = col2.text_input("직접입력(병원)", key=f"cl_t_{idx}") if sel_cl == "➕ 직접" else (sel_cl if sel_cl != "선택" else "")
    
    sel_doc = col3.selectbox("의사", ["선택"] + doctors + ["➕ 직접"], key=f"doc_{idx}")
    final_doc = col3.text_input("직접입력(의사)", key=f"doc_t_{idx}") if sel_doc == "➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    with st.expander("⚙️ 세부 설정 및 수량", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary", "Mandibular"], horizontal=True, key=f"ar_{idx}")
        mat = d1.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key=f"ma_{idx}")
        qty = d1.number_input("수량(ea)", 1, 10, 1, key=f"qy_{idx}")
        rd = d2.date_input("접수일", date.today(), key=f"rd_{idx}")
        stt = d3.selectbox("상태", ["Normal", "Hold", "Canceled"], key=f"st_{idx}")

    with st.expander("📂 특이사항 및 참고사진", expanded=True):
        ref_p = st.file_uploader("📸 참고사진 첨부", type=["jpg","png","jpeg"], key=f"rp_{idx}")
        memo = st.text_area("메모", key=f"me_{idx}", height=100)

    if st.button("🚀 최종 저장"):
        if not case_no: st.error("Case Number 필수")
        else:
            p_u = 180
            if final_cl and not ref_df.empty:
                m = ref_df[ref_df.iloc[:, 1] == final_cl]
                if not m.empty: p_u = int(float(m.iloc[0, 3]))
            
            new_row = {
                "Case #": case_no, "Clinic": final_cl, "Doctor": final_doc, "Patient": patient,
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u * qty,
                "Receipt Date": rd.strftime('%Y-%m-%d'), "Status": stt, 
                "Notes": f"{memo}" + (" [Photo]" if ref_p else "")
            }
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("저장 완료!")
            st.session_state.it += 1
            st.rerun()

# 📊 [중요] 정산 탭 - 모든 항목이 보이도록 수정
with t2:
    st.markdown("### 📊 정산 데이터 (전체)")
    if not main_df.empty:
        # 모든 열을 명시적으로 표시
        display_cols = ["Case #", "Clinic", "Doctor", "Patient", "Arch", "Material", "Price", "Qty", "Total", "Receipt Date", "Status"]
        
        # 합계 계산용 데이터 필터링
        now = datetime.now()
        main_df['RD_DT'] = pd.to_datetime(main_df['Receipt Date'], errors='coerce')
        this_month = main_df[(main_df['RD_DT'].dt.year == now.year) & (main_df['RD_DT'].dt.month == now.month)]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("이번 달 총 건수", f"{len(this_month)}건")
        m2.metric("총 수량", f"{int(this_month['Qty'].sum())} ea")
        m3.metric("매출 총합", f"${int(this_month['Total'].sum()):,}")
        
        st.dataframe(main_df[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("표시할 데이터가 없습니다.")

with t3:
    st.markdown("### 🔍 검색")
    q = st.text_input("검색어 (Case# / 환자명)")
    if q and not main_df.empty:
        res = main_df[main_df['Case #'].str.contains(q, case=False) | main_df['Patient'].str.contains(q, case=False)]
        st.dataframe(res, use_container_width=True, hide_index=True)
