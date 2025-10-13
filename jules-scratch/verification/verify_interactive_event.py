from playwright.sync_api import sync_playwright, expect
import os
import json

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Load the local HTML file
        file_path = os.path.abspath('naturalearth_map_viewer_with_draggable_labels_fixed.html')
        page.goto(f'file://{file_path}')
        expect(page.locator("#globe")).to_be_visible(timeout=10000)

        # Load the cities database
        with open('newmap/countries+states+cities.json', 'r', encoding='utf-8') as f:
            cities_data = json.load(f)
        page.evaluate(f"window.citiesDatabase = {json.dumps(cities_data)};")

        # Load a map layer to have something to click on
        page.evaluate("""
            () => {
                const geojson = {
                    type: "FeatureCollection",
                    features: [{
                        type: "Feature",
                        id: "test-country-1",
                        properties: { NAME: "Testland" },
                        geometry: { type: "Polygon", coordinates: [ [ [0,0], [10,0], [10,10], [0,10], [0,0] ] ] }
                    }]
                };
                processLayerData('countries', geojson, '110m');
                toggleLayer('countries', true);
            }
        """)

        # --- Test Case: Location Not Found, User Intervenes ---
        event_input = page.locator("#eventInput")
        add_event_btn = page.locator("#addEventBtn")
        picker_panel = page.locator("#location-picker-panel")
        missing_loc_name = page.locator("#missing-location-name")
        confirm_btn = page.locator("#confirm-location-btn")
        selected_info = page.locator("#selected-location-info")

        # 1. Input an event with a deliberately fake location name
        event_string = "2025-01-01;探险;Atlantis;前往;中国"
        event_input.fill(event_string)
        add_event_btn.click()

        # 2. Verify that the location picker panel appears for "Atlantis"
        expect(picker_panel).to_be_visible(timeout=5000)
        expect(missing_loc_name).to_have_text("Atlantis")
        expect(confirm_btn).to_be_disabled()
        page.screenshot(path='jules-scratch/verification/1_picker_panel_visible.png')
        print("Test Case 1 Passed: Location picker panel appeared for unknown location.")

        # 3. Simulate user clicking on the map
        picker_panel.evaluate("el => el.style.display = 'none'")
        page.locator(".layer-country").first.click()
        picker_panel.evaluate("el => el.style.display = 'block'")
        page.wait_for_timeout(500) # Wait for UI to update

        # After clicking, some location name should appear
        expect(selected_info).to_have_text("已选择: Testland")
        expect(confirm_btn).to_be_enabled()
        page.screenshot(path='jules-scratch/verification/2_location_selected.png')
        print("Test Case 2 Passed: User selection was registered.")

        # 4. User confirms the location
        confirm_btn.click()

        # Panel should disappear
        expect(picker_panel).to_be_hidden()

        # Now the process should continue and find "China" automatically
        # and create the connection.
        expect(page.locator(".connection-group")).to_have_count(1, timeout=5000)
        expect(page.locator(".connection-label")).to_contain_text("2025-01-01, 探险, 前往")
        page.screenshot(path='jules-scratch/verification/3_event_created.png')
        print("Test Case 3 Passed: Event was created successfully after user intervention.")

        browser.close()
        print("\nVerification PASSED: Interactive event creation workflow is working correctly.")

if __name__ == "__main__":
    run_verification()