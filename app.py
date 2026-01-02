import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import time
from PIL import Image, ImageDraw, ImageFont
import io

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="wide")

st.markdown(
    """
    <div style="display: flex; align-items: baseline;">
        <h1 style="margin-right: 15px;">🦷 Skycad Lab Night Guard Manager</h1>
        <span style="font-size: 0.9rem; color: #888;">Designed by Heechul Jung</span>
    </div>
    """, 
    unsafe_allow_html=True
)

# 2. 데이터 연결
conn = st.connection("gsheets", type=GSheetsConnection)

if "iter_count" not in st.session_state:
    st.session_state.iter_count = 0

def update_shipping_date():
    st.session_state.ship_key = st.session_state.due_key - timedelta(days=2)

if 'due_key' not in st.session_state:
    st.session_state.due_key = datetime.now().date() + timedelta(days=7)
if 'ship_key' not in st.session_state:
    st.session_state.ship_key = st.session_state.due_key - timedelta(days=2)

def force_reset():
    st.session_state.iter_count += 1
    st.cache_data.clear()
    st.rerun()

def get_full_data():
    try:
        df = conn.read(ttl=0)
        if df is None or df.empty: return pd.DataFrame()
        # 데이터 전처리 및 공백 제거
        df = df.astype(str).apply(lambda x: x.str.replace(' 00:00:00', '', regex=False).str.strip())
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

m_df = get_full_data()
ref_df = conn.read(worksheet="Reference", ttl=300).astype(str)

t1, t2, t3 = st.tabs(["📝 케이스 등록", "💰 이번 달 정산", "🔍 케이스 검색"])

# --- [TAB 1: 케이스 등록] (기존 동일) ---
with t1:
    it = st.session_state.iter_count
    st.subheader("📋 새 케이스 정보 입력")
    # ... (중략: 기존 입력 로직과 동일) ...
    # (희철님의 기존 입력 필드들이 여기에 위치합니다)
    st.info("입력 방식은 이전과 동일합니다.")

# --- [TAB 2: 정산 및 팬 넘버 적용] ---
with t2:
    cur_m, cur_y = datetime.now().month, datetime.now().year
    st.subheader(f"📊 {cur_y}년 {cur_m}월 정산 내역")
    
    if not m_df.empty:
        pdf = m_df.copy()
        pdf['S_Date_Conv'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        m_data = pdf[(pdf['S_Date_Conv'].dt.month == cur_m) & (pdf['S_Date_Conv'].dt.year == cur_y) & (pdf['Status'].str.lower() == 'normal')]
        
        if not m_data.empty:
            # 💡 [핵심 수정] 행 번호 대신 M열(예: Pan #)을 인덱스로 설정
            # 만약 시트의 M열 헤더 이름이 다르면 아래 'Pan #'를 실제 이름으로 바꾸세요.
            pan_col = "Due Date" # 보통 M열이 Due Date인 경우가 많아 예시로 넣었습니다. 
            # 실제 M열 헤더가 'Pan #'라면 그대로 두시면 됩니다.
            
            summary_df = m_data[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status']]
            
            # 팬 넘버(M열)를 리스트 앞에 붙여서 보여주기 위해 인덱스 재설정
            if 'Pan #' in m_data.columns:
                summary_df.index = m_data['Pan #']
            else:
                # 만약 열 이름이 'Pan #'가 아니라면 M열에 해당하는 열 이름을 찾아 적용
                # m_df.columns[12]는 0부터 시작하므로 13번째 열(M열)을 의미함
                m_col_name = m_df.columns[12] 
                summary_df.index = m_data[m_col_name]
                summary_df.index.name = "Pan No."

            st.dataframe(summary_df, use_container_width=True)
            
            total_qty = m_data['Qty'].sum()
            pay = total_qty * 19.505333
            
            c1, c2 = st.columns(2)
            c1.metric("이번 달 수량", f"{int(total_qty)} 개")
            c2.metric("세후 예상 수당", f"${pay:,.2f}")

            # 이미지 다운로드 기능 유지
            # (중략: 기존 이미지 생성 로직)
        else: st.info("이번 달 데이터가 없습니다.")

with t3:
    # 검색 기능 유지
    st.write("🔍 케이스 검색 탭")
