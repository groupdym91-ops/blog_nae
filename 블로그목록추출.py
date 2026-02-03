from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, parse_qs, quote
import time


def extract_blog_ids(keyword):
    """키워드로 검색한 네이버 블로그에서 블로그 ID 목록 추출"""

    # 검색 URL 생성 (키워드 인코딩)
    encoded_keyword = quote(keyword)
    url = f"https://m.blog.naver.com/SectionSearch.naver?orderType=sim&pageAccess=trend&periodType=all&searchValue={encoded_keyword}"

    # Chrome 옵션 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    # WebDriver 실행
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    # 자동화 탐지 우회
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        # URL 접속
        print(f"검색 키워드: {keyword}")dlavmffkssmx
        print(f"URL 접속 중: {url}")
        driver.get(url)

        # 페이지 로딩 대기
        time.sleep(2)

        # 스크롤을 끝까지 내리고 0.5초 대기를 10번 반복
        print("스크롤 진행 중...")
        for i in range(10):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            print(f"스크롤 {i + 1}/10 완료")

        # 추가 로딩 대기
        time.sleep(1)

        # a.profile_area__riebt 셀렉터로 모든 요소 찾기
        elements = driver.find_elements(By.CSS_SELECTOR, 'a.profile_area__riebt')
        print(f"\n총 {len(elements)}개의 프로필 요소 발견")

        # blogId 추출 (중복 제거)
        blog_ids = []
        seen = set()

        for element in elements:
            href = element.get_attribute('href')
            if href:
                # URL 파싱하여 blogId 추출
                parsed = urlparse(href)
                params = parse_qs(parsed.query)

                if 'blogId' in params:
                    blog_id = params['blogId'][0]
                    if blog_id not in seen:
                        seen.add(blog_id)
                        blog_ids.append(blog_id)

        return blog_ids

    except Exception as e:
        print(f"오류 발생: {e}")
        return []

    finally:
        driver.quit()


if __name__ == "__main__":
    # 사용자로부터 키워드 입력 받기
    keyword = input("검색할 키워드를 입력하세요: ")

    if not keyword.strip():
        print("키워드를 입력해주세요.")
    else:
        # 블로그 ID 추출
        blog_ids = extract_blog_ids(keyword)

        # 결과 출력
        print("\n" + "=" * 50)
        print(f"추출된 블로그 ID 목록 (총 {len(blog_ids)}개)")
        print("=" * 50)

        for idx, blog_id in enumerate(blog_ids, 1):
            print(f"{idx}. {blog_id}")

        print("=" * 50)
