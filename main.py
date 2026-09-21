
import streamlit as st
import pandas as pd
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# =========================================================
# 1. 페이지 기본 설정
# =========================================================

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 박스오피스")
st.caption("영화진흥위원회(KOBIS) 일일 박스오피스 기준")


# =========================================================
# 2. 한국 시간 기준으로 '어제' 날짜 계산
# =========================================================

# Streamlit Cloud 서버가 한국 시간이 아닐 수 있기 때문에
# 반드시 한국 시간(Asia/Seoul)을 직접 지정합니다.
KST = ZoneInfo("Asia/Seoul")

# 현재 한국 시간
now_kst = datetime.now(KST)

# 한국 시간 기준으로 하루 전 날짜를 계산합니다.
yesterday = now_kst.date() - timedelta(days=1)

# KOBIS API에서 사용하는 날짜 형식: YYYYMMDD
target_date = yesterday.strftime("%Y%m%d")

# 화면에 표시할 날짜
display_date = yesterday.strftime("%Y년 %m월 %d일")


# =========================================================
# 3. KOBIS API 주소
# =========================================================

# 일일 박스오피스 API
BOXOFFICE_API_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/boxoffice/"
    "searchDailyBoxOfficeList.json"
)

# 영화 상세정보 API
# 영화의 장르 정보를 가져올 때 사용합니다.
MOVIE_INFO_API_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/movie/"
    "searchMovieInfo.json"
)


# =========================================================
# 4. Secrets에서 KOBIS 인증키 가져오기
# =========================================================

# 인증키를 코드에 직접 적지 않습니다.
# Streamlit Cloud의 Secrets에 KOBIS_KEY를 저장해야 합니다.
try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]

except Exception:
    st.error(
        "🔑 KOBIS 인증키를 찾을 수 없습니다.\n\n"
        "다음 내용을 확인해 주세요.\n\n"
        "1. Streamlit Cloud의 앱 설정에서 Secrets를 열었는지 확인하세요.\n"
        "2. Secrets에 `KOBIS_KEY`라는 이름이 정확하게 있는지 확인하세요.\n"
        "3. 인증키의 앞뒤에 불필요한 공백이 없는지 확인하세요."
    )

    st.stop()


# =========================================================
# 5. KOBIS 일일 박스오피스 API 요청
# =========================================================

# API에 전달할 값입니다.
params = {
    "key": KOBIS_KEY,
    "targetDt": target_date
}

try:
    response = requests.get(
        BOXOFFICE_API_URL,
        params=params,
        timeout=10
    )

    # HTTP 오류가 발생하면 예외를 발생시킵니다.
    response.raise_for_status()

    # JSON 데이터를 파이썬 딕셔너리로 변환합니다.
    data = response.json()

except requests.exceptions.Timeout:
    st.error(
        "⏰ KOBIS API 요청 시간이 초과되었습니다.\n\n"
        "KOBIS 서버가 늦게 응답하고 있을 수 있습니다.\n"
        "잠시 후 페이지를 새로고침해 주세요."
    )
    st.stop()

except requests.exceptions.RequestException as e:
    st.error(
        "🌐 KOBIS API에 접속하지 못했습니다.\n\n"
        "다음 내용을 확인해 주세요.\n\n"
        "• 인터넷 연결 상태\n"
        "• KOBIS API 서버 상태\n"
        "• API 요청 주소\n\n"
        f"오류 정보: {e}"
    )
    st.stop()

except ValueError:
    st.error(
        "📄 KOBIS 서버에서 정상적인 JSON 데이터를 받지 못했습니다.\n\n"
        "잠시 후 다시 시도하거나 KOBIS API 서버 상태를 확인해 주세요."
    )
    st.stop()


# =========================================================
# 6. KOBIS의 오류 응답 확인
# =========================================================

# KOBIS는 인증키가 잘못되어도 HTTP 상태코드가 200일 수 있습니다.
# 따라서 faultInfo가 있는지 반드시 확인해야 합니다.
if "faultInfo" in data:

    fault_info = data["faultInfo"]

    fault_code = fault_info.get(
        "errorCode",
        "알 수 없음"
    )

    fault_message = fault_info.get(
        "message",
        "알 수 없는 오류"
    )

    st.error(
        "🔑 KOBIS API에서 오류를 반환했습니다.\n\n"
        f"오류 코드: {fault_code}\n\n"
        f"오류 메시지: {fault_message}\n\n"
        "KOBIS 인증키가 정확한지 확인해 주세요."
    )

    st.stop()


# =========================================================
# 7. 박스오피스 영화 목록 가져오기
# =========================================================

try:
    box_office_result = data["boxOfficeResult"]

    movie_list = box_office_result[
        "dailyBoxOfficeList"
    ]

except (KeyError, TypeError):

    st.error(
        "📦 KOBIS 응답에서 박스오피스 데이터를 찾지 못했습니다.\n\n"
        "다음 내용을 확인해 주세요.\n\n"
        "• KOBIS API가 정상적으로 응답했는지\n"
        "• 조회 날짜가 올바른지\n"
        "• KOBIS API 서버에 문제가 없는지"
    )

    st.stop()


# =========================================================
# 8. 영화 목록이 비어 있는 경우
# =========================================================

if not movie_list:

    st.warning(
        f"🎬 {display_date}의 박스오피스 영화 목록이 비어 있습니다.\n\n"
        "다음 내용을 확인해 주세요.\n\n"
        "• 해당 날짜의 박스오피스가 집계되었는지\n"
        "• KOBIS API 인증키가 정상인지\n"
        "• KOBIS API 서버에 문제가 없는지\n"
        "• API 요청 날짜가 올바른지"
    )

    st.stop()


# =========================================================
# 9. 영화 데이터를 DataFrame으로 변환
# =========================================================

df = pd.DataFrame(movie_list)


# KOBIS API의 숫자 데이터는 문자열로 전달됩니다.
# 따라서 숫자로 변환해



