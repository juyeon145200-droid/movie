
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
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# 2. 영화관 분위기를 위한 CSS
# =========================================================

st.markdown(
    """
    <style>

    /* 전체 화면 배경 */
    .stApp {
        background:
            radial-gradient(circle at 50% 0%, #3b2020 0%, #160d0d 38%, #090909 75%);
        color: #f5f5f5;
    }

    /* 기본 글자 */
    html, body, [class*="css"] {
        font-family: "Arial", "Noto Sans KR", sans-serif;
    }

    /* 상단 헤더 */
    .movie-header {
        text-align: center;
        padding: 35px 20px 25px 20px;
        margin-bottom: 25px;
    }

    .movie-header .small-title {
        color: #d8b06a;
        font-size: 14px;
        letter-spacing: 5px;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .movie-header h1 {
        color: #ffffff;
        font-size: 46px;
        margin: 0;
        font-weight: 800;
        letter-spacing: -2px;
    }

    .movie-header .subtitle {
        color: #bdbdbd;
        margin-top: 12px;
        font-size: 15px;
    }

    /* 필름처럼 보이는 구분선 */
    .film-line {
        height: 4px;
        margin: 15px 0 30px 0;
        background: repeating-linear-gradient(
            90deg,
            #d8b06a 0px,
            #d8b06a 18px,
            transparent 18px,
            transparent 28px
        );
        opacity: 0.8;
    }

    /* 1위 영화 영역 */
    .winner-box {
        background: linear-gradient(
            135deg,
            rgba(75, 34, 34, 0.95),
            rgba(25, 15, 15, 0.95)
        );
        border: 1px solid rgba(216, 176, 106, 0.45);
        border-radius: 18px;
        padding: 28px;
        margin-bottom: 20px;
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.35);
    }

    .winner-label {
        color: #d8b06a;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 3px;
        margin-bottom: 7px;
    }

    .winner-title {
        color: white;
        font-size: 30px;
        font-weight: 800;
        margin: 0;
    }

    /* 지표 카드 */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.055);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 14px;
        padding: 18px;
    }

    div[data-testid="stMetricLabel"] {
        color: #bdbdbd;
    }

    div[data-testid="stMetricValue"] {
        color: #ffffff;
    }

    /* 섹션 제목 */
    .section-title {
        color: #ffffff;
        font-size: 24px;
        font-weight: 800;
        margin-top: 35px;
        margin-bottom: 5px;
    }

    .section-subtitle {
        color: #999999;
        font-size: 13px;
        margin-bottom: 15px;
    }

    /* 데이터프레임 */
    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(216, 176, 106, 0.25);
        border-radius: 12px;
        overflow: hidden;
    }

    /* 차트 영역 */
    .chart-box {
        background: rgba(255, 255, 255, 0.035);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 15px;
    }

    /* 하단 */
    .footer {
        text-align: center;
        color: #777777;
        font-size: 12px;
        margin-top: 45px;
        padding: 25px;
        border-top: 1px solid rgba(255,255,255,0.08);
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 3. 영화관 느낌의 제목
# =========================================================

st.markdown(
    """
    <div class="movie-header">
        <div class="small-title">KOBIS DAILY BOX OFFICE</div>
        <h1>🎬 어제의 박스오피스</h1>
        <div class="subtitle">
            어제 하루 동안 관객들이 가장 많이 찾은 영화는?
        </div>
    </div>

    <div class="film-line"></div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 4. 한국 시간 기준으로 '어제' 계산
# =========================================================

# 배포 서버가 한국 시간이 아닐 수 있기 때문에
# 서버의 현재 시간을 그대로 사용하지 않습니다.
#
# Asia/Seoul을 지정해서 항상 한국 시간으로 현재 날짜를 구합니다.

KST = ZoneInfo("Asia/Seoul")

now_kst = datetime.now(KST)

# 오늘 날짜에서 하루를 빼면 '어제'입니다.
yesterday = now_kst.date() - timedelta(days=1)

# KOBIS API가 요구하는 날짜 형식: YYYYMMDD
target_date = yesterday.strftime("%Y%m%d")

# 화면에 표시할 날짜
display_date = yesterday.strftime("%Y년 %m월 %d일")


# =========================================================
# 5. KOBIS API 주소
# =========================================================

API_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/boxoffice/"
    "searchDailyBoxOfficeList.json"
)


# =========================================================
# 6. Secrets에서 인증키 가져오기
# =========================================================

# 인증키를 코드에 직접 쓰지 않습니다.
#
# Streamlit Cloud의 Secrets에 다음처럼 등록해야 합니다.
#
# KOBIS_KEY = "본인의 인증키"
#
# 실제 인증키는 이 코드에 넣지 않습니다.

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]

except Exception:
    st.error(
        """
        🔑 **KOBIS 인증키를 찾을 수 없습니다.**

        다음 내용을 확인해 주세요.

        1. Streamlit Cloud에서 **Settings → Secrets**를 열었는지 확인하세요.
        2. Secrets에 이름을 정확히 **`KOBIS_KEY`**로 입력했는지 확인하세요.
        3. 인증키의 앞뒤에 불필요한 공백이 없는지 확인하세요.
        4. Secrets를 저장한 뒤 앱을 다시 실행해 보세요.
        """
    )

    st.stop()


# =========================================================
# 7. KOBIS API 요청
# =========================================================

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

    # HTTP 상태코드가 200이 아닌 경우 오류 처리
    response.raise_for_status()

    # JSON 응답을 파이썬 데이터로 변환
    data = response.json()


except requests.exceptions.Timeout:

    st.error(
        """
        ⏰ **KOBIS API 요청 시간이 초과되었습니다.**

        KOBIS 서버의 응답이 늦어지고 있을 수 있습니다.

        다음을 확인해 주세요.

        • 인터넷 연결 상태  
        • KOBIS API 서버 상태  
        • 잠시 후 앱 새로고침
        """
    )

    st.stop()


except requests.exceptions.RequestException as e:

    st.error(
        f"""
        🌐 **KOBIS API에 연결하지 못했습니다.**

        다음 내용을 확인해 주세요.

        • 인터넷 연결 상태  
        • KOBIS API 서버 상태  
        • API 주소가 올바른지 확인

        오류 내용: `{e}`
        """
    )

    st.stop()


except ValueError:

    st.error(
        """
        📄 **KOBIS 서버에서 정상적인 JSON 데이터를 받지 못했습니다.**

        잠시 후 다시 실행하거나 KOBIS API 서버 상태를 확인해 주세요.
        """
    )

    st.stop()


# =========================================================
# 8. KOBIS API의 오류 응답 확인
# =========================================================

# KOBIS는 인증키가 틀려도 HTTP 200을 보낼 수 있습니다.
# 따라서 HTTP 상태코드만 확인하면 안 됩니다.
#
# faultInfo가 있으면 API 자체에서 오류가 발생한 것입니다.

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
        f"""
        🔑 **KOBIS API에서 오류를 반환했습니다.**

        **오류 코드:** `{fault_code}`

        **오류 메시지:** {fault_message}

        특히 다음을 확인해 주세요.

        • Streamlit Secrets의 `KOBIS_KEY`가 정확한지  
        • 인증키가 정상적으로 발급되었는지  
        • 인증키 앞뒤에 공백이 없는지
        """
    )

    st.stop()


# =========================================================
# 9. 박스오피스 데이터 가져오기
# =========================================================

try:

    box_office_result = data["boxOfficeResult"]

    movie_list = box_office_result["dailyBoxOfficeList"]

except (KeyError, TypeError):

    st.error(
        """
        📦 **박스오피스 데이터를 찾을 수 없습니다.**

        KOBIS API의 응답 구조를 정상적으로 받지 못했습니다.

        다음을 확인해 주세요.

        • KOBIS API 서버가 정상적으로 작동하는지  
        • API 인증키가 정상인지  
        • 조회 날짜에 박스오피스 데이터가 집계되었는지
        """
    )

    st.stop()


# =========================================================
# 10. 영화 목록이 비어 있는 경우
# =========================================================

if not movie_list:

    st.warning(
        f"""
        🎞️ **{display_date}의 영화 목록이 비어 있습니다.**

        아직 해당 날짜의 박스오피스가 집계되지 않았거나
        KOBIS API에서 데이터를 제공하지 않는 상태일 수 있습니다.

        다음을 확인해 주세요.

        • KOBIS에서 해당 날짜의 일일 박스오피스가 집계되었는지  
        • API 인증키가 정상인지  
        • KOBIS API 서버에 문제가 없는지  
        • 잠시 후 다시 새로고침했는지
        """
    )

    st.stop()


# =========================================================
# 11. DataFrame 만들기
# =========================================================

df = pd.DataFrame(movie_list)


# =========================================================
# 12. 문자열로 들어온 숫자를 숫자로 변환
# =========================================================

# KOBIS API의 숫자 데이터는 문자열로 전달될 수 있습니다.
# 따라서 그래프와 숫자 계산을 위해 정수로 변환합니다.

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


# =========================================================
# 13. 1위 영화 가져오기
# =========================================================

first_movie = df.iloc[0]

first_movie_name = first_movie["movieNm"]

first_audience = first_movie["audiCnt"]

first_total_audience = first_movie["audiAcc"]


# =========================================================
# 14. 1위 영화 표시
# =========================================================

st.markdown(
    f"""
    <div class="winner-box">

        <div class="winner-label">
            🏆 DAILY BOX OFFICE No.1
        </div>

        <div class="winner-title">
            {first_movie_name}
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 15. 1위 영화 지표 카드 3개
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        label="🎬 영화",
        value=first_movie_name
    )

with col2:

    st.metric(
        label="👥 어제 관객수",
        value=f"{first_audience:,}명"
    )

with col3:

    st.metric(
        label="🎟️ 누적 관객수",
        value=f"{first_total_audience:,}명"
    )


# =========================================================
# 16. 관객수 상위 5편
# =========================================================

st.markdown(
    """
    <div class="section-title">
        📊 TOP 5
    </div>

    <div class="section-subtitle">
        어제 하루 동안 관객수가 가장 많았던 영화 5편
    </div>
    """,
    unsafe_allow_html=True
)


top5 = df.head(5).copy()


# 영화명을 인덱스로 사용해서 그래프를 만듭니다.
chart_data = top5.set_index("movieNm")[["audiCnt"]]


st.bar_chart(
    chart_data,
    horizontal=True
)


# =========================================================
# 17. 전체 박스오피스 표
# =========================================================

st.markdown(
    """
    <div class="section-title">
        🎞️ 전체 박스오피스
    </div>

    <div class="section-subtitle">
        순위 · 영화명 · 개봉일 · 관객수 · 누적관객 · 스크린수
    </div>
    """,
    unsafe_allow_html=True
)


# 필요한 열만 선택합니다.
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


# 표에 표시할 한글 이름으로 변경합니다.
table_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]


# 숫자에 천 단위 쉼표를 넣습니다.
for column in [
    "순위",
    "관객수",
    "누적관객",
    "스크린수"
]:

    table_df[column] = table_df[column].map(
        lambda x: f"{x:,}"
    )


# 개봉일 데이터가 비어 있으면 '-'로 표시합니다.
table_df["개봉일"] = table_df["개봉일"].replace(
    "",
    "-"
)


# 완성된 표를 화면에 표시합니다.
st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 18. 하단 출처
# =========================================================

st.markdown(
    f"""
    <div class="footer">
        🎬 데이터 출처: 영화진흥위원회(KOBIS)<br>
        조회 기준일: {display_date}<br>
        한국 시간(Asia/Seoul) 기준 '어제'의 일일 박스오피스
    </div>
    """,
    unsafe_allow_html=True
)

