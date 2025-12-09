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

# --- ✨ 평가초점 생성 콜백 함수 ---
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

# ★ 수정: 평가 척도 옵션 + 점수 매핑(1=독립, 5=완전 도움)
RATING_OPTIONS = [
    "도움 없이 스스로 과제를 완수해요.",                          # 1점(높은 성취)
    "한두 번의 언어적, 신체적 도움을 받으면 과제를 완수해요.",      # 2점
    "과제의 일부 단계를 도와주면 완수해요.",                        # 3점
    "과제의 대부분 단계를 도와주어야 완수해요.",                    # 4점
    "교사의 완전한 도움을 통해서만 과제 수행이 가능해요."           # 5점(낮은 성취)
]

RATING_SCORE_MAP = {
    RATING_OPTIONS[0]: 1,
    RATING_OPTIONS[1]: 2,
    RATING_OPTIONS[2]: 3,
    RATING_OPTIONS[3]: 4,
    RATING_OPTIONS[4]: 5,
}

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
                eval_focus_text = st.text_area(
                    f"{month} 평가초점 (줄바꿈으로 항목 구분)", 
                    key=f"eval_focus_{month}", 
                    height=100
                )

            with col2:
                st.write("") 
                st.write("")
                st.button(
                    f"✨ {month} 평가초점 생성",
                    key=f"btn_gen_focus_{month}",
                    on_click=generate_focus_callback,
                    args=(month, goal_text, instructional_text)
                )
            
            eval_focus_items = [item.strip() for item in eval_focus_text.split('\n') if item.strip()]

            if eval_focus_items:
                st.markdown("---")
                st.markdown("#### 각 항목별 성취도 평가")
                for i, item in enumerate(eval_focus_items):
                    st.markdown(f"**- {item}**")
                    # ★ 수정: 공통 RATING_OPTIONS 사용
                    st.radio(
                        "성취도 평가",
                        RATING_OPTIONS,
                        key=f"rating_{month}_{i}",
                        label_visibility="collapsed",
                        horizontal=True
                    )
            
            if st.button(f"🧠 {month} 평가 문구 생성", key=f"btn_ai_{month}"):
                if not goal_text or not eval_focus_text:
                    st.error("교육 목표와 평가초점을 모두 입력해주세요.")
                else:
                    full_evaluation_data = ""
                    scores_for_stats = []

                    for i, item in enumerate(eval_focus_items):
                        rating_label = st.session_state.get(f"rating_{month}_{i}", "평가되지 않음")
                        score = RATING_SCORE_MAP.get(rating_label, None)

                        if score is not None:
                            scores_for_stats.append(score)
                            score_text = f"{score}점"
                        else:
                            score_text = "평가되지 않음"

                        # ★ 수정: 라벨 + 점수 모두 전달
                        full_evaluation_data += (
                            f"- 평가 초점: {item}\n"
                            f"  · 성취도 문장: {rating_label}\n"
                            f"  · 성취도 점수: {score_text}\n"
                        )

                    # ★ 수정: 점수 해석 규칙을 프롬프트에 명시
                    prompt = f"""
                    당신은 특수교육 개별화교육계획(IEP) 평가 전문가입니다.
                    아래 자료를 바탕으로 학생의 전반적인 성취를 하나의 유기적인 문단으로 작성하세요.

                    [성취도 척도 설명]
                    - 성취도 점수는 1~5점입니다.
                    - 1점에 가까울수록 독립적으로 과제를 수행하는 수준이 높음을 의미합니다.
                    - 5점에 가까울수록 교사의 많은 도움을 필요로 하며, 목표 성취 수준이 낮음을 의미합니다.

                    [작성 규칙]
                    1. 평가초점별 점수를 면밀히 반영하여, 점수가 4~5점인 항목이 많은 경우
                       전반적으로 목표 달성이 어렵고 상당한 지원이 필요하다는 점을 분명하게 서술하세요.
                    2. 점수가 1~2점인 항목이 있으면 해당 강점은 간단히 언급하되,
                       전체적으로 3~5점이 많다면 '전반적으로 어려움이 크다'는 메시지가 우선 전달되도록 작성하세요.
                    3. 실제 점수 분포에 비해 과도하게 긍정적인 표현
                       (예: '전반적으로 매우 우수하다', '대부분 독립적으로 수행한다' 등)은 사용하지 마세요.
                    4. 마지막 1~2문장은 '앞으로 ~ 지원이 필요합니다.', '~에 대한 반복 연습이 요구됩니다.',
                       '~에 대한 환경 조정이 필요합니다.'처럼 구체적인 교육적 지원과 향후 지도 방향을 제시하세요.
                    5. '독립적 수행'이라는 표현은 직접 쓰지 말고,
                       '~을 스스로 수행하는 모습이 많다/드물다'처럼 자연스러운 서술형 문장으로 표현하세요.

                    [학생 정보]
                    - 교육 목표: {goal_text}
                    - 교육 내용: {instructional_text}
                    - 평가초점별 성취도(문장 + 점수):
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

# ---------------- 학기 종합 평가 ----------------
st.markdown("---")
st.subheader("🎓 학기 종합 평가")
if st.button("🧠 학기 종합 평가 생성", key="btn_semester_eval"):
    monthly_evals = {m: st.session_state.evaluations_ai[m] for m in months if m in st.session_state.evaluations_ai}
    if not monthly_evals:
        st.error("먼저 1개 이상의 월별 평가를 생성해주세요.")
    else:
        full_semester_data = "\n\n".join([
            f"**{m} 평가:**\n- 목표: {d['goal']}\n- 평가: {d['evaluation']}"
            for m, d in monthly_evals.items()
        ])
        prompt = (
            "당신은 IEP 평가 전문가입니다. "
            "다음 월별 평가 내용을 바탕으로 학생의 학기 전반적인 성취(강점, 보완점, 향후 지도 방향 포함)에 대해 "
            "종합적으로 기술해 주세요.\n\n"
            f"{full_semester_data}"
        )
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

# ---------------- Word 문서 생성 ----------------
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
st.markdown(
    "<p style='text-align: center; color: grey;'>Copyright © 2025 신하영(천안가온중학교), "
    "성현준(청양고등학교). All Rights Reserved.</p>",
    unsafe_allow_html=True
)
