import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# 페이지 설정
st.set_page_config(page_title="다함께돌봄센터 통합 도장 관리 시스템", page_icon="🔖", layout="wide")

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

# --- 데이터 불러오기 함수 (아이 이름순 정렬) ---
def load_data(center_id):
    response = supabase.table("stamps").select("*").eq("center_id", center_id).order("stamp_name").execute()
    data = response.data
    if data:
        df = pd.DataFrame(data)
        df = df[["stamp_name", "owner", "reg_date", "status"]]
        df.columns = ["아이 이름", "담당 선생님", "등록일", "도장 수량 / 상태"]
        return df
    else:
        return pd.DataFrame(columns=["아이 이름", "담당 선생님", "등록일", "도장 수량 / 상태"])

# --- 히스토리 로그 불러오기 함수 ---
def load_logs(center_id):
    response = supabase.table("stamp_logs").select("*").eq("center_id", center_id).order("created_at", descending=True).limit(15).execute()
    data = response.data
    if data:
        df = pd.DataFrame(data)
        df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
        df = df[["created_at", "stamp_name", "owner", "change_type", "detail"]]
        df.columns = ["일시", "아이 이름", "선생님", "구분", "상세 메모"]
        return df
    else:
        return pd.DataFrame(columns=["일시", "아이 이름", "선생님", "구분", "상세 메모"])

# --- 로그 저장 함수 ---
def save_log(center_id, stamp_name, owner, change_type, detail):
    log_data = {
        "center_id": center_id,
        "stamp_name": stamp_name,
        "owner": owner,
        "change_type": change_type,
        "detail": detail
    }
    supabase.table("stamp_logs").insert(log_data).execute()

# ==================== 1. 로그인 및 회원가입 화면 ====================
if not st.session_state.logged_in:
    st.title("🔖 돌봄센터 통합 도장 관리 시스템")
    st.success("🌈 **안녕하세요! 다함께돌봄센터 관리 시스템 플랫폼입니다.** 바쁜 현장의 선생님들을 응원합니다!")
    
    # 로그인과 회원가입을 탭으로 분리
    tab1, tab2 = st.tabs(["🔑 로그인", "📝 새로운 돌봄센터 회원가입"])
    
    # --- [탭 1] 로그인 구역 ---
    with tab1:
        with st.form("login_form"):
            input_id = st.text_input("돌봄센터 ID", placeholder="가입하신 센터 ID를 입력하세요 (예: center34)")
            input_pw = st.text_input("비밀번호", type="password")
            login_btn = st.form_submit_button("아이들을 만나러 ^^")
            
            if login_btn:
                if input_id and input_pw:
                    # DB에서 해당 센터의 계정 정보 조회
                    user_res = supabase.table("center_users").select("*").eq("center_id", input_id).execute()
                    if user_res.data and user_res.data[0]["password"] == input_pw:
                        st.session_state.logged_in = True
                        st.session_state.center_id = input_id
                        st.rerun()
                    # 기존 맛보기 테스트용 계정 예외 처리 유지 (비밀번호: 12345)
                    elif input_pw == "12345":
                        st.session_state.logged_in = True
                        st.session_state.center_id = input_id
                        st.rerun()
                    else:
                        st.error("❌ ID 또는 비밀번호가 일치하지 않습니다.")
                else:
                    st.warning("⚠️ ID와 비밀번호를 모두 입력해 주세요.")
                    
    # --- [탭 2] 회원가입 구역 ---
    with tab2:
        st.write("우리 돌봄센터만의 전용 대시보드 계정을 생성합니다.")
        with st.form("register_center_form", clear_on_submit=True):
            reg_id = st.text_input("희망하는 돌봄센터 ID", placeholder="영문, 숫자 조합 권장 (예: dharum34)")
            reg_pw = st.text_input("접속 비밀번호 설정", type="password")
            reg_pw_confirm = st.text_input("비밀번호 확인", type="password")
            
            register_btn = st.form_submit_button("돌봄센터 계정 만들기")
            if register_btn:
                if reg_id and reg_pw and reg_pw_confirm:
                    if reg_pw != reg_pw_confirm:
                        st.error("❌ 설정한 두 비밀번호가 서로 다릅니다. 다시 확인해 주세요.")
                    else:
                        # 아이디 중복 체크
                        exist_res = supabase.table("center_users").select("center_id").eq("center_id", reg_id).execute()
                        if exist_res.data:
                            st.error("❌ 이미 존재하는 돌봄센터 ID입니다. 다른 ID를 사용해 주세요.")
                        else:
                            # DB에 새로운 돌봄센터 유저 저장
                            new_user = {
                                "center_id": reg_id,
                                "password": reg_pw
                            }
                            supabase.table("center_users").insert(new_user).execute()
                            st.success(f"🎉 '{reg_id}' 센터 계정이 성공적으로 생성되었습니다! 로그인 탭에서 로그인을 진행해 주세요.")
                else:
                    st.warning("⚠️ 모든 빈칸을 입력하셔야 회원가입이 가능합니다.")
    st.stop()

# ==================== 2. 로그인 성공 후 올인원 메인 화면 ====================
with st.sidebar:
    st.info(f"🏠 **소속:** {st.session_state.center_id}\n\n오늘도 아이들과 좋은 하루 보내세요! ❤️")
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.center_id = ""
        st.rerun()

# 메인 타이틀 구역
st.title(f"📊 {st.session_state.center_id} 통합 도장 대시보드")
st.markdown("✨ 아이들의 도장 현황 및 선생님들의 입력 히스토리를 한눈에 관리하는 안심 공간입니다.")
st.markdown("---")

df = load_data(st.session_state.center_id)

# ----------------- [상단 레이아웃] 아이 추가 및 삭제 폼 -----------------
col_add, col_del = st.columns(2)

with col_add:
    st.subheader("➕ 새로운 아이 추가")
    with st.form("add_child_form", clear_on_submit=True):
        new_name = st.text_input("아이 이름", placeholder="예: 홍길동")
        new_owner = st.text_input("담당 선생님 성함", placeholder="예: 강정선 선생님")
        new_status = st.text_input("초기 도장 개수 설정", value="0 개")
        
        add_btn = st.form_submit_button("대시보드에 추가하기")
        if add_btn:
            if new_name and new_owner:
                check_res = supabase.table("stamps").select("stamp_name").eq("stamp_name", new_name).eq("center_id", st.session_state.center_id).execute()
                if check_res.data:
                    st.error("❌ 이미 대시보드에 존재하는 아이 이름입니다.")
                else:
                    new_data = {
                        "stamp_name": new_name,
                        "owner": new_owner,
                        "reg_date": datetime.now().strftime("%Y-%m-%d"),
                        "status": new_status,
                        "center_id": st.session_state.center_id
                    }
                    supabase.table("stamps").insert(new_data).execute()
                    save_log(st.session_state.center_id, new_name, new_owner, "아이추가", f"초기 수량: {new_status}")
                    st.toast(f"🎉 '{new_name}' 어린이가 명단에 추가되었습니다!")
                    st.rerun()
            else:
                st.warning("⚠️ 모든 빈칸을 채워주세요.")

with col_del:
    st.subheader("❌ 아이 삭제")
    if len(df) > 0:
        del_target_name = st.selectbox("삭제할 아이 이름을 선택하세요", df["아이 이름"].values)
        st.write(f"선택된 아이: **{del_target_name}**")
        if st.button("🚨 명단에서 완전히 삭제"):
            supabase.table("stamps").delete().eq("stamp_name", del_target_name).eq("center_id", st.session_state.center_id).execute()
            save_log(st.session_state.center_id, del_target_name, "관리자", "아이삭제", "명단에서 제거됨")
            st.toast(f"🔥 '{del_target_name}' 어린이의 데이터가 삭제되었습니다.")
            st.rerun()
    else:
        st.info("삭제할 명단이 없습니다.")

st.markdown("---")

# ----------------- [중단 레이아웃] 가나다순 실시간 현황판 -----------------
st.subheader("📋 실시간 도장 현황판 (아이 이름순 정렬)")
if len(df) > 0:
    st.dataframe(df, use_container_width=True,
