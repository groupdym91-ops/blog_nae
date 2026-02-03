# -*- coding: utf-8 -*-
import streamlit as st
import time
import os
from urllib.parse import quote, urlparse, parse_qs

# Selenium 관련 임포트
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# 페이지 설정
st.set_page_config(
    page_title="네이버 서로이웃 자동 신청",
    page_icon="🤝",
    layout="wide"
)

# 세션 상태 초기화
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'stop_requested' not in st.session_state:
    st.session_state.stop_requested = False

def add_log(log_type, message):
    """로그 추가"""
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.logs.append({
        "type": log_type,
        "message": message,
        "timestamp": timestamp
    })

def get_chrome_driver():
    """Chrome 드라이버 설정 (Streamlit Cloud 호환)"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')

    # Streamlit Cloud 환경 감지 (Linux + 시스템 chromium 존재)
    is_streamlit_cloud = os.path.exists('/usr/bin/chromium-browser') or os.path.exists('/usr/bin/chromium')

    if is_streamlit_cloud:
        # Streamlit Cloud: 시스템 chromium 사용
        chromium_path = '/usr/bin/chromium-browser' if os.path.exists('/usr/bin/chromium-browser') else '/usr/bin/chromium'
        chromedriver_path = '/usr/bin/chromedriver'

        options.binary_location = chromium_path
        service = Service(chromedriver_path)
    else:
        # 로컬 환경: webdriver-manager 사용
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def keyboard_input(element, text):
    """키보드 직접 입력"""
    element.click()
    time.sleep(0.3)
    for char in text:
        element.send_keys(char)
        time.sleep(0.05)
    time.sleep(0.3)

def naver_login(driver, user_id, user_pw):
    """네이버 로그인"""
    try:
        driver.get('https://nid.naver.com/nidlogin.login')
        wait = WebDriverWait(driver, 10)

        id_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#id')))
        keyboard_input(id_input, user_id)

        pw_input = driver.find_element(By.CSS_SELECTOR, '#pw')
        keyboard_input(pw_input, user_pw)

        login_btn = driver.find_element(By.CSS_SELECTOR, '#log\\.login')
        login_btn.click()

        add_log("success", "로그인 시도 완료")
        time.sleep(3)
        return True
    except Exception as e:
        add_log("error", f"로그인 오류: {str(e)[:100]}")
        return False

def extract_blog_ids(driver, keyword, target_count=100):
    """블로그 ID 추출"""
    try:
        encoded_keyword = quote(keyword)
        url = f"https://m.blog.naver.com/SectionSearch.naver?orderType=sim&pageAccess=trend&periodType=all&searchValue={encoded_keyword}"

        add_log("info", "검색 URL 접속 중...")
        driver.get(url)
        time.sleep(2)

        # 목표 개수에 따라 스크롤 횟수 조정
        scroll_count = max(15, target_count // 5)
        add_log("info", f"스크롤 진행 중... ({scroll_count}회)")
        for i in range(scroll_count):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)

        time.sleep(1)

        elements = driver.find_elements(By.CSS_SELECTOR, 'a.profile_area__riebt')
        add_log("info", f"총 {len(elements)}개의 프로필 요소 발견")

        blog_ids = []
        seen = set()

        for element in elements:
            href = element.get_attribute('href')
            if href:
                parsed = urlparse(href)
                params = parse_qs(parsed.query)
                if 'blogId' in params:
                    blog_id = params['blogId'][0]
                    if blog_id not in seen:
                        seen.add(blog_id)
                        blog_ids.append(blog_id)

        return blog_ids
    except Exception as e:
        add_log("error", f"블로그 목록 추출 오류: {str(e)[:100]}")
        return []

def send_buddy_request(driver, blog_id, message):
    """서로이웃 신청"""
    try:
        url = f"https://m.blog.naver.com/BuddyAddForm.naver?blogId={blog_id}"
        add_log("info", f"서로이웃 신청 중: {blog_id}")
        driver.get(url)
        time.sleep(2)

        # 서로이웃 라디오 버튼
        try:
            wait = WebDriverWait(driver, 3)
            both_buddy_radio = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#bothBuddyRadio')))
            both_buddy_radio.click()
            add_log("info", "  - 서로이웃 라디오 버튼 클릭")
            time.sleep(0.5)
        except:
            add_log("warning", f"  [건너뜀] {blog_id}님은 서로이웃을 받지 않거나 이미 신청했습니다.")
            return False

        # 메시지 입력
        try:
            message_textarea = driver.find_element(
                By.CSS_SELECTOR,
                '#buddyAddForm > fieldset > div > div.set_detail_t1 > div.set_detail_t1 > div > textarea'
            )
            message_textarea.click()
            time.sleep(0.3)
            message_textarea.clear()
            message_textarea.send_keys(message)
            add_log("info", "  - 메시지 입력 완료")
            time.sleep(0.5)
        except:
            pass

        # 그룹 선택
        try:
            group_select_element = driver.find_element(By.CSS_SELECTOR, '#buddyGroupSelect')
            group_select = Select(group_select_element)
            options = group_select.options
            if len(options) > 0:
                group_select.select_by_index(len(options) - 1)
            time.sleep(0.5)
        except:
            pass

        # 확인 버튼
        confirm_btn = driver.find_element(By.CSS_SELECTOR, 'body > ui-view > div.head.type1 > a.btn_ok')
        confirm_btn.click()
        time.sleep(1)

        add_log("success", f"[성공] {blog_id} 서로이웃 신청 완료!")
        return True
    except Exception as e:
        add_log("error", f"[실패] {blog_id} 오류: {str(e)[:50]}")
        return False

def run_automation(naver_id, naver_pw, keyword, message, request_count, exclude_ids, status_container):
    """자동화 실행"""
    st.session_state.is_running = True
    st.session_state.stop_requested = False
    st.session_state.logs = []

    add_log("info", "서로이웃 자동 신청을 시작합니다...")
    add_log("info", f"계정: {naver_id}")
    add_log("info", f"키워드: {keyword}")
    add_log("info", f"신청 개수: {request_count}개")
    if exclude_ids:
        add_log("info", f"제외 아이디: {len(exclude_ids)}개")

    driver = None
    try:
        add_log("info", "브라우저 시작 중...")
        try:
            driver = get_chrome_driver()
        except Exception as e:
            add_log("error", f"브라우저 시작 실패: {str(e)[:200]}")
            st.session_state.is_running = False
            return

        # 로그인
        add_log("info", "=" * 40)
        add_log("info", "1. 네이버 로그인")
        if not naver_login(driver, naver_id, naver_pw):
            add_log("error", "로그인 실패")
            return

        # 블로그 목록 추출
        add_log("info", "=" * 40)
        add_log("info", "2. 블로그 목록 추출")
        blog_ids = extract_blog_ids(driver, keyword, request_count)

        if not blog_ids:
            add_log("warning", "추출된 블로그가 없습니다.")
            return

        add_log("success", f"추출된 블로그 ID: {len(blog_ids)}개")

        # 제외 아이디 필터링
        if exclude_ids:
            original_count = len(blog_ids)
            blog_ids = [bid for bid in blog_ids if bid not in exclude_ids]
            excluded_count = original_count - len(blog_ids)
            if excluded_count > 0:
                add_log("info", f"제외된 아이디: {excluded_count}개")

        # 신청 개수 제한
        if len(blog_ids) > request_count:
            blog_ids = blog_ids[:request_count]
            add_log("info", f"신청 개수 제한: {request_count}개로 제한됨")

        # 서로이웃 신청
        add_log("info", "=" * 40)
        add_log("info", "3. 서로이웃 신청 시작")

        success_count = 0
        fail_count = 0

        for idx, blog_id in enumerate(blog_ids, 1):
            # 중지 요청 확인
            if st.session_state.stop_requested:
                add_log("warning", "사용자에 의해 중지되었습니다.")
                break

            add_log("info", f"[{idx}/{len(blog_ids)}] 처리 중...")

            if send_buddy_request(driver, blog_id, message):
                success_count += 1
            else:
                fail_count += 1
            time.sleep(2)

        # 결과
        add_log("info", "=" * 40)
        add_log("success", "서로이웃 신청 완료")
        add_log("success", f"성공: {success_count}개 / 실패: {fail_count}개")

    except Exception as e:
        add_log("error", f"오류 발생: {str(e)[:100]}")
    finally:
        if driver:
            driver.quit()
        st.session_state.is_running = False

# 메인 UI
st.title("🤝 네이버 서로이웃 자동 신청")
st.caption("키워드로 검색된 블로그에 자동으로 서로이웃을 신청합니다")

st.divider()

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("🔐 네이버 계정")
    naver_id = st.text_input("아이디", placeholder="네이버 아이디를 입력하세요", autocomplete="off")
    naver_pw = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", autocomplete="new-password")

    st.subheader("💬 서로이웃 메시지")
    message = st.text_area(
        "메시지",
        value="안녕하세요! 서로이웃 신청드립니다.",
        height=100,
        placeholder="서로이웃 신청 시 보낼 메시지를 입력하세요"
    )

    st.subheader("🔍 검색 키워드")
    keyword = st.text_input("키워드", placeholder="블로그 검색 키워드를 입력하세요")

    st.subheader("🔢 신청 개수")
    request_count = st.radio(
        "서로이웃 신청 개수 선택",
        options=[30, 50, 100],
        horizontal=True,
        index=0
    )

    st.subheader("🚫 제외 아이디")
    exclude_ids_input = st.text_area(
        "제외할 블로그 아이디",
        height=80,
        placeholder="제외할 아이디를 입력하세요 (쉼표 또는 줄바꿈으로 구분)\n예: blogid1, blogid2, blogid3"
    )

    st.divider()

    # 시작/중지 버튼
    btn_col1, btn_col2 = st.columns(2)

    with btn_col1:
        if st.button(
            "🚀 서로이웃 신청 시작",
            disabled=st.session_state.is_running,
            use_container_width=True,
            type="primary"
        ):
            if not naver_id or not naver_pw:
                st.error("❌ 네이버 아이디와 비밀번호를 입력해주세요.")
            elif not keyword:
                st.error("❌ 검색 키워드를 입력해주세요.")
            else:
                # 제외 아이디 파싱 (쉼표, 줄바꿈, 공백으로 구분)
                exclude_ids = set()
                if exclude_ids_input.strip():
                    for item in exclude_ids_input.replace('\n', ',').replace(' ', ',').split(','):
                        item = item.strip()
                        if item:
                            exclude_ids.add(item)

                with st.spinner("자동화 실행 중..."):
                    run_automation(naver_id, naver_pw, keyword, message, request_count, exclude_ids, col2)
                    st.rerun()

    with btn_col2:
        if st.button(
            "⏹️ 중지",
            disabled=not st.session_state.is_running,
            use_container_width=True,
            type="secondary"
        ):
            st.session_state.stop_requested = True
            add_log("warning", "중지 요청됨... 현재 작업 완료 후 중지됩니다.")
            st.rerun()

with col2:
    st.subheader("📋 실시간 로그")

    # 로그 표시 영역
    log_container = st.container(height=400)

    with log_container:
        if st.session_state.logs:
            for log in st.session_state.logs:
                timestamp = log["timestamp"]
                msg = log["message"]
                log_type = log["type"]

                if log_type == "success":
                    st.success(f"[{timestamp}] {msg}")
                elif log_type == "error":
                    st.error(f"[{timestamp}] {msg}")
                elif log_type == "warning":
                    st.warning(f"[{timestamp}] {msg}")
                else:
                    st.info(f"[{timestamp}] {msg}")
        else:
            st.info("로그가 여기에 표시됩니다. 시작 버튼을 눌러주세요.")

    btn_col_a, btn_col_b = st.columns(2)
    with btn_col_a:
        if st.button("🗑️ 로그 지우기", use_container_width=True):
            st.session_state.logs = []
            st.rerun()
    with btn_col_b:
        if st.button("🔄 상태 초기화", use_container_width=True):
            st.session_state.logs = []
            st.session_state.is_running = False
            st.session_state.stop_requested = False
            st.rerun()

# 사이드바 안내
with st.sidebar:
    st.header("📌 사용 방법")
    st.markdown("""
    1. **네이버 계정** 입력
    2. **서로이웃 메시지** 작성
    3. **검색 키워드** 입력
    4. **시작 버튼** 클릭
    """)

    st.divider()

    st.header("⚠️ 주의사항")
    st.markdown("""
    - 과도한 사용은 계정 제재를 받을 수 있습니다
    - 네이버 정책을 준수해주세요
    - 개인정보 보호에 유의하세요
    """)
