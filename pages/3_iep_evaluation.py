import streamlit as st
import google.generativeai as genai
from datetime import datetime
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# API 키 및 모델 설정
if 'user_api_key' in st.session_state and st.session_state.user_api_key:
    genai.configure(api_key=st.session_state.user_api_key)
else:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    except Exception as e:
        st.error("Gemini API 키가 설정되지 않았습니다.")
        st.stop()

# 유효한 모델 이름으로 설정
model = genai.GenerativeModel('gemini-2.0-flash')

st.set_page_config(
    page_title="AI 기반 개별화교육평가",
    page_icon="📝",
    layout="wide"
)

# --- ✨ [수정된 부분 1] 콜백 함수 정의 ---
# 버튼을 클릭했을 때 실행될 함수를 미리 정의합니다.
def generate_focus_callback(month, goal, content):
    if not goal or not content:
        st.error("평가초점을 생성하려면 먼저 교육 목표와 교육 내용을 입력해주세요.")
        return

    prompt_focus = f"""
    당신은 특수교육 IEP 전문가입니다.
    다음 교육 목표와 교육 내용을 바탕으로, 학생의 성취 수준을 구체적으로 관찰하고 평가할 수 있는 '평가 초점'을 4~5가지 제안해주세요.
    각 초점은 줄바꿈으로 구분하여 간결한 문장 형태로 작성해주세요.
    '~할 수 있는가?'와 같은 의문문으로 작성해주세요.

    - 교육 목표: {goal}
    - 교육 내용: {content}
    """
    with st.spinner(f"{month} 평가초점을 생성하는 중..."):
        try:
            response = model.generate_content(prompt_focus)
            # session_state 값을 업데이트합니다.
            st.session_state[f"eval_focus_{month}"] = response.text
        except Exception as e:
            st.error(f"AI 생성 중 오류가 발생했습니다: {e}")


st.title("📝 AI 기반 개별화교육평가")
st.markdown("---")
st.info("IEP에 수립된 월별 교육 목표, 내용, 평가초점을 붙여넣고 평가를 진행하세요.")

if 'evaluations_ai' not in st.session_state:
    st.session_state.evaluations_ai = {}
if 'semester_evaluation' not in st.session_state:
    st.session_state.semester_evaluation = {}

with st.container(border=True):
    st.subheader("🗓️ 월별 교육 목표 입력 및 평가")
    semester = st.radio("평가 대상 학기 선택", ["1학기", "2학기"], horizontal=True, key="semester_radio_eval")
    months = {"1학기": ["3월", "4월", "5월", "6월", "7월"], "2학기": ["8월", "9월", "10월", "11월", "12월"]}[semester]
    
    for month in months:
        with st.container(border=True):
            st.subheader(f"✅ {month} 평가")
            
            goal_text = st.text_area(f"{month} 교육 목표", key=f"goal_{month}", height=100)
            instructional_text = st.text_area(f"{month} 교육 내용", key=f"instructional_{month}", height=150)
            
            col1, col2 = st.columns([4, 1])

            with col1:
                eval_focus_text = st.text_area(f"{month} 평가초점 (줄바꿈으로 항목 구분)", key=f"eval_focus_{month}", height=100)

            with col2:
                st.write("") 
                st.write("")
                # --- ✨ [수정된 부분 2] on_click을 사용하도록 버튼 코드 변경 ---
                st.button(
                    f"✨ {month} 평가초점 생성",
                    key=f"btn_gen_focus_{month}",
                    on_click=generate_focus_callback,
                    args=(month, goal_text, instructional_text) # 콜백 함수에 전달할 인자들
                )
            
            eval_focus_items = [item.strip() for item in eval_focus_text.split('\n') if item.strip()]

            if eval_focus_items:
                st.markdown("---")
                st.markdown("#### 각 항목별 성취도 평가")
                for i, item in enumerate(eval_focus_items):
                    st.markdown(f"**- {item}**")
                    rating_options = ["도움 없이 스스로 과제를 완수해요.", "한두 번의 언어적, 신체적 도움을 받으면 과제를 완수해요.", "과제의 일부 단계를 도와주면 완수해요.", "과제의 대부분 단계를 도와주어야 완수해요.", "교사의 완전한 도움을 통해서만 과제 수행이 가능해요."]
                    st.radio("성취도 평가", rating_options, key=f"rating_{month}_{i}", label_visibility="collapsed", horizontal=True)
            
            if st.button(f"🧠 {month} 평가 문구 생성", key=f"btn_ai_{month}"):
                if not goal_text or not eval_focus_text:
                    st.error("교육 목표와 평가초점을 모두 입력해주세요.")
                else:
                    full_evaluation_data = ""
                    for i, item in enumerate(eval_focus_items):
                        rating_value = st.session_state.get(f"rating_{month}_{i}", "평가되지 않음")
                        full_evaluation_data += f"- 평가 초점: {item}\n- 성취도: {rating_value}\n"
                    
                    prompt = f"""
                    당신은 IEP 평가 전문가입니다.
                    다음 자료를 바탕으로 학생의 전반적인 성취에 대해 하나의 유기적인 문단으로 작성해 주세요.
                    '독립적 수행' 등의 직접적인 용어는 피하고, 평가초점별 성취 수준을 종합하여 자연스럽게 서술하세요.

                    - 교육 목표: {goal_text}
                    - 교육 내용: {instructional_text}
                    - 평가초점별 성취도:
                    {full_evaluation_data}
                    """
                    with st.spinner(f"AI가 {month} 종합 평가를 생성하고 있습니다..."):
                        response = model.generate_content(prompt)
                        st.session_state.evaluations_ai[month] = {
                            "goal": goal_text,
                            "instructional": instructional_text,
                            "eval_focus": eval_focus_text,
                            "evaluation": response.text
                        }
                    st.success(f"✔️ {month} 평가 문구 생성이 완료되었습니다!")

            if st.session_state.evaluations_ai.get(month):
                st.session_state.evaluations_ai[month]["evaluation"] = st.text_area(
                    f"{month} AI 제안 평가 문구 (수정 가능)",
                    value=st.session_state.evaluations_ai[month]["evaluation"],
                    key=f"ai_edit_{month}",
                    height=200
                )

# (이하 코드는 이전과 동일)
st.markdown("---")
st.subheader("🎓 학기 종합 평가")
if st.button("🧠 학기 종합 평가 생성", key="btn_semester_eval"):
    monthly_evals = {m: st.session_state.evaluations_ai[m] for m in months if m in st.session_state.evaluations_ai}
    if not monthly_evals:
        st.error("먼저 1개 이상의 월별 평가를 생성해주세요.")
    else:
        full_semester_data = "\n\n".join([f"**{m} 평가:**\n- 목표: {d['goal']}\n- 평가: {d['evaluation']}" for m, d in monthly_evals.items()])
        prompt = f"당신은 IEP 평가 전문가입니다. 다음 월별 평가 내용을 바탕으로 학생의 학기 전반적인 성취(강점, 보완점, 향후 지도 방향 포함)에 대해 종합적으로 기술해 주세요.\n\n{full_semester_data}"
        with st.spinner("AI가 학기 종합 평가를 생성하고 있습니다..."):
            st.session_state.semester_evaluation[semester] = model.generate_content(prompt).text
        st.success("✔️ 학기 종합 평가가 생성되었습니다!")

if st.session_state.semester_evaluation.get(semester):
    st.session_state.semester_evaluation[semester] = st.text_area(
        f"{semester} 종합 평가 (수정 가능)",
        value=st.session_state.semester_evaluation[semester],
        key=f"semester_eval_editor",
        height=300
    )

st.markdown("---")
st.subheader("📥 평가 결과 워드 파일로 저장")
if st.button("📄 평가 문서(Word) 생성 및 다운로드", key="btn_download_eval"):
    with st.spinner("평가 Word 문서를 생성 중입니다..."):
        document = Document()
        style = document.styles['Normal']
        style.font.name = '맑은 고딕'
        style.font.size = Pt(11)
        
        title = document.add_heading('개별화교육평가', level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        document.add_paragraph(f"작성일: {datetime.now().strftime('%Y년 %m월 %d일')}\n")
        
        for month in months:
            if month in st.session_state.evaluations_ai:
                data = st.session_state.evaluations_ai[month]
                document.add_heading(f"{month} 평가", level=2)
                document.add_paragraph(f"▪︎ 교육 목표: {data['goal']}")
                document.add_paragraph(f"▪︎ 주요 교육 내용:\n{data['instructional']}")
                if data.get('eval_focus'):
                    document.add_paragraph(f"▪︎ 평가 초점:\n{data['eval_focus']}")
                document.add_paragraph(f"▪︎ 종합 평가: {data['evaluation']}\n")
        
        if semester in st.session_state.semester_evaluation:
            document.add_heading(f"{semester} 종합 평가", level=1)
            document.add_paragraph(st.session_state.semester_evaluation[semester])

        file_stream = io.BytesIO()
        document.save(file_stream)
        file_stream.seek(0)
        
        st.success("✅ 평가 문서 생성이 완료되었습니다.")
        st.download_button(
            label="📥 Word 파일 다운로드",
            data=file_stream,
            file_name=f"개별화교육평가_{datetime.now().strftime('%Y%m%d')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
# --- 저작권 표시 ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>Copyright © 2025 신하영(천안가온중학교), 성현준(청양고등학교). All Rights Reserved.</p>", unsafe_allow_html=True)