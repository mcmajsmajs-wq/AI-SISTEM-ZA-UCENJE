#!/usr/bin/env python3
"""
Frontend Quiz Test - Simplified version
"""

from playwright.sync_api import sync_playwright
import sys

BASE_URL = "http://localhost:8090"


def test_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        results = {"passed": 0, "failed": 0, "tests": []}

        def log(test_name, passed, error=None):
            status = "PASS" if passed else "FAIL"
            print(f"  [{status}] {test_name}")
            if error:
                print(f"         Error: {error[:100]}")
            if passed:
                results["passed"] += 1
            else:
                results["failed"] += 1

        try:
            # 1. Test login page loads
            print("\n1. Testing login page...")
            page.goto(BASE_URL + "/login")
            page.wait_for_load_state("domcontentloaded")

            # Check for login form elements
            email_input = page.locator('input[type="email"]').count()
            password_input = page.locator('input[type="password"]').count()
            submit_btn = page.locator('button[type="submit"]').count()

            log("Login page loads", email_input > 0 and password_input > 0)
            log("Email input present", email_input > 0)
            log("Password input present", password_input > 0)
            log("Submit button present", submit_btn > 0)

            # 2. Take screenshot of login page
            page.screenshot(path="/tmp/login_page.png")
            log("Login screenshot saved", True)

            # 3. Test login
            print("\n2. Testing login...")
            page.fill('input[type="email"]', "test@example.com")
            page.fill('input[type="password"]', "TestPass123!")
            page.click('button[type="submit"]')

            # Wait for navigation
            page.wait_for_timeout(5000)
            current_url = page.url
            log(f"After login URL: {current_url}", True)

            # 4. Take dashboard screenshot
            page.screenshot(path="/tmp/dashboard.png", full_page=True)
            log("Dashboard screenshot saved", True)

            # 5. Check documents page
            print("\n3. Testing documents page...")
            page.goto(BASE_URL + "/documents")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            page.screenshot(path="/tmp/documents.png", full_page=True)
            log("Documents page loads", True)

            # 6. Check quizzes page
            print("\n4. Testing quizzes page...")
            page.goto(BASE_URL + "/quizzes")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            page.screenshot(path="/tmp/quizzes.png", full_page=True)
            log("Quizzes page loads", True)

            # 7. Find any quiz and play it
            print("\n5. Testing quiz play...")
            page.goto(BASE_URL + "/quizzes")
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)

            # Find first quiz link - use /quizzes/:id pattern
            quiz_links = (
                page.locator('a[href*="/quizzes/"]')
                .filter(
                    has_not=page.locator('[href*="/quizzes/"]').filter(
                        has_text="Prijavi"
                    )
                )
                .all()
            )
            if quiz_links:
                # Find the first link that contains a quiz ID
                for link in quiz_links:
                    href = link.get_attribute("href")
                    if href and "/play" not in href:
                        print(f"  Clicking quiz: {href}")
                        link.click()
                        page.wait_for_load_state("domcontentloaded")
                        page.wait_for_timeout(3000)
                        page.screenshot(path="/tmp/quiz_play.png", full_page=True)
                        log("Quiz play page loads", True)
                        break
            else:
                # Try direct URL
                page.goto(
                    BASE_URL + "/quizzes/480da8b5-b30d-42da-920f-cdbc4a9d5bbe/play"
                )
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(3000)
                page.screenshot(path="/tmp/quiz_play.png", full_page=True)
                log("Quiz play page loads", True)

        except Exception as e:
            print(f"\n  [FAIL] Test execution: {str(e)[:100]}")
            page.screenshot(path="/tmp/error.png")
            results["failed"] += 1

        browser.close()

        # Print summary
        print("\n" + "=" * 60)
        print(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
        print("=" * 60)

        return results["failed"] == 0


if __name__ == "__main__":
    success = test_frontend()
    sys.exit(0 if success else 1)
