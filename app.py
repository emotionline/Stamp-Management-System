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

# ==================== 1. 로그인 화면 ====================
if not st.session_state.logged_in:
    st.title("🔖 돌봄센터 통합 도장 관리 시스템")
    
    # 화사함을 더하기 위해 이모지와 Streamlit 공식 배너 디자인 활용
    st.success("🌈 **안녕하세요! 다함께돌봄센터 관리 시스템 플랫폼입니다.** 바쁜 현장의 선생님들을 응원합니다!")
    
    st.subheader("🔑 로그인")
    with st.form("login_form"):
        input_id = st.text_input("돌봄센터 ID", placeholder="예: center__")
        input_pw = st.text_input("비밀번호", type="password")
        login_btn = st.form_submit_button("아이들을 만나러 ^^")
        
        if login_btn:
            if input_id and input_pw == "12345":
                st.session_state.logged_in = True
                st.session_state.center_id = input_id
                st.rerun()
            else:
                st.error("ID 또는 비밀번호가 틀렸습니다.")
    st.stop()

# ==================== 2. 로그인 성공 후 올인원 메인 화면 ====================
with st.sidebar:
    st.info(f"🏠 **소속:** {st.session_state.center_id}\n\n오늘도 아이들과 좋은 하루 보내세요! ❤️")
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.center_id = ""
        st.rerun()

# 메인 타이틀 구역 (따뜻하고 화사한 멘트 안내)
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
        log_reason = st.text_input("변경 사유 입력 (메모)", placeholder="예: 받아쓰기 100점, 착한 일 함")

    with col_ctrl:
        st.markdown("<br>", unsafe_allow_index=True)
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
            reason = log_reason if log_reason else "도장 1개 지급"
            save_log(st.session_state.center_id, edit_target_name, current_teacher, "증가", reason)
            st.toast(f"👍 {edit_target_name}: {new_val}")
            st.rerun()
            
        if c2.button("➖ 1개 줄이기", use_container_width=True):
            if current_num > 0:
                new_val = f"{current_num - 1} {unit}"
                supabase.table("stamps").update({"status": new_val}).eq("stamp_name", edit_target_name).eq("center_id", st.session_state.center_id).execute()
                reason = log_reason if log_reason else "도장 1개 회수/사용"
                save_log(st.session_state.center_id, edit_target_name, current_teacher, "감소", reason)
                st.toast(f"👎 {edit_target_name}: {new_val}")
                st.rerun()
            else:
                st.warning("이미 도장 개수가 0개입니다.")
                
        new_text_status = st.text_input("상태 직접 입력 (문구 입력용)", value=current_status)
        if st.button("✏️ 상태 텍스트 변경", use_container_width=True):
            supabase.table("stamps").update({"status": new_text_status}).eq("stamp_name", edit_target_name).eq("center_id", st.session_state.center_id).execute()
            reason = log_reason if log_reason else f"텍스트 변경: {new_text_status}"
            save_log(st.session_state.center_id, edit_target_name, current_teacher, "텍스트변경", reason)
            st.toast("✏️ 상태가 변경되었습니다.")
            st.rerun()

    with col_reset:
        st.markdown("<br>", unsafe_allow_index=True)
        st.markdown("<div style='text-align: center; font-weight: bold; color: #E67E22;'>🎁 칭찬 보상 완료 처리</div>", unsafe_allow_index=True)
        if st.button("🚨 보상 완료 (0개 초기화)", use_container_width=True, type="primary"):
            new_val = f"0 {unit}"
            supabase.table("stamps").update({"status": new_val}).eq("stamp_name", edit_target_name).eq("center_id", st.session_state.center_id).execute()
            reason = log_reason if log_reason else "보상 완료 및 개수 초기화"
            save_log(st.session_state.center_id, edit_target_name, current_teacher, "초기화", reason)
            st.success(f"🎁 {edit_target_name} 어린이의 도장이 0개로 초기화되었습니다!")
            st.rerun()

st.markdown("---")

# ----------------- [최하단 레이아웃] 실시간 히스토리 로그 -----------------
st.subheader("📜 센터 도장 변경 히스토리 (최근 15개 내역)")
log_df = load_logs(st.session_state.center_id)
if len(log_df) > 0:
    st.dataframe(log_df, use_container_width=True, hide_index=True)
else:
    st.info("아직 기록된 도장 변경 내역이 없습니다.")
