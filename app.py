import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import io

# 1. 시스템 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 25px 35px; border-radius: 12px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    .stButton>button { width: 100%; height: 3.8em; background-color: #4c6ef5 !important; color: white !important; font-weight: 800; border-radius: 8px; }
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p { color: #ffffff !important; font-weight: 600 !important; }
    </style>
    """, unsafe_allow_html=True)

# 메인 타이틀
st.markdown(f"""
    <div class="header-container">
        <div>
            <div style="font-size: 28px; font-weight: 800; color: #ffffff;"> SKYCAD Dental Lab NIGHT GUARD Manager </div>
            <div style="font-size: 14px; color: #8b949e;"> Advanced AI Dental Order Management System </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 18px; font-weight: 700; color: #4c6ef5;"> Designed by Heechul Jung </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 2. 데이터 연결 및 AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

conn = st.connection("gsheets", type=GSheetsConnection)
if "it" not in st.session_state: st.session_state.it = 0
idx = str(st.session_state.it)

def load_all_data():
    try:
        df = conn.read(ttl=0).astype(str)
        df = df[df['Case #'].str.strip() != ""].reset_index(drop=True)
        # 숫자 변환
        for col in ['Qty', 'Price', 'Total']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df
    except: return pd.DataFrame()

main_df = load_all_data()
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)

# 3. AI 분석 함수 (더 엄격한 파싱)
def run_ai_analysis(img_file):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(img_file).convert("RGB")
        img.thumbnail((500, 500))
        # 형식을 엄격하게 지정
        prompt = """Extract from dental order. 
        Reply ONLY in this format: 
        CASE: value
        PATIENT: value
        CLINIC: value
        DOCTOR: value"""
        
        response = model.generate_content([prompt, img])
        lines = response.text.split('\n')
        extracted = {}
        for line in lines:
            if ':' in line:
                k, v = line.split(':', 1)
                extracted[k.strip().upper()] = v.strip()
        return extracted
    except: return None

# 4. 탭 구성
t1, t2, t3 = st.tabs(["📝 주문 등록", "📊 실적 정산", "🔍 통합 검색"])

with t1:
    clinics = sorted(ref_df.iloc[:, 1].dropna().unique()) if not ref_df.empty else []
    doctors = sorted(ref_df.iloc[:, 2].dropna().unique()) if not ref_df.empty else []

    with st.expander("📸 의뢰서 분석 촬영", expanded=True):
        cam = st.file_uploader("사진 촬영", type=["jpg","jpeg","png"], key="ai_cam")
        if cam and st.button("✨ 데이터 추출 시작"):
            with st.spinner("AI 분석 중..."):
                res = run_ai_analysis(cam)
                if res:
                    st.session_state[f"c_{idx}"] = res.get('CASE', '')
                    st.session_state[f"p_{idx}"] = res.get('PATIENT', '')
                    if res.get('CLINIC') in clinics: st.session_state[f"cl_{idx}"] = res.get('CLINIC')
                    if res.get('DOCTOR') in doctors: st.session_state[f"doc_{idx}"] = res.get('DOCTOR')
                    st.success("데이터 추출 성공! 아래 정보를 확인하세요.")
                    st.rerun()

    st.markdown("### 📋 정보 확인 및 날짜 관리")
    col1, col2, col3 = st.columns(3)
    case_no = col1.text_input("Case Number", key=f"c_{idx}")
    patient = col1.text_input("환자명", key=f"p_{idx}")
    
    sel_cl = col2.selectbox("병원", ["선택"] + clinics + ["➕ 직접"], key=f"cl_{idx}")
    final_cl = col2.text_input("직접입력(병원)", key=f"cl_t_{idx}") if sel_cl == "➕ 직접" else (sel_cl if sel_cl != "선택" else "")
    
    sel_doc = col3.selectbox("의사", ["선택"] + doctors + ["➕ 직접"], key=f"doc_{idx}")
    final_doc = col3.text_input("직접입력(의사)", key=f"doc_t_{idx}") if sel_doc == "➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    # 날짜 및 공정 관리 섹션 (복구 완료)
    with st.expander("📅 공정 및 날짜 관리 (-2일 자동계산)", expanded=True):
        d1, d2, d3 = st.columns(3)
        receipt_date = d1.date_input("접수일", date.today(), key=f"rd_{idx}")
        # 모델 체크란 추가
        model_check = d1.checkbox("3D 모델 체크 완료", key=f"mc_{idx}")
        
        finish_date = d2.date_input("완료일 (마감일)", date.today() + timedelta(days=7), key=f"fd_{idx}")
        # 출하일 자동계산 (-2일)
        ship_date = finish_date - timedelta(days=2)
        d2.info(f"🚚 예상 출하일: {ship_date.strftime('%Y-%m-%d')} (완료 2일 전)")
        
        status = d3.selectbox("상태", ["Normal", "Hold", "Canceled", "Urgent"], key=f"st_{idx}")
        qty = d3.number_input("수량", 1, 10, 1, key=f"qy_{idx}")

    with st.expander("📂 참고사진 및 특이사항", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        chks = []
        if not ref_df.empty and len(ref_df.columns) > 3:
            chks_list = sorted(list(set([str(x) for x in ref_df.iloc[:,3:].values.flatten() if x and str(x)!='nan'])))
            chks = col_ex1.multiselect("특이사항 체크리스트", chks_list, key=f"ck_{idx}")
        
        ref_p = col_ex1.file_uploader("📸 참고사진 (저용량 보관)", type=["jpg","png","jpeg"], key=f"rp_{idx}")
        memo = col_ex2.text_area("기타 메모", key=f"me_{idx}", height=120)

    if st.button("🚀 SKYCAD 데이터베이스 최종 저장"):
        if not case_no: st.error("Case Number를 입력하세요.")
        else:
            p_u = 180
            if final_cl and not ref_df.empty:
                m = ref_df[ref_df.iloc[:, 1] == final_cl]
                if not m.empty:
                    try: p_u = int(float(m.iloc[0, 3]))
                    except: p_u = 180
            
            new_row = {
                "Case #": case_no, "Clinic": final_cl, "Doctor": final_doc, "Patient": patient,
                "Qty": qty, "Price": p_u, "Total": p_u * qty,
                "Receipt Date": receipt_date.strftime('%Y-%m-%d'),
                "3D Model Check": "완료" if model_check else "미완료",
                "Finish Date": finish_date.strftime('%Y-%m-%d'),
                "Ship Date": ship_date.strftime('%Y-%m-%d'),
                "Status": status, "Notes": ", ".join(chks) + f" | {memo}"
            }
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success(f"저장 완료! 출하일은 {ship_date}입니다.")
            st.session_state.it += 1
            st.rerun()

# 📊 정산 및 검색 탭 (전체 데이터 기반)
with t2:
    st.markdown("### 📊 정산 리포트")
    if not main_df.empty:
        valid_df = main_df[main_df['Status'].isin(['Normal', 'Urgent'])]
        t_cases = len(valid_df)
        t_qty = int(valid_df['Qty'].sum())
        t_sales = int(valid_df['Total'].sum())
        
        c1, c2, c3 = st.columns(3)
        c1.metric("총 생산 건수", f"{t_cases} 건")
        c2.metric("총 생산 수량", f"{t_qty} ea")
        c3.metric("총 매출 합계", f"${t_sales:,}")
        st.divider()
        st.dataframe(main_df, use_container_width=True, hide_index=True)

with t3:
    st.markdown("### 🔍 데이터 검색")
    q = st.text_input("검색어 입력")
    if q and not main_df.empty:
        st.dataframe(main_df[main_df['Case #'].str.contains(q, case=False) | main_df['Patient'].str.contains(q, case=False)], use_container_width=True)
