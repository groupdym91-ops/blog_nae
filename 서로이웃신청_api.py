# -*- coding: utf-8 -*-
import argparse
import json
import sys
import io
import time
from urllib.parse import urlparse, parse_qs, quote

# 표준 출력 인코딩을 UTF-8로 설정 (한글 깨짐 방지)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pyperclip


def log(log_type, message):
    """JSON 형식으로 로그 출력"""
    try:
        print(json.dumps({"type": log_type, "message": message}, ensure_ascii=False), flush=True)
    except Exception:
        pass


def clipboard_input(driver, element, text):
    """클립보드를 통해 텍스트를 입력하는 함수"""
    pyperclip.copy(text)
    element.click()
    time.sleep(0.3)
    element.send_keys(Keys.CONTROL, 'v')
    time.sleep(0.3)


def naver_login(driver, user_id, user_pw):
    """네이버 로그인 함수"""
    try:
        driver.get('https://nid.naver.com/nidlogin.login')
        wait = WebDriverWait(driver, 10)

        id_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#id')))
        clipboard_input(driver, id_input, user_id)

        pw_input = driver.find_element(By.CSS_SELECTOR, '#pw')
        clipboard_input(driver, pw_input, user_pw)

        login_btn = driver.find_element(By.CSS_SELECTOR, '#log\\.login')
        login_btn.click()

        log("success", "로그인 시도 완료")
        time.sleep(3)
        return True

    except Exception as e:
        log("error", f"로그인 오류: {e}")
        return False


def extract_blog_ids(driver, keyword):
    """블로그 ID 목록 추출"""
    try:
        encoded_keyword = quote(keyword)
        url = f"https://m.blog.naver.com/SectionSearch.naver?orderType=sim&pageAccess=trend&periodType=all&searchValue={encoded_keyword}"

        log("info", "검색 URL 접속 중...")
        driver.get(url)
        time.sleep(2)

        log("info", "스크롤 진행 중...")
        for i in range(10):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            log("info", f"스크롤 {i + 1}/10 완료")

        time.sleep(1)

        elements = driver.find_elements(By.CSS_SELECTOR, 'a.profile_area__riebt')
        log("info", f"총 {len(elements)}개의 프로필 요소 발견")

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
        log("error", f"블로그 목록 추출 오류: {e}")
        return []


def send_buddy_request(driver, blog_id, message):
    """서로이웃 신청 (개선된 버전)"""
    try:
        url = f"https://m.blog.naver.com/BuddyAddForm.naver?blogId={blog_id}"
        log("info", f"서로이웃 신청 중: {blog_id}")
        driver.get(url)

        # 페이지 로딩 대기
        time.sleep(2)

        # 1. '서로이웃' 라디오 버튼 확인 (가장 중요한 부분)
        try:
            # 3초만 기다려보고 없으면 포기 (이미 이웃이거나 신청 불가)
            wait = WebDriverWait(driver, 3)
            both_buddy_radio = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#bothBuddyRadio')))
            both_buddy_radio.click()
            log("info", "  - 서로이웃 라디오 버튼 클릭")
            time.sleep(0.5)
        except Exception:
            # 라디오 버튼을 못 찾으면 경고 로그를 남기고 False 리턴 (건너뛰기)
            log("warning", f"  [건너뜀] {blog_id}님은 '서로이웃'을 받지 않거나 이미 신청했습니다.")
            return False

        # 2. 메시지 입력
        try:
            message_textarea = driver.find_element(
                By.CSS_SELECTOR,
                '#buddyAddForm > fieldset > div > div.set_detail_t1 > div.set_detail_t1 > div > textarea'
            )
            message_textarea.click()
            time.sleep(0.3)
            message_textarea.clear()
            message_textarea.send_keys(message)
            log("info", "  - 메시지 입력 완료")
            time.sleep(0.5)
        except Exception:
            log("warning", "  - 메시지 입력칸을 찾을 수 없습니다 (기본 메시지로 전송됩니다)")

        # 3. 그룹 선택 (마지막 옵션)
        try:
            group_select_element = driver.find_element(By.CSS_SELECTOR, '#buddyGroupSelect')
            group_select = Select(group_select_element)
            options = group_select.options
            if len(options) > 0:
                group_select.select_by_index(len(options) - 1)
                log("info", f"  - 블로그 그룹 선택: {options[-1].text}")
            time.sleep(0.5)
        except Exception:
            pass  # 그룹 선택 실패해도 진행

        # 4. 확인 버튼 클릭
        confirm_btn = driver.find_element(By.CSS_SELECTOR, 'body > ui-view > div.head.type1 > a.btn_ok')
        confirm_btn.click()
        time.sleep(1)

        log("success", f"[성공] {blog_id} 서로이웃 신청 완료!")
        return True

    except Exception as e:
        log("error", f"[실패] {blog_id} 처리 중 알 수 없는 오류: {str(e)[:100]}")
        return False


def main():
    parser = argparse.ArgumentParser(description='네이버 서로이웃 자동 신청')
    parser.add_argument('--naver-id', required=True, help='네이버 아이디')
    parser.add_argument('--naver-pw', required=True, help='네이버 비밀번호')
    parser.add_argument('--keyword', required=True, help='검색 키워드')
    parser.add_argument('--message', required=True, help='서로이웃 신청 메시지')
    args = parser.parse_args()

    # Chrome 옵션 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        # 1. 로그인
        log("info", "=" * 50)
        log("info", "1. 네이버 로그인")
        log("info", "=" * 50)
        if not naver_login(driver, args.naver_id, args.naver_pw):
            log("error", "로그인 실패. 프로그램을 종료합니다.")
            return

        # 2. 블로그 목록 추출
        log("info", "=" * 50)
        log("info", "2. 블로그 목록 추출")
        log("info", "=" * 50)
        blog_ids = extract_blog_ids(driver, args.keyword)

        if not blog_ids:
            log("warning", "추출된 블로그가 없습니다.")
            return

        log("success", f"추출된 블로그 ID: {len(blog_ids)}개")
        for idx, bid in enumerate(blog_ids, 1):
            log("info", f"  {idx}. {bid}")

        # 3. 서로이웃 신청
        log("info", "=" * 50)
        log("info", "3. 서로이웃 신청 시작")
        log("info", "=" * 50)

        success_count = 0
        fail_count = 0

        for idx, blog_id in enumerate(blog_ids, 1):
            log("info", f"[{idx}/{len(blog_ids)}] 처리 중...")
            if send_buddy_request(driver, blog_id, args.message):
                success_count += 1
            else:
                fail_count += 1
            time.sleep(2)

        # 4. 결과
        log("info", "=" * 50)
        log("success", "서로이웃 신청 완료")
        log("info", "=" * 50)
        log("success", f"총 {len(blog_ids)}개 중")
        log("success", f"  - 성공: {success_count}개")
        if fail_count > 0:
            log("warning", f"  - 실패: {fail_count}개")

    except Exception as e:
        log("error", f"오류 발생: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()