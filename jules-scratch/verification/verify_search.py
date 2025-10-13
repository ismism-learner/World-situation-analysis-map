from playwright.sync_api import sync_playwright, expect
import os
import json

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Log console messages
        page.on("console", lambda msg: print(f"PAGE LOG: {msg.text}"))

        # Load the local HTML file
        file_path = os.path.abspath('naturalearth_map_viewer_with_draggable_labels_fixed.html')
        page.goto(f'file://{file_path}')
        expect(page.locator("#globe")).to_be_visible(timeout=10000)

        # Load the cities database directly into the page
        with open('newmap/countries+states+cities.json', 'r', encoding='utf-8') as f:
            cities_data = json.load(f)

        page.evaluate(f"window.citiesDatabase = {json.dumps(cities_data)};")
        page.evaluate("document.getElementById('search-panel').classList.add('active');")

        # --- Test Case 1: Search for "阿根廷" (Argentina in Chinese) ---
        search_input = page.locator("#searchInput")
        search_results = page.locator("#searchResults")

        search_input.fill("阿根廷")

        # Expect to see "Argentina" in the search results
        result_item = search_results.locator(".search-result-item", has_text="Argentina").first
        expect(result_item).to_be_visible(timeout=5000)

        print("Test Case 1 Passed: Found 'Argentina' when searching for '阿根廷'.")

        # Take a screenshot
        page.screenshot(path='jules-scratch/verification/search_verification.png')

        # --- Test Case 2: Create an event using Chinese names ---
        event_input = page.locator("#eventInput")
        add_event_btn = page.locator("#addEventBtn")

        event_string = "2025-01-01;友好访问;阿根廷;会见;中国"
        event_input.fill(event_string)
        add_event_btn.click()

        # Check if a connection was created
        connection_group = page.locator(".connection-group").first
        expect(connection_group).to_be_visible(timeout=5000)

        # Check the label
        connection_label = connection_group.locator(".connection-label")
        expect(connection_label).to_contain_text("2025-01-01, 友好访问, 会见")

        print("Test Case 2 Passed: Successfully created a connection using Chinese location names.")

        # Take a final screenshot
        page.screenshot(path='jules-scratch/verification/event_creation_verification.png')

        browser.close()
        print("All verification tests passed!")

if __name__ == "__main__":
    run_verification()