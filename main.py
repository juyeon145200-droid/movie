
import streamlit as st
import pandas as pd
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# =========================================================
# 1. 페이지 기본 설정
# =========================================================

st.set_page_config(
    page_title="어제의 박스오피스 🎬",
    page_icon="🎬",
    layout="wide"
)


# =========================================================
# 2. 영화관 느낌의 화면 디자인
# =========================================================
# Streamlit 기본 화면을 영화관처럼 어둡게 꾸밉니다.
# 별도의 CSS 라이브러리는 설치하지 않습니다.

st.markdown(
    """
    <style>
    /* 전체 배경 */
    .stApp {
        background:
            radial-gradient(
                circle at 50% 0%,
                rgba(90, 40, 40, 0.45),
                transparent 45%
            ),
            linear-gradient(
                180deg,
                #090909 0%,
                #111111 45%,
                #080808 100%
            );
        color: #f5f5f5;
    }

    /* 상단 제목 영역 */
    .cinema-header {
        text-align: center;
        padding: 35px 20px 30px 20px;
        margin-bottom: 25px;
        border-radius: 20px;

        background:
            linear-gradient(
                rgba(0, 0, 0, 0.55),
                rgba(0, 0, 0, 0.75)
            ),
            radial-gradient(
                ellipse at center,
                #542020 0%,
                #1a0d0d 55%,
                #080808 100%
            );

        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow:
            0 15px 45px rgba(0, 0, 0, 0.55);
    }

    .cinema-header h1 {
        font-size: 42px;
        margin-bottom: 8px;
        color: #ffffff;
    }

    .cinema-header p {
        color: #bbbbbb;
        font-size: 16px;
    }

    /* 지표 카드 */
    div[data-testid="stMetric"] {
        background:
            linear-gradient(
                145deg,
                rgba(55, 55, 55, 0.85),
                rgba(20, 20, 20, 0.95)
            );
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.35);
    }

    /* 섹션 제목 */
    h2, h3 {
        color: #ffffff;
    }

    /* 표 */
    div[data-testid="stDataFrame"] {
        border-radius: 15px;
        overflow: hidden;
    }

    /* 안내 문구 */
    .info-box {
        background: rgba(255, 255, 255, 0.06);
        border-left: 4px solid #d4af37;
        border-radius: 10px;
        padding: 15px 18px;
        margin: 15px 0;
        color: #dddddd;
    }

    /* 영화관 스크린 느낌 */
    .screen-line {
        height: 5px;
        border-radius: 50%;
        background: linear-gradient(
            90deg,
            transparent,
            #d4af37,
            transparent
        );
        margin: 5px auto 30px auto;
        max-width: 700px;
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.35);
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 3. 제목
# =========================================================

st.markdown(
    """
    <div class="cinema-header">
        <h1>🎬 어제의 박스오피스</h1>
        <div class="screen-line"></div>
        <p>영화진흥위원회(KOBIS) 일일 박스오피스</p>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 4. 한국 시간 기준으로 '어제' 계산
# =========================================================
# 배포 서버가 한국 시간이 아니어도
# Asia/Seoul 시간대를 사용하기 때문에 항상 한국 시간 기준입니다.

KST = ZoneInfo("Asia/Seoul")

now_kst = datetime.now(KST)

# 오늘 날짜에서 하루를 빼서 '어제'를 만듭니다.
yesterday = now_kst.date() - timedelta(days=1)

# KOBIS API가 요구하는 날짜 형식: YYYYMMDD
target_date = yesterday.strftime("%Y%m%d")

# 화면에 표시할 날짜
display_date = yesterday.strftime("%Y년 %m월 %d일")


st.markdown(
    f"""
    <div class="info-box">
        📅 <b>{display_date}</b> 박스오피스입니다.
        <br>
        한국 시간(KST) 기준으로 자동 계산된 어제 날짜를 조회합니다.
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 5. KOBIS 인증키 가져오기
# =========================================================
# 인증키를 코드에 직접 작성하지 않습니다.
# Streamlit Cloud의 Secrets에서 KOBIS_KEY를 읽습니다.

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]

except Exception:
    st.error(
        """
        🔑 KOBIS 인증키를 찾을 수 없습니다.

        다음 사항을 확인해 주세요.

        1. Streamlit Cloud에서 앱의 Settings를 엽니다.
        2. Secrets 메뉴를 엽니다.
        3. 다음과 같이 KOBIS_KEY를 등록했는지 확인합니다.

        KOBIS_KEY = "발급받은_인증키"

        4. 이름이 정확히 `KOBIS_KEY`인지 확인합니다.
        5. 인증키 앞뒤에 불필요한 공백이 없는지 확인합니다.
        """
    )
    st.stop()


# =========================================================
# 6. KOBIS API 주소
# =========================================================

# 일일 박스오피스 정보를 가져오는 API
BOXOFFICE_API_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/boxoffice/"
    "searchDailyBoxOfficeList.json"
)

# 영화 상세정보를 가져오는 API
# 영화 장르를 가져오기 위해 사용합니다.
MOVIE_INFO_API_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/movie/"
    "searchMovieInfo.json"
)


# =========================================================
# 7. 일일 박스오피스 가져오기
# =========================================================

params = {
    "key": KOBIS_KEY,
    "targetDt": target_date
}

try:
    response = requests.get(
        BOXOFFICE_API_URL,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

except requests.exceptions.Timeout:
    st.error(
        """
        ⏰ KOBIS API 요청 시간이 초과되었습니다.

        다음을 확인해 주세요.

        • 인터넷 연결 상태
        • KOBIS API 서버 상태
        • 잠시 후 다시 새로고침

        서버가 일시적으로 느린 경우 잠시 후 다시 시도하면 됩니다.
        """
    )
    st.stop()

except requests.exceptions.RequestException as e:
    st.error(
        f"""
        🌐 KOBIS API에 접속하지 못했습니다.

        다음을 확인해 주세요.

        • 인터넷 연결 상태
        • KOBIS API 서버 상태
        • API 주소가 올바른지 확인
        • 잠시 후 다시 시도

        오류 정보: {e}
        """
    )
    st.stop()

except ValueError:
    st.error(
        """
        📄 KOBIS 서버에서 정상적인 JSON 데이터를 받지 못했습니다.

        KOBIS API 서버가 정상적으로 응답하고 있는지 확인한 뒤
        잠시 후 다시 시도해 주세요.
        """
    )
    st.stop()


# =========================================================
# 8. KOBIS 오류 응답 확인
# =========================================================
# 중요한 부분입니다.
#
# KOBIS는 인증키가 틀려도 HTTP 상태코드가 200일 수 있습니다.
# 따라서 response.status_code만 확인하면 안 되고
# 응답 안에 faultInfo가 있는지도 확인해야 합니다.

if "faultInfo" in data:

    fault_info = data["faultInfo"]

    error_code = fault_info.get(
        "errorCode",
        "알 수 없음"
    )

    error_message = fault_info.get(
        "message",
        "알 수 없는 오류"
    )

    st.error(
        f"""
        🔑 KOBIS API에서 오류를 반환했습니다.

        오류 코드: {error_code}

        오류 메시지: {error_message}

        특히 다음을 확인해 주세요.

        • Streamlit Secrets의 KOBIS_KEY가 정확한지
        • 인증키가 만료되거나 제한된 상태가 아닌지
        • KOBIS Open API 이용 상태에 문제가 없는지
        """
    )

    st.stop()


# =========================================================
# 9. 박스오피스 데이터 꺼내기
# =========================================================

try:

    box_office_result = data["boxOfficeResult"]

    movie_list = box_office_result["dailyBoxOfficeList"]

except (KeyError, TypeError):

    st.error(
        """
        📦 박스오피스 데이터를 찾을 수 없습니다.

        다음을 확인해 주세요.

        • KOBIS API가 정상적으로 응답했는지
        • 조회 날짜가 올바른지
        • KOBIS API 서버에 문제가 없는지
        • 인증키가 정상적으로 등록되어 있는지
        """
    )

    st.stop()


# =========================================================
# 10. 영화 목록이 비어 있는 경우
# =========================================================

if not movie_list:

    st.warning(
        f"""
        🎬 {display_date}의 영화 목록이 비어 있습니다.

        아직 해당 날짜의 박스오피스가 집계되지 않았거나
        KOBIS API에서 데이터를 제공하지 않는 상태일 수 있습니다.

        다음을 확인해 주세요.

        • KOBIS에서 해당 날짜의 일일 박스오피스가 집계되었는지
        • 한국 시간 기준으로 조회 날짜가 맞는지
        • KOBIS API 서버에 문제가 없는지
        • Streamlit Secrets의 KOBIS_KEY가 정확한지
        """
    )

    st.stop()


# =========================================================
# 11. DataFrame 만들기
# =========================================================

df = pd.DataFrame(movie_list)


# =========================================================
# 12. 숫자 데이터를 숫자로 변환
# =========================================================
# KOBIS API에서는 숫자도 문자열 형태로 올 수 있으므로
# 그래프와 표에서 제대로 처리할 수 있도록 숫자로 바꿉니다.

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
# 13. 영화 장르 가져오기
# =========================================================
# 일일 박스오피스 API에는 장르가 직접 들어 있지 않기 때문에
# 각 영화의 movieCd를 이용해 영화 상세정보 API를 호출합니다.
#
# 장르 API 요청에 문제가 생겨도 박스오피스 전체 화면이
# 사라지지 않도록 '장르 정보 없음'으로 처리합니다.

@st.cache_data(ttl=3600)
def get_movie_genre(movie_code, api_key):
    """
    영화 코드(movieCd)를 이용해 KOBIS에서 장르를 가져옵니다.
    """

    try:

        params = {
            "key": api_key,
            "movieCd": movie_code
        }

        response = requests.get(
            MOVIE_INFO_API_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        movie_data = response.json()

        # 영화 상세정보 API에도 faultInfo가 있을 수 있습니다.
        if "faultInfo" in movie_data:
            return "장르 정보 없음"

        movie_info = movie_data.get(
            "movieInfoResult",
            {}
        ).get(
            "movieInfo",
            {}
        )

        genres = movie_info.get(
            "genres",
            []
        )

        # 장르 목록에서 genreNm만 뽑습니다.
        genre_names = [
            genre.get("genreNm")
            for genre in genres
            if genre.get("genreNm")
        ]

        if genre_names:
            return ", ".join(genre_names)

        return "장르 정보 없음"

    except Exception:
        return "장르 정보 없음"


# 영화별 장르를 가져옵니다.
genres = []

for _, movie in df.iterrows():

    movie_code = movie.get("movieCd")

    if movie_code:
        genre = get_movie_genre(
            movie_code,
            KOBIS_KEY
        )
    else:
        genre = "장르 정보 없음"

    genres.append(genre)


df["genre"] = genres


# =========================================================
# 14. 1위 영화 정보
# =========================================================

first_movie = df.iloc[0]

first_movie_name = first_movie["movieNm"]
first_genre = first_movie["genre"]

first_audience = first_movie["audiCnt"]
first_total_audience = first_movie["audiAcc"]


st.subheader("🏆 어제의 박스오피스 1위")


# 1위 영화명을 크게 보여 줍니다.
st.markdown(
    f"""
    <div style="
        text-align:center;
        padding:25px;
        margin-bottom:20px;
        border-radius:18px;
        background:rgba(255,255,255,0.05);
        border:1px solid rgba(255,255,255,0.1);
    ">
        <div style="
            font-size:16px;
            color:#aaaaaa;
            margin-bottom:8px;
        ">
            BOX OFFICE NO.1
        </div>

        <div style="
            font-size:34px;
            font-weight:bold;
            color:#ffffff;
        ">
            🎞️ {first_movie_name}
        </div>

        <div style="
            font-size:16px;
            color:#d4af37;
            margin-top:10px;
        ">
            장르 · {first_genre}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 15. 1위 영화 지표 카드 3개
# =========================================================

col1, col2, col3 = st.columns(3

