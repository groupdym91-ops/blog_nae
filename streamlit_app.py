# -*- coding: utf-8 -*-
import streamlit as st
import time
import json
from urllib.parse import quote, urlparse, parse_qs

# Selenium 관련 임포트
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pyperclip

# 페이지 설정
st.set_page_config(
    page_title="네이버 서로이웃 자동 신청",
    page_icon="🤝",
    layout="wide"
)

# CSS 스타일
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

    * {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    }

    .stApp {
        background-color: #0f172a;
    }

    .main-header {
        text-align: center;
        padding: 2rem 0;
    }

    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }

    .main-header p {
        color: #94a3b8;
    }

    .log-container {
        background-color: #0f172a;
        border-radius: 8px;
        padding: 1rem;
        height: 400px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 0.85rem;
    }

    .log-info { color: #cbd5e1; }
    .log-success { color: #4ade80; }
    .log-error { color: #f87171; }
    .log-warning { color: #fbbf24; }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'accounts' not in st.session_state:
    st.session_state.accounts = [{"id": "1", "naver_id": "", "naver_pw": ""}]
if 'messages' not in st.session_state:
    st.session_state.messages = [{"id": "1", "content": "안녕하세요! 서로이웃 신청드립니다."}]

def add_log(log_type, message):
    """로그 추가"""
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.logs.append({
        "type": log_type,
        "message": message,
        "timestamp": timestamp
    })

def get_chrome_driver():
    """Chrome 드라이버 설정"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def clipboard_input(driver, element, text):
    """클립보드를 통한 입력"""
    pyperclip.copy(text)
    element.click()
    time.sleep(0.3)
    element.send_keys(Keys.CONTROL, 'v')
    time.sleep(0.3)

def naver_login(driver, user_id, user_pw, log_placeholder):
    """네이버 로그인"""
    try:
        driver.get('https://nid.naver.com/nidlogin.login')
        wait = WebDriverWait(driver, 10)

        id_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#id')))
        clipboard_input(driver, id_input, user_id)

        pw_input = driver.find_element(By.CSS_SELECTOR, '#pw')
        clipboard_input(driver, pw_input, user_pw)

        login_btn = driver.find_element(By.CSS_SELECTOR, '#log\\.login')
        login_btn.click()

        add_log("success", "로그인 시도 완료")
        update_log_display(log_placeholder)
        time.sleep(3)
        return True
    except Exception as e:
        add_log("error", f"로그인 오류: {str(e)[:100]}")
        update_log_display(log_placeholder)
        return False

def extract_blog_ids(driver, keyword, log_placeholder):
    """블로그 ID 추출"""
    try:
        encoded_keyword = quote(keyword)
        url = f"https://m.blog.naver.com/SectionSearch.naver?orderType=sim&pageAccess=trend&periodType=all&searchValue={encoded_keyword}"

        add_log("info", "검색 URL 접속 중...")
        update_log_display(log_placeholder)
        driver.get(url)
        time.sleep(2)

        add_log("info", "스크롤 진행 중...")
        update_log_display(log_placeholder)
        for i in range(10):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)

        time.sleep(1)

        elements = driver.find_elements(By.CSS_SELECTOR, 'a.profile_area__riebt')
        add_log("info", f"총 {len(elements)}개의 프로필 요소 발견")
        update_log_display(log_placeholder)

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
        update_log_display(log_placeholder)
        return []

def send_buddy_request(driver, blog_id, message, log_placeholder):
    """서로이웃 신청"""
    try:
        url = f"https://m.blog.naver.com/BuddyAddForm.naver?blogId={blog_id}"
        add_log("info", f"서로이웃 신청 중: {blog_id}")
        update_log_display(log_placeholder)
        driver.get(url)
        time.sleep(2)

        # 서로이웃 라디오 버튼
        try:
            wait = WebDriverWait(driver, 3)
            both_buddy_radio = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#bothBuddyRadio')))
            both_buddy_radio.click()
            add_log("info", "  - 서로이웃 라디오 버튼 클릭")
            update_log_display(log_placeholder)
            time.sleep(0.5)
        except:
            add_log("warning", f"  [건너뜀] {blog_id}님은 서로이웃을 받지 않거나 이미 신청했습니다.")
            update_log_display(log_placeholder)
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
            update_log_display(log_placeholder)
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
        update_log_display(log_placeholder)
        return True
    except Exception as e:
        add_log("error", f"[실패] {blog_id} 오류: {str(e)[:50]}")
        update_log_display(log_placeholder)
        return False

def update_log_display(placeholder):
    """로그 표시 업데이트"""
    log_html = ""
    for log in st.session_state.logs[-100:]:  # 최근 100개만 표시
        color_class = f"log-{log['type']}"
        log_html += f'<div class="{color_class}">[{log["timestamp"]}] {log["message"]}</div>'

    placeholder.markdown(f'<div class="log-container">{log_html}</div>', unsafe_allow_html=True)

def run_automation(naver_id, naver_pw, keyword, message, log_placeholder):
    """자동화 실행"""
    st.session_state.is_running = True
    st.session_state.logs = []

    add_log("info", "서로이웃 자동 신청을 시작합니다...")
    add_log("info", f"계정: {naver_id}")
    add_log("info", f"키워드: {keyword}")
    update_log_display(log_placeholder)

    driver = None
    try:
        add_log("info", "브라우저 시작 중...")
        update_log_display(log_placeholder)
        driver = get_chrome_driver()

        # 로그인
        add_log("info", "=" * 40)
        add_log("info", "1. 네이버 로그인")
        update_log_display(log_placeholder)
        if not naver_login(driver, naver_id, naver_pw, log_placeholder):
            add_log("error", "로그인 실패")
            update_log_display(log_placeholder)
            return

        # 블로그 목록 추출
        add_log("info", "=" * 40)
        add_log("info", "2. 블로그 목록 추출")
        update_log_display(log_placeholder)
        blog_ids = extract_blog_ids(driver, keyword, log_placeholder)

        if not blog_ids:
            add_log("warning", "추출된 블로그가 없습니다.")
            update_log_display(log_placeholder)
            return

        add_log("success", f"추출된 블로그 ID: {len(blog_ids)}개")
        update_log_display(log_placeholder)

        # 서로이웃 신청
        add_log("info", "=" * 40)
        add_log("info", "3. 서로이웃 신청 시작")
        update_log_display(log_placeholder)

        success_count = 0
        fail_count = 0

        for idx, blog_id in enumerate(blog_ids, 1):
            add_log("info", f"[{idx}/{len(blog_ids)}] 처리 중...")
            update_log_display(log_placeholder)

            if send_buddy_request(driver, blog_id, message, log_placeholder):
                success_count += 1
            else:
                fail_count += 1
            time.sleep(2)

        # 결과
        add_log("info", "=" * 40)
        add_log("success", "서로이웃 신청 완료")
        add_log("success", f"성공: {success_count}개 / 실패: {fail_count}개")
        update_log_display(log_placeholder)

    except Exception as e:
        add_log("error", f"오류 발생: {str(e)[:100]}")
        update_log_display(log_placeholder)
    finally:
        if driver:
            driver.quit()
        st.session_state.is_running = False

# 메인 UI
st.markdown('<div class="main-header"><h1>🤝 네이버 서로이웃 자동 신청</h1><p>키워드로 검색된 블로그에 자동으로 서로이웃을 신청합니다</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔐 네이버 계정")
    naver_id = st.text_input("아이디", placeholder="네이버 아이디")
    naver_pw = st.text_input("비밀번호", type="password", placeholder="비밀번호")

    st.subheader("💬 서로이웃 메시지")
    message = st.text_area("메시지", value="안녕하세요! 서로이웃 신청드립니다.", height=100)

    st.subheader("🔍 검색 키워드")
    keyword = st.text_input("키워드", placeholder="블로그 검색 키워드")

    if st.button("🚀 서로이웃 신청 시작", disabled=st.session_state.is_running, use_container_width=True):
        if not naver_id or not naver_pw:
            st.error("네이버 아이디와 비밀번호를 입력해주세요.")
        elif not keyword:
            st.error("검색 키워드를 입력해주세요.")
        else:
            with col2:
                log_placeholder = st.empty()
                run_automation(naver_id, naver_pw, keyword, message, log_placeholder)

with col2:
    st.subheader("📋 실시간 로그")
    log_placeholder = st.empty()

    if st.session_state.logs:
        update_log_display(log_placeholder)
    else:
        log_placeholder.markdown('<div class="log-container"><p style="color: #64748b; text-align: center; margin-top: 150px;">로그가 여기에 표시됩니다</p></div>', unsafe_allow_html=True)

    if st.button("🗑️ 로그 지우기", use_container_width=True):
        st.session_state.logs = []
        st.rerun()
