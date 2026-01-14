import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import json
import io

# 1. 페이지 설정 및 디자인 고정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    .stFileUploader section {
        background-color: #1a1c24 !important;
        border: 2px dashed #4c6ef5 !important;
        border-radius: 10px !important;
    }
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p, .stMetric p {
        color: #ffffff !important; font-weight: 600 !important;
    }
    .stButton>button {
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important;
        color: white !important; font-weight: bold !important; border-radius: 5px;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, textarea {
        background-color: #1a1c24 !important; color: #ffffff !important; border: 1px solid #4a4a4a !important;
    }
    [data-testid="stMetricValue"] { color: #4c6ef5 !important; }
    </style>
    """, unsafe_allow_html=True)

# 상단 헤더
st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;"> SKYCAD Dental Lab NIGHT GUARD Manager </div>
        <div style="text-align: right; color: #ffffff;">
            <span style="font-size: 18px; font-weight: 600;">Designed by Heechul Jung</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 2. API 및 연결 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

conn = st.connection("gsheets", type=GSheetsConnection)

if "it" not in st.session_state: st.session_state.it = 0
idx = str(st.session_state.it)

# 데이터 로드
@st.cache_data(ttl=1)
def get_data():
    try: return conn.read(ttl=0).astype(str)
    except: return pd.DataFrame()

@st.cache_data(ttl=600)
def get_ref():
    try: return conn.read(worksheet="Reference", ttl=600).astype(str)
    except: return pd.DataFrame()

main_df = get_data()
ref = get_ref()

# 3. AI 분석 함수
def run_ai_analysis(img_file):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(img_file)
        img.thumbnail((800, 800))
        prompt = "Analyze this dental lab order and extract: Case: [val], Patient: [val], Clinic: [val], Doctor: [val], Arch: [Max/Man], Material: [Type]"
        response = model.generate_content([prompt, img])
        res_text = response.text
        parsed = {}
        for line in res_text.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                parsed[k.strip().lower()] = v.strip()
        return parsed
    except: return None

# 4. 메인 탭
t1, t2, t3 = st.tabs(["📝 등록 (Register)", "📊 통계 및 정산 (Analytics)", "🔍 검색 (Search)"])

with t1:
    docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan']) if not ref.empty else []
    clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan']) if not ref.empty else []
    
    # 📸 [섹션 1] 의뢰서 AI 분석 촬영 (휘발성)
    with st.expander("📸 의뢰서 촬영 및 AI 분석", expanded=True):
        st.write("의뢰서 분석용 카메라입니다. 사진은 저장되지 않습니다.")
        cam_img = st.file_uploader("카메라 열기 (의뢰서용)", type=["jpg","jpeg","png"], key="cam_ai")
        if cam_img and st.button("✨ 데이터 추출 시작"):
            with st.spinner("AI 분석 중..."):
                res = run_ai_analysis(cam_img)
                if res:
                    if 'case' in res: st.session_state[f"c_{idx}"] = res['case']
                    if 'patient' in res: st.session_state[f"p_{idx}"] = res['patient']
                    if res.get('clinic') in clinics_list: st.session_state[f"cl_{idx}"] = res['clinic']
                    if res.get('doctor') in docs_list: st.session_state[f"doc_{idx}"] = res['doctor']
                    st.success("데이터 추출 완료!")
                    st.rerun()

    # 📋 [섹션 2] 정보 확인 및 수정
    st.markdown("### 📋 정보 확인")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key=f"c_{idx}")
    patient = c1.text_input("환자명 (Patient)", key=f"p_{idx}")
    sel_cl = c2.selectbox("병원 (Clinic)", ["선택"] + clinics_list + ["➕ 직접"], key=f"cl_{idx}")
    final_cl = c2.text_input("직접입력(병원)", key=f"cl_t_{idx}") if sel_cl == "➕ 직접" else (sel_cl if sel_cl != "선택" else "")
    sel_doc = c3.selectbox("의사 (Doctor)", ["선택"] + docs_list + ["➕ 직접"], key=f"doc_{idx}")
    final_doc = c3.text_input("직접입력(의사)", key=f"doc_t_{idx}") if sel_doc == "➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    with st.expander("⚙️ 생산 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary","Mandibular"], horizontal=True, key=f"ar_{idx}")
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key=f"ma_{idx}")
        qty = d1.number_input("수량", 1, 10, 1, key=f"qy_{idx}")
        rd = d2.date_input("접수일", date.today(), key=f"rd_{idx}")
        cp = d2.date_input("완료예정일", date.today()+timedelta(1), key=f"cp_{idx}")
        stt = d3.selectbox("상태", ["Normal","Hold","Canceled"], key=f"st_{idx}")

    # 📂 [섹션 3] 특이사항 및 참고사진 (살려낸 부분)
    with st.expander("📂 특이사항 및 참고사진 첨부", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        chks = []
        if not ref.empty and len(ref.columns) > 3:
            chks_list = sorted(list(set([str(x) for x in ref.iloc[:,3:].values.flatten() if x and str(x)!='nan' and str(x)!='Price'])))
            chks = col_ex1.multiselect("체크리스트 선택", chks_list, key=f"ck_{idx}")
        
        # 🚨 되살린 참고사진 입력창
        ref_photo = col_ex1.file_uploader("📸 참고사진 추가 (선택사항)", type=["jpg","png","jpeg"], key=f"ref_p_{idx}")
        memo = col_ex2.text_area("기타 메모", key=f"me_{idx}", height=120)

    # 🚀 최종 저장
    if st.button("🚀 데이터 시트에 최종 저장"):
        if not case_no:
            st.error("Case Number를 입력하세요.")
        else:
            p_u = 180
            if final_cl and not ref.empty:
                match = ref[ref.iloc[:, 1] == final_cl]
                if not match.empty:
                    try: p_u = int(float(match.iloc[0, 3]))
                    except: p_u = 180
            
            f_notes = ", ".join(chks) + (f" | {memo}" if memo else "")
            # 참고사진이 있으면 메모에 표시 (실제 저장은 시트 텍스트 한계로 경로/유무만 표시 가능)
            if ref_photo: f_notes += " [참고사진 첨부됨]"
            
            new_row = {
                "Case #": case_no, "Clinic": final_cl, "Doctor": final_doc, "Patient": patient, 
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u * qty,
                "Receipt Date": rd.strftime('%Y-%m-%d'), "Completed Date": cp.strftime('%Y-%m-%d'),
                "Status": stt, "Notes": f_notes
            }
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("성공적으로 저장되었습니다!")
            st.session_state.it += 1
            st.rerun()

# 📊 통계/검색 유지
with t2:
    st.markdown("### 💰 실적 요약")
    if not main_df.empty:
        today = date.today()
        pdf = main_df.copy()
        pdf['RD_DT'] = pd.to_datetime(pdf['Receipt Date'], errors='coerce')
        m_dt = pdf[(pdf['RD_DT'].dt.year == today.year) & (pdf['RD_DT'].dt.month == today.month)]
        m1, m2, m3 = st.columns(3)
        m1.metric("이번 달 건수", f"{len(m_dt)} 건")
        m2.metric("이번 달 수량", f"{pd.to_numeric(m_dt['Qty'], errors='coerce').sum():.0f} ea")
        m3.metric("매출", f"${pd.to_numeric(m_dt['Total'], errors='coerce').sum():,.0f}")
        st.dataframe(m_dt, use_container_width=True, hide_index=True)

with t3:
    st.markdown("### 🔍 데이터 검색")
    search_q = st.text_input("Case 번호 또는 환자명")
    if search_q and not main_df.empty:
        st.dataframe(main_df[main_df['Case #'].str.contains(search_q, case=False) | main_df['Patient'].str.contains(search_q, case=False)], use_container_width=True)
