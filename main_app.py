import streamlit as st

# -------------------------------
# 페이지 기본 설정
# -------------------------------
st.set_page_config(
    page_title="AI 기반 IEP 시스템",
    page_icon="🏠",
    layout="centered"
)

# -------------------------------
# 메인 페이지 표시 함수
# -------------------------------
def show_main_page():
    st.title("🤖 AI 기반 IEP 시스템")
    st.markdown("---")
    st.subheader("원하는 서비스를 선택하세요.")

    # 다른 페이지로 이동하는 링크 (multipage 구조)
    st.page_link("pages/1_iep_meeting.py", label="📋 협의회 회의록 작성하기", icon="➡️")
    st.page_link("pages/2_iep_planning.py", label="📄 개별화교육계획 수립하기", icon="➡️")
    st.page_link("pages/3_iep_evaluation.py", label="📝 개별화교육평가 진행하기", icon="➡️")

    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: grey;'>각 버튼을 클릭하면 해당 웹앱으로 이동합니다.</p>",
        unsafe_allow_html=True
    )

# -------------------------------
# 사용자 확인 함수 (secrets.toml 기반)
# -------------------------------
def check_user(org: str, name: str) -> bool:
    """
    .streamlit/secrets.toml 또는 Streamlit Cloud Secrets 에
    아래와 같은 형식으로 저장되어 있다고 가정한다.

    [approved_users]
    user1 = { org = "천안가온중학교", name = "신하영" }
    user2 = { org = "청양고등학교",  name = "성현준" }
    user3 = { org = "대한초등학교",  name = "김선생" }
    """

    approved_users = st.secrets.get("approved_users", None)
    if not approved_users:
        # 승인 사용자 목록이 설정되어 있지 않으면 기본적으로 차단
        return False

    org = org.strip()
    name = name.strip()

    # user1, user2, ... 값들을 순회하며 소속/이름 비교
    for _, info in approved_users.items():
        saved_org = str(info.get("org", "")).strip()
        saved_name = str(info.get("name", "")).strip()

        if org == saved_org and name == saved_name:
            return True

    return False

# -------------------------------
# 세션 상태 초기화
# -------------------------------
if "is_approved" not in st.session_state:
    st.session_state.is_approved = False

# -------------------------------
# 메인 로직
# -------------------------------
if st.session_state.is_approved:
    # 승인 완료 시: 메인 페이지 노출
    show_main_page()

else:
    # 승인 전에는 사이드바 Nav 숨기기
    st.markdown(
        """<style>[data-testid="stSidebarNav"] {display: none;}</style>""",
        unsafe_allow_html=True
    )

    st.title("🔒 사용자 확인")
    st.info("앱을 사용하려면 관리자에게 승인된 소속 기관과 이름을 입력해주세요.")

    with st.form("approval_form"):
        organization = st.text_input("소속 기관")
        name = st.text_input("이름")
        submitted = st.form_submit_button("확인")

        if submitted:
            if check_user(organization, name):
                st.session_state.is_approved = True
                st.success("확인되었습니다. 잠시 후 앱으로 이동합니다.")
                st.rerun()
            else:
                st.error("승인된 사용자가 아닙니다. 관리자에게 문의하세요.")

# -------------------------------
# (선택) 하단 저작권 표시
# -------------------------------
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        text-align: center;
        color: #888888;
        background-color: #f5f5f5;
        padding: 6px 0;
        font-size: 0.85rem;
        z-index: 100;
    }
    </style>
    <div class="footer">
        © 천안가온중학교 신하영
    </div>
    """,
    unsafe_allow_html=True
)
