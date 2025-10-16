from playwright.sync_api import sync_playwright, expect

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost")

        # Wait for the "Run Simulation" button to be enabled
        run_button = page.get_by_role("button", name="Run Simulation")
        expect(run_button).to_be_enabled()

        # Take a screenshot to verify the fix
        page.screenshot(path="jules-scratch/verification/verification.png")

        browser.close()

if __name__ == "__main__":
    run_verification()