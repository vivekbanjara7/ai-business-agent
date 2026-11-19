
from playwright.sync_api import sync_playwright

APP_URL = "http://localhost:8501"


def test_app_loads(page):
    page.goto(APP_URL)
    page.wait_for_load_state("domcontentloaded")

    assert page.title() != ""

    print("PASS: AI Business Agent loaded successfully!")


def test_chat_response(page):
    expected_text = "PLAYWRIGHT_CHAT_TEST_74291"

    chat_input = page.locator(
        '[data-testid="stChatInputTextArea"]'
    )

    chat_input.wait_for(state="visible", timeout=15000)

    chat_input.fill(
        f"Reply with exactly this text and nothing else: {expected_text}"
    )

    chat_input.press("Enter")

    print("Waiting for normal chat response...")

    page.get_by_text(
        expected_text,
        exact=True
    ).wait_for(state="visible", timeout=120000)

    print("PASS: AI chat response verified!")


def test_calculator(page):
    chat_input = page.locator(
        '[data-testid="stChatInputTextArea"]'
    )

    chat_input.wait_for(state="visible", timeout=15000)

    prompt = (
        "Use your calculator tool to calculate "
        "15000 minus 9500. Tell me the final result."
    )

    chat_input.fill(prompt)
    chat_input.press("Enter")

    print("Calculator request submitted. Waiting for result...")

    page.wait_for_function(
        """
        () => {
            const text = document.body.innerText;
            return /5,?500/.test(text);
        }
        """,
        timeout=120000
    )

    print("PASS: Expected calculator result 5500 detected!")


def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        try:
            page = browser.new_page()

            print("\\nStarting AI Business Agent tests...\\n")

            test_app_loads(page)
            test_chat_response(page)
            test_calculator(page)

            print("\\nALL TESTS PASSED!")

        except Exception:
            print("\\nTEST FAILED!")

            page.screenshot(
                path="tests/calculator_test_failure.png",
                full_page=True
            )

            print(page.locator("body").inner_text()[:3000])

            raise

        finally:
            input("\\nPress Enter to close Chromium...")
            browser.close()


if __name__ == "__main__":
    run_tests()
