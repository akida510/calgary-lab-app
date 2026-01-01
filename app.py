import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Calgary Lab Manager", layout="centered")
st.title("🦷 Calgary Lab Manager")

# 1. 보안 키 처리
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# 2. 데이터 불러오기 (캐시 완전 제거)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 제목(Header)이 몇 번째 줄에 있든 상관없이 전체를 다 읽어옵니다.
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    # 모든 칸의 앞뒤 공백 제거
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)
except Exception as e:
    st.error(f"시트 연결 실패: {e}")
    st.stop()

# 3. 탭 구성
tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    # --- 데이터 정제 ---
    # B열(Index 1)이 클리닉 열이라고 가정하고 목록을 만듭니다.
    all_rows = ref_df.values.tolist()
    
    # 클리닉 목록 (빈칸과 제목 단어 제외)
    clinics = sorted(list(set([row[1] for row in all_rows if row[1] and row[1].lower() not in ['nan', 'none', 'clinic', 'deliver']])))

    col1, col2 = st.columns(2)
    
    with col1:
        case_no = st.text_input("A: Case #")
        # 클리닉 선택
        selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + clinics)
        
        # --- 닥터 매칭 (자석 로직) ---
        doctor_options = ["클리닉을 먼저 선택하세요"]
        
        if selected_clinic != "선택하세요":
            matched_doctors = []
            for row in all_rows:
                # 선택한 클리닉 이름과 똑같은 글자가 B열(1번 인덱스)에 있다면
                if row[1] == selected_clinic:
                    doc = row[2] # 바로 옆 C열(2번 인덱스)의 글자를 가져옴
                    if doc and doc.lower() not in ['nan', 'none', 'doctor', '']:
                        matched_doctors.append(doc)
            
            doctor_options = sorted(list(set(matched_doctors)))
            if not doctor_options:
                doctor_options = ["등록된 의사 없음"]
        
        selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options)
        patient = st.text_input("D: Patient Name")

    with col2:
        date_completed = st.date_input("G: Date Completed", datetime.now())
        
        # Arch와 Material도 시트 내용에 맞게 자동 추출
        arch_opts = sorted(list(set([row[3] for row in all_rows if row[3] and row[3].lower() not in ['nan', 'none', 'arch', 'note']])))
        selected_arch = st.radio("Arch", options=arch_opts if arch_opts else ["Mand", "Max"], horizontal=True)
        
        mat_opts = sorted(list(set([row[4] for row in all_rows if row[4] and row[4].lower() not in ['nan', 'none', 'material', 'note']])))
        selected_material = st.selectbox("Material", options=mat_opts if mat_opts else ["Thermo", "Dual"])

    notes = st.text_area("F: Check List")
    
    # 저장 버튼
    if st.button("✅ 구글 시트에 저장", use_container_width=True):
        if selected_clinic == "선택하세요" or not patient or "선택하세요" in selected_doctor:
            st.warning("항목을 정확히 선택/입력해 주세요.")
        else:
            new_data = pd.DataFrame([{
                "Case #": case_no, "Clinic": selected_clinic, "Doctor": selected_doctor,
                "Patient": patient, "Arch": selected_arch, "Material": selected_material,
                "Date": date_completed.strftime('%Y-%m-%d'), "Notes": notes
            }])
            try:
                updated = pd.concat([main_df, new_data], ignore_index=True)
                conn.update(data=updated)
                st.success(f"🎉 {patient}님 저장 완료!")
                st.balloons()
            except Exception as e:
                st.error(f"저장 실패: {e}")
