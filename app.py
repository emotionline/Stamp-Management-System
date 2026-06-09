import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
from streamlit_option_menu import option_menu

# 페이지 설정
st.set_page_config(page_title="도장 관리 시스템", page_icon="🔖", layout="wide")

# --- Supabase 연결 설정 ---
# 로컬(`.streamlit/secrets.toml`) 또는 웹 배포 환경의 Secrets에서 환경변수를 읽어옵니다.
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Supabase 연결 설정(Secrets)을 확인해 주세요.")
    st.stop()

# --- 데이터 불러오기 함수 ---
def load_data():
    # 'stamps' 테이블의 모든 데이터 조회 (도장 ID 순으로 정렬)
    response = supabase.table("stamps").select("*").order("stamp_id").execute()
    data = response.data
    
    if data:
        df = pd.DataFrame(data)
        # 컬럼 순서 맞추기 및 한글 매핑
        df = df[["stamp_id", "stamp_name", "owner", "reg_date", "status"]]
        df.columns = ["도장 ID", "도장 이름", "소유자/담당자", "등록일", "상태"]
        return df
    else:
        return pd.DataFrame(columns=["도장 ID", "도장 이름", "소유자/담당자", "등록일", "상태"])

# --- 사이드바 메뉴 ---
with st.sidebar:
    selected = option_menu(
        "메인 메뉴", 
        ["도장 대시보드", "새 도장 등록", "도장 상태 변경"],
        icons=["house", "plus-circle", "pencil-square"],
        menu_icon="cast", 
        default_index=0
    )

# --- 1. 도장 대시보드 화면 ---
if selected == "도장 대시보드":
    st.title("🔖 도장 관리 대시보드")
    st.write("클라우드 데이터베이스(Supabase)와 실시간 연동된 현황입니다.")
    
    df = load_data()
    total_stamps = len(df)
    active_stamps = len(df[df["상태"] == "사용 중"]) if total_stamps > 0 else 0
    
    col1, col2 = st.columns(2)
    col1.metric("총 등록 도장 수", f"{total_stamps} 개")
    col2.metric("현재 사용 중", f"{active_stamps} 개")
    
    st.markdown("---")
    
    if total_stamps > 0:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("등록된 도장이 없습니다. '새 도장 등록' 메뉴에서 도장을 추가해 주세요.")

# --- 2. 새 도장 등록 화면 ---
elif selected == "새 도장 등록":
    st.title("➕ 새 도장 등록")
    
    with st.form("register_form", clear_on_submit=True):
        stamp_id = st.text_input("도장 고유 ID (예: STAMP-001)")
        stamp_name = st.text_input("도장 이름/종류 (예: 법인인감)")
        owner = st.text_input("담당자 / 소유자")
        status = st.selectbox("초기 상태", ["사용 중", "보관 중", "폐기/분실"])
        
        submit_btn = st.form_submit_button("도장 등록하기")
        
        if submit_btn:
            if stamp_id and stamp_name and owner:
                # 중복 ID 체크
                check_res = supabase.table("stamps").select("stamp_id").eq("stamp_id", stamp_id).execute()
                if check_res.data:
                    st.error("이미 존재하는 도장 ID입니다.")
                else:
                    # Supabase에 데이터 삽입
                    reg_date = datetime.now().strftime("%Y-%m-%d")
                    new_stamp = {
                        "stamp_id": stamp_id,
                        "stamp_name": stamp_name,
                        "owner": owner,
                        "reg_date": reg_date,
                        "status": status
                    }
                    supabase.table("stamps").insert(new_stamp).execute()
                    st.success(f"'{stamp_name}' 도장이 Supabase DB에 성공적으로 저장되었습니다!")
            else:
                st.warning("모든 필드를 입력해 주세요.")

# --- 3. 도장 상태 변경 화면 ---
elif selected == "도장 상태 변경":
    st.title("🔄 도장 상태 관리")
    
    df = load_data()
    
    if len(df) > 0:
        selected_id = st.selectbox("상태를 변경할 도장 ID를 선택하세요", df["도장 ID"].values)
        current_status = df[df["도장 ID"] == selected_id]["상태"].values[0]
        
        st.info(f"선택한 도장의 현재 상태: **{current_status}**")
        
        new_status = st.selectbox("변경할 상태 선택", ["사용 중", "보관 중", "폐기/분실"])
        update_btn = st.button("상태 업데이트")
        
        if update_btn:
            # Supabase 데이터 업데이트
            supabase.table("stamps").update({"status": new_status}).eq("stamp_id", selected_id).execute()
            st.success(f"도장 ID [{selected_id}]의 상태가 '{new_status}'로 변경되었습니다.")
    else:
        st.info("등록된 도장이 없어 상태를 변경할 수 없습니다.")
