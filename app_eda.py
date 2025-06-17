#app_eda.py

import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends 통합 EDA")

        file = st.file_uploader("population_trends.csv 파일을 업로드해 주세요", type="csv")
        if file is None:
            st.info("먼저 population_trends.csv 파일을 업로드해야 한다.")
            return

        df_raw = pd.read_csv(file)

        for col in ["연도", "인구", "출생아수(명)", "사망자수(명)"]:
            if col in df_raw.columns:
                df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

        df = df_raw.fillna(0)
        dup_mask = df.duplicated(keep="first")
        df.loc[dup_mask, "지역"] = df.loc[dup_mask, "지역"] + "(중복)"

        st.sidebar.header("📂 데이터 정보")
        st.sidebar.write(f"총 행: {len(df):,d}개")
        st.sidebar.write(f"기간: {int(df['연도'].min())} – {int(df['연도'].max())}년")
        st.sidebar.markdown("---")

        last_year = int(df["연도"].max())
        start_year = last_year - 9

        tabs = st.tabs([
            "1) 데이터 요약",
            "2) 전국 인구 추이",
            "3) 최근 10년 지역별 변화량",
            "4) 연도별 증감 상위 100",
            "5) 피벗 테이블·누적 영역"
        ])

        # 1) 데이터 요약
        with tabs[0]:
            st.subheader("✅ 전처리 데이터 샘플 (상위 10행)")
            st.dataframe(df.head(10), use_container_width=True)

            st.subheader("ℹ️ 데이터프레임 구조 (df.info())")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("📈 요약 통계 (df.describe())")
            st.dataframe(df.describe(), use_container_width=True)

        # 2) 전국 인구 추이
        with tabs[1]:
            st.subheader("📉 전국 연도별 인구 추이")
            nationwide = df[df["지역"] == "전국"].sort_values("연도")

            fig1, ax1 = plt.subplots(figsize=(10, 5))
            ax1.plot(nationwide["연도"], nationwide["인구"], marker="o", linestyle="-", color="skyblue")
            ax1.set_title("전국 연도별 인구 추이", fontsize=14)
            ax1.set_xlabel("연도")
            ax1.set_ylabel("인구 수")
            ax1.grid(True)
            st.pyplot(fig1)

        # 3) 최근 10년 지역별 변화량
        with tabs[2]:
            st.subheader("📊 최근 10년 지역별 인구 변화량 순위")

            mask = (df["연도"].between(start_year, last_year) & (df["지역"] != "전국"))
            period_df = df[mask]

            pop_start = period_df[period_df["연도"] == start_year][["지역", "인구"]].set_index("지역").rename(columns={"인구": "start"})
            pop_end = period_df[period_df["연도"] == last_year][["지역", "인구"]].set_index("지역").rename(columns={"인구": "end"})
            change_df = pop_end.join(pop_start, how="inner")
            change_df["change"] = change_df["end"] - change_df["start"]
            change_df = change_df.sort_values("change", ascending=False)

            fig2, ax2 = plt.subplots(figsize=(10, 8))
            ax2.barh(change_df.index, change_df["change"], color="steelblue")
            ax2.set_xlabel("인구 변화량")
            ax2.set_ylabel("지역")
            ax2.set_title(f"{start_year}–{last_year}년 지역별 인구 변화량 순위")
            ax2.invert_yaxis()
            ax2.grid(axis="x", linestyle="--", alpha=0.5)
            st.pyplot(fig2)

            with st.expander("🔍 변화량 상세 데이터"):
                st.dataframe(change_df[["start", "end", "change"]], use_container_width=True)

        # 4) 연도별 증감 상위 100
        with tabs[3]:
            st.subheader("📑 지역·연도별 인구 증감 상위 100")

            df_delta = (
                df[df["지역"] != "전국"]
                .sort_values(["지역", "연도"])
                .assign(증감=lambda x: x.groupby("지역")["인구"].diff())
                .dropna(subset=["증감"])
            )

            delta_period = df_delta[df_delta["연도"].between(start_year, last_year)]

            top100 = (
                delta_period
                .assign(abs_change=lambda x: x["증감"].abs())
                .sort_values("abs_change", ascending=False)
                .head(100)
                .drop(columns="abs_change")
                .reset_index(drop=True)
            )

            max_abs = top100["증감"].abs().max()
            styled = (
                top100.style
                .background_gradient(cmap="RdBu", vmin=-max_abs, vmax=max_abs, subset=["증감"])
                .format({"인구": "{:,.0f}", "증감": "{:+,.0f}"})
            )
            st.dataframe(styled, use_container_width=True)

        # 5) 피벗 테이블 및 누적 영역 그래프
        with tabs[4]:
            st.subheader("🗺️ 연도·지역별 인구 피벗 테이블")
            pivot = pd.pivot_table(df, index="연도", columns="지역", values="인구", aggfunc="sum").sort_index()
            st.dataframe(pivot, use_container_width=True)

            st.subheader("📊 지역별 누적 영역 그래프")
            regions = [c for c in pivot.columns if c != "전국"]
            sns.set_theme(style="whitegrid")

            fig3, ax3 = plt.subplots(figsize=(12, 8))
            colors = sns.color_palette("tab20", n_colors=len(regions))
            ax3.stackplot(pivot.index, pivot[regions].T, labels=regions, colors=colors)
            ax3.set_xlabel("연도")
            ax3.set_ylabel("인구 수")
            ax3.set_title("연도별 지역 인구 누적 영역 그래프")
            ax3.legend(loc="upper left", bbox_to_anchor=(1.02, 1), title="지역")
            ax3.margins(0, 0)
            st.pyplot(fig3)



# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()