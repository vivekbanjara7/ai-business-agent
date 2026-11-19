
from playwright.sync_api import sync_playwright

APP_URL = "http://localhost:8501"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    page = browser.new_page()
    page.goto(APP_URL)
    page.wait_for_load_state("domcontentloaded")

    print("\nAI Business Agent opened.")
    print("Send one short message manually in Chromium.")
    print("You have 60 seconds...\n")

    page.wait_for_timeout(60000)

    # Inspect Streamlit's actual test IDs
    elements = page.locator("[data-testid]").evaluate_all(
        """
        elements => elements.map(element => ({
            testid: element.getAttribute("data-testid"),
            text: (element.innerText || "").slice(0, 200)
        }))
        """
    )

    print("\n--- DETECTED ELEMENTS ---")

    for element in elements:
        if any(word in element["testid"].lower()
               for word in ["chat", "message", "status"]):
            print(element)

    print("\n--- PAGE TEXT ---")
    print(page.locator("body").inner_text()[:3000])

    print("\nInspection complete.")

    browser.close()
