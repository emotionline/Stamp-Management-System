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

# ==================== 1. 로그인 및 회원가입 화면 ====================
if not st.session_state.logged_in:
    st.title("🔖 돌봄센터 통합 도장 관리 시스템")
    st.success("🌈 **안녕하세요! 다함께돌봄센터 관리 시스템 플랫폼입니다.** 바쁜 현장의 선생님들을 응원합니다!")
    st.success("🧑‍🎄 (1) 익명 게시판 + (2) 실시간 도장 관리 원클릭 버튼 이용을 더욱 편리하게 하실 수 있도록 시스템 구축 중입니다...")
    st.success("🛫 사용하심에 불편함이 없도록, 매일 사용자가 없는 오후 10시에 시스템 업그레이드를 위한 실험을 진행합니다.")
    
    # 로그인과 회원가입을 탭으로 분리
    tab1, tab2 = st.tabs(["🔑 로그인", "📝 새로운 돌봄센터 회원가입"])
    
    # --- [탭 1] 로그인 구역 ---
    with tab1:
        with st.form("login_form"):
            input_id = st.text_input("돌봄센터 ID", placeholder="가입하신 센터 ID를 입력하세요 (예: center__)")
            input_pw = st.text_input("비밀번호", type="password")
            login_btn = st.form_submit_button("🫶")
            
            if login_btn:
                if input_id and input_pw:
                    # DB에서 해당 센터의 계정 정보 조회
                    user_res = supabase.table("center_users").select("*").eq("center_id", input_id).execute()
                    if user_res.data and user_res.data[0]["password"] == input_pw:
                        st.session_state.logged_in = True
                        st.session_state.center_id = input_id
                        st.rerun()
                    
                    # 🎁 [체험용 치트키] 외부 사람들은 오직 'demo_center' 아이디로만 1234 접속이 가능합니다!
                    elif input_id == "demo_center" and input_pw == "1234":
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
            reg_id = st.text_input("희망하는 돌봄센터 ID", placeholder="영문, 숫자 조합 권장 (예: center__)")
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
st.markdown("✨ 아이들의 도장 현황을 한눈에 관리하는 안심 공간입니다.")
st.markdown("---")

df = load_data(st.session_state.center_id)

# ----------------- [상단 레이아웃] 아이 추가 및 삭제 폼 -----------------
col_add, col_del = st.columns(2)

with col_add:
    st.subheader("➕ 새로운 아이 추가")
    with st.form("add_child_form", clear_on_submit=True):
        new_name = st.text_input("아이 이름", placeholder="예: 홍길동")
        new_owner = st.text_input("담당 선생님 성함", placeholder="예: ___ 선생님")
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
            st.toast(f"🔥 '{del_target_name}' 어린이의 데이터가 삭제되었습니다.")
            st.rerun()
    else:
        st.info("삭제할 명단이 없습니다.")

st.markdown("---")

# ----------------- [중단 레이아웃] 가나다순 실시간 현황판 -----------------
st.subheader("📋 실시간 도장 현황판 (아이 이름순 정렬)")
if len(df) > 0:
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("현재 등록된 아이들이 없습니다. 위의 추가 폼을 이용해 첫 아이를 등록해 주세요!")

st.markdown("---")

# ----------------- [하단 레이아웃] 수량 증감 / 상태 변경 / 보상 초기화 -----------------
st.subheader("🔄 간편 도장 수량 조절 및 보상 초기화")
if len(df) > 0:
    col_select, col_ctrl, col_reset = st.columns([1.5, 2, 1.5])
    
    with col_select:
        edit_target_name = st.selectbox("도장을 조절할 아이를 고르세요", df["아이 이름"].values)
        current_status = df[df["아이 이름"] == edit_target_name]["도장 수량 / 상태"].values[0]
        current_teacher = df[df["아이 이름"] == edit_target_name]["담당 선생님"].values[0]
        st.write(f"현재 보유량: **{current_status}** (담당: {current_teacher})")

    with col_ctrl:
        st.write("") 
        c1, c2 = st.columns(2)
        
        try:
            current_num = int(''.join(filter(str.isdigit, current_status)))
            unit = ''.join(filter(lambda x: not x.isdigit(), current_status)).strip()
            if not unit: unit = "개"
        except ValueError:
            current_num = 0
            unit = "개"
            
        if c1.button("➕ 1개 늘리기", use_container_width=True):
            new_val = f"{current_num + 1} {unit}"
            supabase.table("stamps").update({"status": new_val}).eq("stamp_name", edit_target_name).eq("center_id", st.session_state.center_id).execute()
            st.toast(f"👍 {edit_target_name}: {new_val}")
            st.rerun()
            
        if c2.button("➖ 1개 줄이기", use_container_width=True):
            if current_num > 0:
                new_val = f"{current_num - 1} {unit}"
                supabase.table("stamps").update({"status": new_val}).eq("stamp_name", edit_target_name).eq("center_id", st.session_state.center_id).execute()
                st.toast(f"👎 {edit_target_name}: {new_val}")
                st.rerun()
            else:
                st.warning("이미 도장 개수가 0개입니다.")
                
        new_text_status = st.text_input("상태 직접 입력 (문구 입력용)", value=current_status)
        if st.button("✏️ 상태 텍스트 변경", use_container_width=True):
            supabase.table("stamps").update({"status": new_text_status}).eq("stamp_name", edit_target_name).eq("center_id", st.session_state.center_id).execute()
            st.toast("✏️ 상태가 변경되었습니다.")
            st.rerun()

    with col_reset:
        st.write("") 
        st.write("🎁 **칭찬 보상 완료 처리**")
        if st.button("🚨 보상 완료 (0개 초기화)", use_container_width=True, type="primary"):
            new_val = f"0 {unit}"
            supabase.table("stamps").update({"status": new_val}).eq("stamp_name", edit_target_name).eq("center_id", st.session_state.center_id).execute()
            st.success(f"🎁 {edit_target_name} 어린이의 도장이 0개로 초기화되었습니다!")
            st.rerun()
