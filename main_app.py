import streamlit as st

def show_main_page():
    st.title("🤖 AI 기반 IEP 시스템")
    st.markdown("---")
    st.subheader("원하는 서비스를 선택하세요.")

    st.page_link("pages/1_iep_meeting.py", label="📋 협의회 회의록 작성하기", icon="➡️")
    st.page_link("pages/2_iep_planning.py", label="📄 개별화교육계획 수립하기", icon="➡️")
    st.page_link("pages/3_iep_evaluation.py", label="📝 개별화교육평가 진행하기", icon="➡️")

    st.markdown("---")
    st.markdown("<p style='text-align: center; color: grey;'>각 버튼을 클릭하면 해당 웹앱으로 이동합니다.</p>", unsafe_allow_html=True)

def check_user(org, name):
    for user_info in st.secrets.get("approved_users", {}).values():
        if user_info.get("org", "").strip() == org.strip() and user_info.get("name", "").strip() == name.strip():
            return True
    return False

if "is_approved" not in st.session_state:
    st.session_state.is_approved = False

if not st.session_state.is_approved:
    st.set_page_config(page_title="사용자 확인", page_icon="🔒", layout="centered")
else:
    st.set_page_config(page_title="AI 기반 IEP 시스템", page_icon="🏠", layout="centered")

if st.session_state.is_approved:
    show_main_page()
else:
    st.markdown("""<style>[data-testid="stSidebarNav"] {display: none;}</style>""", unsafe_allow_html=True)
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