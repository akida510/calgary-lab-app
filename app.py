import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import io

# 1. 디자인 및 테마 고정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; }
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;"> SKYCAD Dental Lab NIGHT GUARD Manager </div>
        <div style="text-align: right; color: #ffffff;"><span style="font-size: 14px;">Designed by Heechul Jung</span></div>
    </div>
    """, unsafe_allow_html=True)

# 2. 연결 및 AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
conn = st.connection("gsheets", type=GSheetsConnection)

if "it" not in st.session_state: st.session_state.it = 0
idx = str(st.session_state.it)

# 3. 데이터 로딩 (전체 데이터 강제 로드 및 숫자 변환)
def load_and_clean_data():
    try:
        # 캐시 무시하고 최신 데이터 긁어오기
        df = conn.read(ttl=0).astype(str)
        df = df[df['Case #'].str.strip() != ""].reset_index(drop=True)
        
        # [핵심] 정산 계산을 위한 숫자 강제 변환
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0).astype(int)
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0).astype(int)
        df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0).astype(int)
        
        # 날짜 형식 표준화
        df['RD_DT'] = pd.to_datetime(df['Receipt Date'], errors='coerce')
        return df
    except:
        return pd.DataFrame()

main_df = load_and_clean_data()
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)

# 4. 분석 함수
def run_ai(img_file):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(img_file).convert("RGB")
        img.thumbnail((500, 500))
        prompt = "Extract from dental order: Case Number, Patient Name, Clinic Name, Doctor Name. Just values."
        response = model.generate_content([prompt, img])
        return response.text.strip().split('\n')
    except: return None

# 5. 메인 화면
t1, t2, t3 = st.tabs(["📝 등록", "📊 정산 현황", "🔍 검색"])

with t1:
    clinics = sorted(ref_df.iloc[:, 1].dropna().unique()) if not ref_df.empty else []
    doctors = sorted(ref_df.iloc[:, 2].dropna().unique()) if not ref_df.empty else []

    with st.expander("📸 의뢰서 분석 (촬영 후 1초 대기)", expanded=True):
        cam = st.file_uploader("사진 찍기", type=["jpg","jpeg","png"])
        if cam and st.button("✨ 데이터 분석"):
            with st.spinner("AI가 읽는 중..."):
                res = run_ai(cam)
                # 세션 저장 로직 (생략 - 기존과 동일)
                st.success("분석 완료!")

    # 입력 폼
    st.markdown("### 📋 정보 확인")
    col1, col2, col3 = st.columns(3)
    case_no = col1.text_input("Case Number", key=f"c_{idx}")
    patient = col1.text_input("환자명", key=f"p_{idx}")
    sel_cl = col2.selectbox("병원", ["선택"] + clinics + ["➕ 직접"], key=f"cl_{idx}")
    final_cl = col2.text_input("직접입력(병원)", key=f"cl_t_{idx}") if sel_cl == "➕ 직접" else (sel_cl if sel_cl != "선택" else "")
    sel_doc = col3.selectbox("의사", ["선택"] + doctors + ["➕ 직접"], key=f"doc_{idx}")
    final_doc = col3.text_input("직접입력(의사)", key=f"doc_t_{idx}") if sel_doc == "➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    with st.expander("⚙️ 생산 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary", "Mandibular"], horizontal=True, key=f"ar_{idx}")
        mat = d1.selectbox("Material", ["Thermo", "Dual", "Soft", "Hard"], key=f"ma_{idx}")
        qty = d1.number_input("수량", 1, 10, 1, key=f"qy_{idx}")
        rd = d2.date_input("접수일", date.today(), key=f"rd_{idx}")
        stt = d3.selectbox("상태", ["Normal", "Hold", "Canceled"], key=f"st_{idx}")

    with st.expander("📂 참고사진 첨부", expanded=True):
        ref_p = st.file_uploader("📸 참고사진", type=["jpg","png","jpeg"], key=f"rp_{idx}")
        memo = st.text_area("메모", key=f"me_{idx}")

    if st.button("🚀 데이터 저장"):
        if not case_no: st.error("번호 입력 필수")
        else:
            p_u = 180
            if final_cl and not ref_df.empty:
                m = ref_df[ref_df.iloc[:, 1] == final_cl]
                if not m.empty: p_u = int(float(m.iloc[0, 3]))
            
            new_row = {
                "Case #": case_no, "Clinic": final_cl, "Doctor": final_doc, "Patient": patient,
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u * qty,
                "Receipt Date": rd.strftime('%Y-%m-%d'), "Status": stt, "Notes": memo + (" [P]" if ref_p else "")
            }
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("저장 완료!")
            st.session_state.it += 1
            st.rerun()

# 📊 [중요] 정산 탭 - 계산 로직 전면 수정
with t2:
    st.markdown("### 📊 이번 달 실적 리포트")
    if not main_df.empty:
        # 이번 달 데이터 필터링 (Status가 Normal인 것만 계산)
        now = datetime.now()
        cur_month_df = main_df[
            (main_df['RD_DT'].dt.year == now.year) & 
            (main_df['RD_DT'].dt.month == now.month) &
            (main_df['Status'] == 'Normal')
        ]
        
        total_cases = len(cur_month_df)
        total_qty = int(cur_month_df['Qty'].sum())
        total_sales = int(cur_month_df['Total'].sum())
        # 320개 기준 부족 수량
        shortage = max(0, 320 - total_qty)

        # 상단 대시보드
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("총 생산 건수", f"{total_cases} 건")
        m2.metric("총 생산 수량", f"{total_qty} ea")
        m3.metric("부족 수량(320기준)", f"{shortage} ea", delta=f"-{shortage}" if shortage > 0 else "목표달성", delta_color="inverse")
        m4.metric("이번 달 매출합", f"${total_sales:,}")

        st.divider()
        st.markdown("#### 📋 상세 내역 (전체)")
        # 정산에 필요한 열만 깔끔하게 표시
        st.dataframe(
            main_df[["Case #", "Clinic", "Patient", "Material", "Qty", "Total", "Receipt Date", "Status"]],
            use_container_width=True, hide_index=True
        )
    else:
        st.info("데이터가 없습니다.")

with t3:
    st.markdown("### 🔍 검색")
    q = st.text_input("검색 (번호/환자)")
    if q and not main_df.empty:
        st.dataframe(main_df[main_df['Case #'].str.contains(q, case=False) | main_df['Patient'].str.contains(q, case=False)], use_container_width=True)
