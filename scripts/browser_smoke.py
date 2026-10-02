"""Launch the installed browser on an offline page to check its native runtime."""

from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.set_content("<title>quant-browser-check</title><p>offline</p>")
            if page.title() != "quant-browser-check":
                raise RuntimeError("Chromium did not render the offline check page")
            print("Chromium headless launch and offline page check passed.")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
