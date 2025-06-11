import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time
import io

# ---------------------------
# 초기 세션 변수 정의
# ---------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "로그인"
if "user" not in st.session_state:
    st.session_state.user = ""
if "history" not in st.session_state:
    st.session_state.history = []
if "page_selector" not in st.session_state:
    st.session_state.page_selector = "로그인"  # 또는 기본 진입 페이지

# ---------------------------
# 시뮬레이션용 신호 및 예측 함수
# ---------------------------
def generate_signal():
    t = np.linspace(0, 1, 200)
    signal = np.sin(2 * np.pi * 5 * t) + np.random.normal(0, 0.2, size=t.shape)
    return t, signal

def fake_predict_soh_soc(image):
    soh = np.round(np.random.uniform(70, 100), 2)
    soc = np.round(np.random.uniform(60, 100), 2)
    return soh, soc

# ---------------------------
# 로그인 페이지
# ---------------------------
def show_login():
    st.title("로그인 페이지")
    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if user and pw:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.session_state.page = "배터리 진단"
            return
        else:
            st.warning("아이디와 비밀번호를 입력하세요.")

# ---------------------------
# 배터리 진단 페이지
# ---------------------------
def show_diagnosis():
    st.title("배터리 진단")
    st.markdown("**Bit 파일 업로드 후 측정 시작**")

    col1, col2 = st.columns([2, 1])
    with col2:
        bitfile = st.file_uploader("비트 파일 업로드", type=["bit"])
        serial = st.text_input("배터리 시리얼 넘버")

    if st.button("Acquisition 시작"):
        cmode = np.zeros((3, 4))
        plot_area = st.empty()

        for i in range(3):
            for j in range(4):
                t, s = generate_signal()
                cmode[i, j] = np.max(np.abs(s))

                with plot_area.container():
                    fig, ax = plt.subplots()
                    ax.plot(t, s)
                    ax.set_title(f"element position: ({i+1}, {j+1})")
                    ax.set_xlabel("Time [s]")
                    ax.set_ylabel("Amplitude")
                    st.pyplot(fig)
                time.sleep(0.1)

        with plot_area.container():
            fig2, ax2 = plt.subplots()
            im = ax2.imshow(cmode, cmap="hot", aspect="auto")
            fig2.colorbar(im, ax=ax2, label="Signal Intensity")
            ax2.set_title("Ultrasound Image")
            st.pyplot(fig2)

        # 예측 결과
        soh, soc = fake_predict_soh_soc(cmode)
        st.subheader("진단 결과")
        st.write(f"**SoH** (State of Health): `{soh}%`")
        st.write(f"**SoC** (State of Charge): `{soc}%`")

        if soh >= 80:
            st.success("✅ 재사용 가능")
        else:
            st.error("⚠️ 성능 저하 → 재사용 불가")

        # 결과 저장을 위한 상태값 등록
        buf = io.BytesIO()
        fig2.savefig(buf, format="png")
        img_bytes = buf.getvalue()

        st.session_state.last_result = {
            "serial": serial,
            "soh": soh,
            "soc": soc,
            "img": img_bytes
        }

    # 저장 버튼 처리
    if st.button("결과 저장"):
        if "last_result" not in st.session_state:
            st.warning("진단 결과가 없습니다. 먼저 진단을 실행해주세요.")
        else:
            result = st.session_state.last_result

            if "history" not in st.session_state:
                st.session_state.history = []

            st.session_state.history.append(result)

            # ✅ 페이지 상태와 사이드바 동기화
            st.session_state.page = "마이페이지"
            st.session_state.page_selector = "마이페이지"
            show_mypage()
            st.stop()





# ---------------------------
# 마이페이지
# ---------------------------
def show_mypage():
    st.title("마이페이지")
    if len(st.session_state.history) == 0:
        st.info("저장된 진단 결과가 없습니다.")
    else:
        for i, record in enumerate(st.session_state.history):
            st.markdown(f"#### 배터리 {i+1} - `{record['serial']}`")
            st.write(f"- SoH: `{record['soh']}%`, SoC: `{record['soc']}%`")
            st.image(record["img"], caption="C-mode Image", use_column_width=True)

# ---------------------------
# 페이지 라우팅
# ---------------------------
if st.session_state.page == "로그인":
    show_login()
elif st.session_state.page == "배터리 진단":
    show_diagnosis()
elif st.session_state.page == "마이페이지":
    show_mypage()

# ---------------------------
# 사이드바 메뉴
# ---------------------------
with st.sidebar:
    st.title("메뉴")
    if st.session_state.logged_in:
        st.radio("페이지 이동", ["배터리 진단", "마이페이지"], key="page_selector")
        st.session_state.page = st.session_state.page_selector
    else:
        st.info("로그인 후 사용 가능합니다.")
