import streamlit as st
from openai import OpenAI


# ---------------------------------------------------------
# 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="최범규와의 채팅",
    page_icon="💬",
    layout="centered",
)


# ---------------------------------------------------------
# 화면 제목
# ---------------------------------------------------------
st.title("💬 최범규와의 채팅")
st.caption("편하게 이야기해 보세요! ")


# ---------------------------------------------------------
# API 키 확인
# ---------------------------------------------------------
# Streamlit Cloud의 Secrets에
# GEMINI_API_KEY = "실제 API 키"
# 형태로 저장해 두어야 합니다.
if "GEMINI_API_KEY" not in st.secrets:
    st.info("AI 채팅을 사용하려면 Secrets에 GEMINI_API_KEY를 설정해 주세요.")
    st.stop()

api_key = st.secrets["GEMINI_API_KEY"]


# ---------------------------------------------------------
# Gemini API를 OpenAI 라이브러리로 연결
# ---------------------------------------------------------
client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)


# ---------------------------------------------------------
# AI의 성격 설정
# ---------------------------------------------------------
# 이 문장은 화면에 표시하지 않고 AI에게만 전달합니다.
SYSTEM_MESSAGE = """
너는 다정하고 잘 챙겨주는 섬세한 투모로우바이투게더라는 아이돌 멤버인 최범규.
사용자에게 따뜻하고 친절하게 대하며, 상대방의 말에 세심하게 반응해.
대화가 자연스럽고 편안하게 이어지도록 해.
"""


# ---------------------------------------------------------
# 대화 기록 만들기
# ---------------------------------------------------------
# st.session_state를 사용하면 페이지가 다시 실행되어도
# 현재 세션에서 이전 대화 내용을 기억할 수 있습니다.
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []


# ---------------------------------------------------------
# 지금까지의 대화 내용을 화면에 표시
# ---------------------------------------------------------
for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ---------------------------------------------------------
# 사용자 입력창
# ---------------------------------------------------------
user_message = st.chat_input("메시지를 입력해 보세요...")


# 사용자가 메시지를 보냈을 때 실행됩니다.
if user_message:
    # 먼저 사용자의 메시지를 대화 기록에 저장합니다.
    st.session_state.chat_messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    # 사용자의 메시지를 바로 화면에 보여 줍니다.
    with st.chat_message("user"):
        st.markdown(user_message)

    # -----------------------------------------------------
    # Gemini에 보낼 전체 대화 만들기
    # -----------------------------------------------------
    # system 메시지 + 지금까지의 모든 대화를 함께 보냅니다.
    # 그래서 AI가 앞에서 나눈 이야기를 참고할 수 있습니다.
    messages = [
        {
            "role": "system",
            "content": SYSTEM_MESSAGE,
        }
    ]

    messages.extend(st.session_state.chat_messages)

    # -----------------------------------------------------
    # AI 답변 받기
    # -----------------------------------------------------
    try:
        # AI 답변이 표시될 말풍선을 먼저 만듭니다.
        with st.chat_message("assistant"):
            response_placeholder = st.empty()

            full_response = ""

            # stream=True를 사용하면 답변이 한꺼번에 나타나지 않고
            # 생성되는 대로 조금씩 화면에 표시됩니다.
            stream = client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=messages,
                stream=True,
            )

            # 스트리밍으로 들어오는 답변을 하나씩 이어 붙입니다.
            for chunk in stream:
                # 답변 내용이 들어 있는 부분을 가져옵니다.
                content = chunk.choices[0].delta.content

                if content:
                    full_response += content

                    # 커서 모양을 함께 표시해서
                    # 답변이 실시간으로 나오는 느낌을 줍니다.
                    response_placeholder.markdown(full_response + "▌")

            # 답변이 모두 끝나면 커서를 제거합니다.
            response_placeholder.markdown(full_response)

        # 완성된 AI 답변을 대화 기록에 저장합니다.
        # 다음 질문을 할 때 이 내용도 함께 Gemini에 전달됩니다.
        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": full_response,
            }
        )

    except Exception:
        # API 오류가 발생했을 때 복잡한 오류 내용을 그대로 보여 주지 않습니다.
        st.info("잠시 문제가 생겼어요. API 키와 인터넷 연결을 확인한 뒤 다시 시도해 주세요.")
