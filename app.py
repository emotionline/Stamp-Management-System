import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
from streamlit_option_menu import option_menu

# 페이지 설정
st.set_page_config(page_title="다함께돌봄센터 도장 관리 시스템", page_icon="🔖", layout="wide")

# --- 화사한 배경화면 및 스타일 CSS 정의 ---
BACKGROUND_IMAGE_URL = "https://images.unsplash.com/photo-1516627145497-ae6968895b74?auto=format&fit=crop&q=80&w=1200"

# f-string 충돌을 방지하기 위해 일반 문자열로 CSS 작성
css_code = """
<style>
.stApp {
    background-image: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url("#BG_URL#");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}
h1, h2, h3, p, span {
    color: #2C3E50 !important;
}
.center-promo {
    background-color: #FFEAA7;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    font-weight: bold;
    color: #D35400 !important;
    margin-bottom: 20px;
}
</style>
""".replace("#BG_URL#", BACKGROUND_IMAGE_URL)

st.markdown(css_code, unsafe_allow_index=True)

# --- Supabase 연결 설정 ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Supabase 연결 설정(Secrets)을 확인해 주세요.")
    st.stop()

# --- 로그인 세션 상태 관리 ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "center_id" not in st.session_state:
    st.session_state.center_id = ""

# --- 데이터 불러오기 함수 (로그인한 센터 데이터만 필터링) ---
def load_data(center_id):
    response = supabase.table("stamps").select("*").eq("center_id", center_id).order("stamp_id").execute()
    data = response.data
    
    if data:
        df = pd.DataFrame(data)
        df = df[["stamp_id", "stamp_name", "owner", "reg_date", "status"]]
        df.columns = ["도장 ID", "도장 이름", "소유자/담당자", "등록일", "상태"]
        return df
    else:
        return pd.DataFrame(columns=["도장 ID", "도장 이름", "소유자/담당자", "등록일", "상태"])

# ==================== 로그인 화면 ====================
if not st.session_state.logged_in:
    st.title("🔖 돌봄센터 통합 도장 관리 시스템")
    st.markdown('<div class="center-promo">🌈 안녕하세요! 다함께돌봄센터 34호점 관리 시스템 플랫폼입니다.</div>', unsafe_allow_index=True)
    
    st.subheader("🔑 로그인")
    st.write("각 돌봄센터별 지정된 계정으로 로그인해 주세요.")
    
    with st.form("login_form"):
        input_id = st.text_input("돌봄센터 ID", placeholder="예: center34")
        input_pw = st.text_input("비밀번호", type="password")
        login_btn = st.form_submit_button("로그인하기")
        
        if login_btn:
            if input_id and input_pw == "1234":  # 임시 비밀번호 1234
                st.session_state.logged_in = True
                st.session_state.center_id = input_id
                st.rerun()
            else:
                st.error("ID 또는 비밀번호가 틀렸습니다. (비밀번호 테스트용: 1234)")
    st.stop()

# ==================== 로그인 성공 후 메인 화면 ====================
with st.sidebar:
    st.markdown(f'<div class="center-promo">🏠 다함께돌봄센터 34호점<br><span style="font-size:0.8rem;">현재 접속: {st.session_state.center_id}</span></div>', unsafe_allow_index=True)
    
    selected = option_menu(
        "메인 메뉴", 
        ["도장 대시보드", "새 도장 등록", "도장 수량/상태 변경"],
        icons=["house", "plus-circle", "pencil-square"],
        menu_icon="cast", 
        default_index=0
    )
    
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.center_id = ""
        st.rerun()

# --- 1. 도장 대시보드 화면 ---
if selected == "도장 대시보드":
    st.title(f"📊 {st.session_state.center_id} 현황판")
    
    df = load_data(st.session_state.center_id)
    total_stamps = len(df)
    active_stamps = len(df[df["상태"].str.contains("사용|개", na=False)]) if total_stamps > 0 else 0
    
    col1, col2 = st.columns(2)
    col1.metric("총 등록 항목 수", f"{total_stamps} 개")
    col2.metric("활성화된 항목", f"{active_stamps} 개")
    
    st.markdown("---")
    
    if total_stamps > 0:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("현재 센터에 등록된 도장/물품이 없습니다. '새 도장 등록'을 이용해 주세요.")

# --- 2. 새 도장 등록 화면 ---
elif selected == "새 도장 등록":
    st.title("➕ 새 도장 및 물품 추가")
    
    with st.form("register_form", clear_on_submit=True):
        stamp_id = st.text_input("고유 ID (예: STAMP-001, ITEM-01)")
        stamp_name = st.text_input("이름/종류 (예: 기획팀 직인, 칭찬 스탬프)")
        owner = st.text_input("담당 선생님 / 소유자")
        status = st.text_input("초기 상태 또는 수량 입력", value="1 개")
        
        submit_btn = st.form_submit_button("등록하기")
        
        if submit_btn:
            if stamp_id and stamp_name and owner:
                check_res = supabase.table("stamps").select("stamp_id").eq("stamp_id", stamp_id).eq("center_id", st.session_state.center_id).execute()
                if check_res.data:
                    st.error("이미 존재하는 고유 ID입니다.")
                else:
                    new_stamp = {
                        "stamp_id": stamp_id,
                        "stamp_name": stamp_name,
                        "owner": owner,
                        "reg_date": datetime.now().strftime("%Y-%m-%d"),
                        "status": status,
                        "center_id": st.session_state.center_id
                    }
                    supabase.table("stamps").insert(new_stamp).execute()
                    st.success(f"'{stamp_name}'이(가) 안전하게 등록되었습니다!")
            else:
                st.warning("모든 항목을 입력해 주세요.")

# --- 3. 도장 수량/상태 변경 화면 (+/- 버튼 기능) ---
elif selected == "도장 수량/상태 변경":
    st.title("🔄 간편 수량 및 상태 조절 (+/-)")
    
    df = load_data(st.session_state.center_id)
    
    if len(df) > 0:
        selected_id = st.selectbox("조절할 항목을 선택하세요", df["도장 ID"].values)
        current_status = df[df["도장 ID"] == selected_id]["상태"].values[0]
        
        st.write(f"현재 상태/수량: **{current_status}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔢 수량 퀵 증감 (+/-)")
            c1, c2 = st.columns(2)
            
            try:
                current_num = int(''.join(filter(str.isdigit, current_status)))
                unit = ''.join(filter(lambda x: not x.isdigit(), current_status)).strip()
            except ValueError:
                current_num = 0
                unit = "개"
                
            if c1.button("➕ 1 올리기"):
                new_val = f"{current_num + 1} {unit}"
                supabase.table("stamps").update({"status": new_val}).eq("stamp_id", selected_id).eq("center_id", st.session_state.center_id).execute()
                st.success(f"수량이 {new_val}(으)로 증가했습니다!")
                st.rerun()
                
            if c2.button("➖ 1 줄이기"):
                if current_num > 0:
                    new_val = f"{current_num - 1} {unit}"
                    supabase.table("stamps").update({"status": new_val}).eq("stamp_id", selected_id).eq("center_id", st.session_state.center_id).execute()
                    st.success(f"수량이 {new_val}(으)로 감소했습니다!")
                    st.rerun()
                else:
                    st.warning("이미 수량이 0입니다.")
                    
        with col2:
            st.markdown("### ✍️ 텍스트 상태 직접 변경")
            new_text_status = st.text_input("직접 입력 (예: 사용 중, 분실, 보관 중)", value=current_status)
            if st.button("상태 텍스트 업데이트"):
                supabase.table("stamps").update({"status": new_text_status}).eq("stamp_id", selected_id).eq("center_id", st.session_state.center_id).execute()
                st.success("텍스트 상태가 변경되었습니다.")
                st.rerun()
    else:
        st.info("등록된 항목이 없습니다.")
