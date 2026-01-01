import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json

st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# --- 구글 시트 연결 시도 ---
try:
    # Secrets 값을 읽어와서 private_key의 줄바꿈을 코드로 강제 보정
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        # 혹시 모를 줄바꿈 에러를 방지하기 위한 내부 처리
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 데이터 불러오기
        df = conn.read(ttl=0)
        ref_df = conn.read(worksheet="Reference", ttl=0)
        st.success("✅ 연결 성공! 시트 데이터를 불러왔습니다.")
    else:
        st.error("❌ Secrets 설정이 누락되었습니다.")
except Exception as e:
    st.error("🔑 보안 키(Secrets) 형식 오류가 발생했습니다.")
    st.info("private_key를 한 줄로 합치고 줄바꿈 자리에 \\n을 넣었는지 확인해 주세요.")
    st.exception(e) # 구체적인 에러 내용을 화면에 표시
