
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# ---------------------------------------------------------
# 1. 기본 설정
# ---------------------------------------------------------

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 박스오피스")
st.caption("영화진흥위원회(KOBIS) 일일 박스오피스 기준")


# ---------------------------------------------------------
# 2. 한국 시간 기준으로 '어제' 날짜 계산
# ---------------------------------------------------------

# 배포 서버가 해외 시간대여도 한국 시간을 기준으로 계산하기 위해
# Asia/Seoul 시간대를 직접 지정합니다.
KST = ZoneInfo("Asia/Seoul")

now_kst = datetime.now(KST)
yesterday = now_kst.date() - timedelta(days=1)

# KOBIS API가 요구하는 날짜 형식: YYYYMMDD
target_date = yesterday.strftime("%Y%m%d")

# 화면에 보여 줄 날짜 형식
display_date = yesterday.strftime("%Y년 %m월 %d일")


# ---------------------------------------------------------
# 3. KOBIS API 설정
# ---------------------------------------------------------

API_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/boxoffice/"
    "searchDailyBoxOfficeList.json"
)

# 인증키는 코드에 직접 작성하지 않고
# Streamlit Cloud의 Secrets에서 가져옵니다.
try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]
except Exception:
    st.error(
        "🔑 KOBIS 인증키를 찾을 수 없습니다.\n\n"
        "다음을 확인해 주세요.\n"
        "1. Streamlit Cloud의 앱 설정에서 Secrets를 열었는지 확인하세요.\n"
        "2. Secrets에 `KOBIS_KEY`라는 이름으로 인증키를 입력했는지 확인하세요.\n"
        "3. 인증키 앞뒤에 불필요한 따옴표나 공백이 없는지 확인하세요."
    )
    st.stop()


# ---------------------------------------------------------
# 4. KOBIS API 호출
# ---------------------------------------------------------

params = {
    "key": KOBIS_KEY,
    "targetDt": target_date
}

try:
    response = requests.get(
        API_URL,
        params=params,
        timeout=10
    )

    # HTTP 오류가 발생하면 예외를 발생시킵니다.
    response.raise_for_status()

    # JSON 형식으로 변환합니다.
    data = response.json()

except requests.exceptions.Timeout:
    st.error(
        "⏰ KOBIS API 요청 시간이 초과되었습니다.\n\n"
        "잠시 후 페이지를 새로고침하거나, "
        "KOBIS 서버 상태를 확인해 주세요."
    )
    st.stop()

except requests.exceptions.RequestException as e:
    st.error(
        "🌐 KOBIS API에 접속하지 못했습니다.\n\n"
        "다음을 확인해 주세요.\n"
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


# ---------------------------------------------------------
# 5. KOBIS API의 오류 응답 확인
# ---------------------------------------------------------

# KOBIS는 인증키가 잘못되어도 HTTP 상태코드가 200일 수 있습니다.
# 따라서 faultInfo가 있는지 반드시 확인합니다.
if "faultInfo" in data:
    fault_info = data["faultInfo"]

    fault_code = fault_info.get("errorCode", "알 수 없음")
    fault_message = fault_info.get("message", "알 수 없는 오류")

    st.error(
        "🔑 KOBIS API에서 오류를 반환했습니다.\n\n"
        f"오류 코드: {fault_code}\n\n"
        f"오류 메시지: {fault_message}\n\n"
        "특히 인증키가 올바른지 확인해 주세요."
    )
    st.stop()


# ---------------------------------------------------------
# 6. 박스오피스 데이터 꺼내기
# ---------------------------------------------------------

try:
    box_office_result = data["boxOfficeResult"]
    movie_list = box_office_result["dailyBoxOfficeList"]

except (KeyError, TypeError):
    st.error(
        "📦 KOBIS 응답에서 박스오피스 데이터를 찾지 못했습니다.\n\n"
        "다음을 확인해 주세요.\n"
        "• KOBIS API가 정상적으로 응답했는지\n"
        "• 조회 날짜가 올바른지\n"
        "• KOBIS API 서버에 문제가 없는지"
    )
    st.stop()


# ---------------------------------------------------------
# 7. 영화 목록이 비어 있는 경우
# ---------------------------------------------------------

if not movie_list:
    st.warning(
        f"🎬 {display_date}의 박스오피스 영화 목록이 비어 있습니다.\n\n"
        "다음을 확인해 주세요.\n"
        "• KOBIS에서 해당 날짜의 일일 박스오피스가 집계되었는지\n"
        "• 조회 날짜가 올바른지\n"
        "• KOBIS API 서버에 문제가 없는지\n"
        "• API 인증키가 정상적으로 등록되어 있는지"
    )
    st.stop()


# ---------------------------------------------------------
# 8. DataFrame 만들기
# ---------------------------------------------------------

df = pd.DataFrame(movie_list)


# KOBIS API에서는 숫자 데이터도 문자열로 전달될 수 있으므로
# 화면에서 숫자로 제대로 처리할 수 있도록 변환합니다.
number_columns = [
    "rank",
    "audiCnt",
    "audiAcc",
    "scrnCnt"
]

for column in number_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0).astype(int)


# ---------------------------------------------------------
# 9. 1위 영화 정보
# ---------------------------------------------------------

first_movie = df.iloc[0]

first_movie_name = first_movie["movieNm"]
first_audience = first_movie["audiCnt"]
first_total_audience = first_movie["audiAcc"]


st.subheader(f"🏆 {display_date} 박스오피스 1위")


# 1위 영화의 주요 지표를 카드 3개로 표시합니다.
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🎬 영화",
        value=first_movie_name
    )

with col2:
    st.metric(
        label="👥 일일 관객수",
        value=f"{first_audience:,}명"
    )

with col3:
    st.metric(
        label="👥 누적 관객수",
        value=f"{first_total_audience:,}명"
    )


# ---------------------------------------------------------
# 10. 관객수 상위 5편 막대그래프
# ---------------------------------------------------------

st.subheader("📊 관객수 상위 5편")

top5 = df.head(5).copy()

# 영화명을 인덱스로 설정하면 Streamlit의 bar_chart에서
# 영화별 관객수를 쉽게 표시할 수 있습니다.
chart_data = top5.set_index("movieNm")[["audiCnt"]]

st.bar_chart(
    chart_data,
    horizontal=True
)


# ---------------------------------------------------------
# 11. 전체 박스오피스 표
# ---------------------------------------------------------

st.subheader("🎥 전체 박스오피스")

# 사용자에게 보여 줄 열과 한글 이름을 정합니다.
table_df = df[
    [
        "rank",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
].copy()

table_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]


# 숫자에 천 단위 쉼표를 적용합니다.
for column in ["순위", "관객수", "누적관객", "스크린수"]:
    table_df[column] = table_df[column].map(
        lambda x: f"{x:,}"
    )


# 개봉일이 없는 경우에는 '-'로 표시합니다.
table_df["개봉일"] = table_df["개봉일"].replace(
    "",
    "-"
)


st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# 12. 데이터 출처
# ---------------------------------------------------------

st.caption(
    f"📌 데이터 출처: 영화진흥위원회(KOBIS) | "
    f"조회 기준일: {display_date}"
)


