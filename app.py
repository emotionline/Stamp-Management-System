import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# 페이지 설정
st.set_page_config(page_title="다함께돌봄센터 통합 도장 관리 시스템", page_icon="🔖", layout="wide")

# ====================================================================
# 🖼️ [배경 화면 설정 구역] 
# 여기에 원하는 이미지 주소(끝이 .jpg, .png 등으로 끝나는 링크)를 넣으시면 배경이 바뀝니다!
# 기본값으로 화사하고 따뜻한 느낌의 아이들 일러스트/사진 주소를 넣어두었습니다.
# ====================================================================
BACKGROUND_IMAGE_URL = "https://images.unsplash.com/photo-1516627145497-ae6968895b74?auto=format&fit=crop&q=80&w=1200"

# 에러가 나지 않도록 파이썬 연산 없이 순수 문자열 매핑으로 스타일 주입
st.markdown("""
<style>
.stApp {
    background-image: linear-gradient(rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.88)), url("%s");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}
/* 다크모드 대응 및 글자 가독성을 위해 메인 텍스트 색상 고정 */
h1, h2, h3, p, span, label, .stMarkdown {
    color: #2C3E50 !important;
}
</style>
""" % BACKGROUND_IMAGE_URL, unsafe_allow_index=True)
# ====================================================================

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

# ==================== 1. 로그인 화면 ====================
if not st.session_state.logged_in:
    st.title("🔖 돌봄센터 통합 도장 관리 시스템")
    st.warning("🌈 안녕하세요! 다함께돌봄센터 관리 시스템 플랫폼입니다.")
    
    st.subheader("🔑 로그인")
    with st.form("login_form"):
        input_id = st.text_input("돌봄센터 ID", placeholder="예: center__")
        input_pw = st.text_input("비밀번호", type="password")
        login_btn = st.form_submit_button("아이들을 만나러 ^^")
        
        if login_btn:
            if input_id and input_pw == "12345":  # 임시 비밀번호 12345
                st.session_state.logged_in = True
                st.session_state.center_id = input_id
                st.rerun()
            else:
                st.error("ID 또는 비밀번호가 틀렸습니다.")
    st.stop()

# ==================== 2. 로그인 성공 후 올인원 메인 화면 ====================

with st.sidebar:
    st.info(f"🏠 소속: {st.session_state.center_id}\n\n오늘도 아이들과 좋은 하루 보내세요! ❤️")
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.center_id = ""
        st.rerun()

# 메인 타이틀
st.title(f"📊 {st.session_state.center_id} 통합 도장 대시보드")
st.write("아이들의 도장/칭찬 스탬프 현황을 한 눈에 관리하는 올인원 공간입니다.")
st.markdown("---")

# 실시간 데이터 로드
df = load_data(st.session_state.center_id)

# ----------------- [상단 레이아웃] 아이 추가 및 삭제 폼 -----------------
col_add, col_del = st.columns(2)

with col_add:
    st.subheader("➕ 새로운 아이 추가")
    with st.form("add_child_form", clear_on_submit=True):
        new_name = st.text_input("아이 이름", placeholder="예: 홍길동")
        new_owner = st.text_input("담당 선생님 성함", placeholder="예: 김선생님")
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
                    st.toast(f"🎉 '{new_name}' 어린이가 목록에 추가되었습니다!")
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

# ----------------- [하단 레이아웃] 간편 도장 수량 증감 (+/-) -----------------
st.subheader("🔄 간편 도장 수량 조절 및 상태 변경")

if len(df) > 0:
    col_select, col_ctrl = st.columns([1, 2])
    
    with col_select:
        edit_target_name = st.selectbox("도장을 조절할 아이를 고르세요", df["아이 이름"].values)
        current_status = df[df["아이 이름"] == edit_target_name]["도장 수량 / 상태"].values[0]
        st.write(f"현재 보유량: **{current_status}**")

    with col_ctrl:
        c1, c2, c3 = st.columns([1, 1, 2])
        
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
                
        with c3:
            new_text_status = st.text_input("상태 직접 입력", value=current_status, label_visibility="collapsed")
            if st.button("✏️ 상태 텍스트 변경"):
                supabase.table("stamps").update({"status": new_text_status}).eq("stamp_name", edit_target_name).eq("center_id", st.session_state.center_id).execute()
                st.toast("✏️ 상태가 변경되었습니다.")
                st.rerun()
else:
    st.info("아이를 먼저 추가하면 수량 조절 창이 활성화됩니다.")
