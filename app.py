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

# 2. 데이터베이스 및 AI 연결
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

conn = st.connection("gsheets", type=GSheetsConnection)

# 세션 상태 초기화
if "it" not in st.session_state: st.session_state.it = 0
idx = str(st.session_state.it)

# 3. 데이터 로드 로직 (안정성 강화)
@st.cache_data(ttl=5) # 5초마다 갱신하여 정산/검색 실시간성 확보
def load_main_data():
    try:
        df = conn.read(ttl=0).astype(str)
        # 공백 제거 및 필수 열 확인
        df = df[df['Case #'].str.strip() != ""].reset_index(drop=True)
        return df
    except:
        return pd.DataFrame(columns=["Case #", "Clinic", "Doctor", "Patient", "Arch", "Material", "Price", "Qty", "Total", "Receipt Date", "Status", "Notes"])

@st.cache_data(ttl=600)
def load_ref_data():
    try: return conn.read(worksheet="Reference", ttl=600).astype(str)
    except: return pd.DataFrame()

main_df = load_main_data()
ref_df = load_ref_data()

# 4. AI 분석 함수 (초경량 전송)
def run_fast_ai(img_file):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(img_file)
        img.thumbnail((400, 400)) # 전송 용량을 위해 아주 작게 축소
        
        prompt = "Extract from dental order. Reply ONLY in this format: Case: value, Patient: value, Clinic: value, Doctor: value"
        response = model.generate_content([prompt, img])
        
        # 텍스트 파싱
        res_text = response.text.lower()
        extracted = {}
        for item in res_text.split(','):
            if ':' in item:
                k, v = item.split(':', 1)
                extracted[k.strip()] = v.strip()
        return extracted
    except:
        return None

# 5. 메인 탭
t1, t2, t3 = st.tabs(["📝 등록 (Register)", "📊 통계 및 정산 (Analytics)", "🔍 검색 (Search)"])

with t1:
    clinics = sorted(ref_df.iloc[:, 1].dropna().unique()) if not ref_df.empty else []
    doctors = sorted(ref_df.iloc[:, 2].dropna().unique()) if not ref_df.empty else []

    with st.expander("📸 의뢰서 촬영 및 AI 분석", expanded=True):
        cam_file = st.file_uploader("전체화면 카메라로 의뢰서 촬영", type=["jpg", "png", "jpeg"], key="ai_cam")
        if cam_file and st.button("✨ 즉시 분석 시작"):
            with st.spinner("데이터 추출 중..."):
                res = run_fast_ai(cam_file)
                if res:
                    st.session_state[f"c_{idx}"] = res.get('case', '')
                    st.session_state[f"p_{idx}"] = res.get('patient', '')
                    if res.get('clinic') in clinics: st.session_state[f"cl_{idx}"] = res.get('clinic')
                    if res.get('doctor') in doctors: st.session_state[f"doc_{idx}"] = res.get('doctor')
                    st.success("추출 완료! 아래 내용을 확인하세요.")
                    st.rerun()

    # 입력 폼
    st.markdown("### 📋 정보 확인")
    col1, col2, col3 = st.columns(3)
    case_no = col1.text_input("Case Number", key=f"c_{idx}")
    patient = col1.text_input("환자명", key=f"p_{idx}")
    
    sel_cl = col2.selectbox("병원", ["선택"] + clinics + ["➕ 직접"], key=f"cl_{idx}")
    final_cl = col2.text_input("직접입력(병원)", key=f"cl_t_{idx}") if sel_cl == "➕ 직접" else (sel_cl if sel_cl != "선택" else "")
    
    sel_doc = col3.selectbox("의사", ["선택"] + doctors + ["➕ 직접"], key=f"doc_{idx}")
    final_doc = col3.text_input("직접입력(의사)", key=f"doc_t_{idx}") if sel_doc == "➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    with st.expander("⚙️ 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary", "Mandibular"], horizontal=True, key=f"ar_{idx}")
        mat = d1.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key=f"ma_{idx}")
        qty = d1.number_input("수량", 1, 10, 1, key=f"qy_{idx}")
        rd = d2.date_input("접수일", date.today(), key=f"rd_{idx}")
        stt = d3.selectbox("상태", ["Normal", "Hold", "Canceled"], key=f"st_{idx}")

    with st.expander("📂 특이사항 및 참고사진 첨부", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        chks = []
        if not ref_df.empty and len(ref_df.columns) > 3:
            chks_list = sorted(list(set([str(x) for x in ref_df.iloc[:,3:].values.flatten() if x and str(x)!='nan'])))
            chks = col_ex1.multiselect("체크리스트", chks_list, key=f"ck_{idx}")
        ref_p = col_ex1.file_uploader("📸 참고사진 (저용량 보관)", type=["jpg","png","jpeg"], key=f"rp_{idx}")
        memo = col_ex2.text_area("기타 메모", key=f"me_{idx}", height=100)

    if st.button("🚀 최종 데이터 저장"):
        if not case_no: st.error("Case Number를 입력하세요.")
        else:
            p_u = 180 # 기본 단가
            if final_cl and not ref_df.empty:
                m = ref_df[ref_df.iloc[:, 1] == final_cl]
                if not m.empty: p_u = int(float(m.iloc[0, 3]))
            
            new_row = {
                "Case #": case_no, "Clinic": final_cl, "Doctor": final_doc, "Patient": patient,
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u * qty,
                "Receipt Date": rd.strftime('%Y-%m-%d'), "Status": stt, 
                "Notes": ", ".join(chks) + f" | {memo}" + (" [Photo]" if ref_p else "")
            }
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.cache_data.clear() # 저장 후 즉시 데이터 갱신
            st.success("저장 완료!")
            st.session_state.it += 1
            st.rerun()

with t2:
    st.markdown("### 📊 이번 달 정산 현황")
    if not main_df.empty:
        # 숫자형 변환 (정산 오류 방지 핵심)
        df_stat = main_df.copy()
        df_stat['Qty'] = pd.to_numeric(df_stat['Qty'], errors='coerce').fillna(0)
        df_stat['Total'] = pd.to_numeric(df_stat['Total'], errors='coerce').fillna(0)
        df_stat['RD_DT'] = pd.to_datetime(df_stat['Receipt Date'], errors='coerce')
        
        now = datetime.now()
        this_month = df_stat[(df_stat['RD_DT'].dt.year == now.year) & (df_stat['RD_DT'].dt.month == now.month)]
        
        if not this_month.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("생산 건수", f"{len(this_month)} 건")
            m2.metric("총 수량", f"{int(this_month['Qty'].sum())} ea")
            m3.metric("총 매출액", f"${int(this_month['Total'].sum()):,}")
            st.dataframe(this_month.drop(columns=['RD_DT']), use_container_width=True, hide_index=True)
        else:
            st.info("이번 달 데이터가 없습니다.")

with t3:
    st.markdown("### 🔍 전체 데이터 검색")
    q = st.text_input("검색어 입력 (번호 또는 환자명)")
    if q and not main_df.empty:
        res_df = main_df[main_df['Case #'].str.contains(q, case=False) | main_df['Patient'].str.contains(q, case=False)]
        st.dataframe(res_df, use_container_width=True, hide_index=True)
    elif not q:
        st.dataframe(main_df, use_container_width=True, hide_index=True)
