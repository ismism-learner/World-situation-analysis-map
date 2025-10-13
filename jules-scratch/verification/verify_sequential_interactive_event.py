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
                    features: [
                        { type: "Feature", id: "test-country-1", properties: { NAME: "Testland" }, geometry: { type: "Polygon", coordinates: [ [ [0,0], [10,0], [10,10], [0,10], [0,0] ] ] } },
                        { type: "Feature", id: "test-country-2", properties: { NAME: "Fakeland" }, geometry: { type: "Polygon", coordinates: [ [ [20,20], [30,20], [30,30], [20,30], [20,20] ] ] } }
                    ]
                };
                processLayerData('countries', geojson, '110m');
                toggleLayer('countries', true);
            }
        """)

        # Wait for the layer to be rendered
        page.wait_for_selector(".layer-country", state="visible")


        # --- Test Case: Two Locations Not Found ---
        event_input = page.locator("#eventInput")
        add_event_btn = page.locator("#addEventBtn")
        picker_panel = page.locator("#location-picker-panel")
        picker_prompt = page.locator("#location-picker-prompt")
        missing_loc_name = page.locator("#missing-location-name")
        confirm_btn = page.locator("#confirm-location-btn")

        # 1. Input an event with two fake location names
        event_string = "2025-02-01;交易;Atlantis;to;El Dorado"
        event_input.fill(event_string)
        add_event_btn.click()

        # 2. Verify panel for Location 1 ("Atlantis")
        expect(picker_panel).to_be_visible(timeout=5000)
        expect(picker_prompt).to_contain_text("地点1")
        expect(missing_loc_name).to_have_text("Atlantis")
        page.screenshot(path='jules-scratch/verification/1_picker_for_loc1.png')
        print("Test Case 1 Passed: Panel appeared for Location 1.")

        # 3. Select the first location ("Testland")
        page.evaluate("""
            () => {
                const countries = d3.selectAll(".layer-country").nodes();
                for (const country of countries) {
                    if (country.__data__.properties.NAME === 'Testland') {
                        country.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                        break;
                    }
                }
            }
        """)
        confirm_btn.click()
        expect(picker_panel).to_be_hidden(timeout=2000)
        print("Test Case 2 Passed: Location 1 confirmed.")
        page.wait_for_timeout(500) # Wait for next step in queue

        # 4. Verify panel for Location 2 ("El Dorado")
        expect(picker_panel).to_be_visible(timeout=5000)
        expect(picker_prompt).to_contain_text("地点2")
        expect(missing_loc_name).to_have_text("El Dorado")
        page.screenshot(path='jules-scratch/verification/2_picker_for_loc2.png')
        print("Test Case 3 Passed: Panel appeared for Location 2.")

        # 5. Select the second location ("Fakeland")
        page.evaluate("""
            () => {
                const countries = d3.selectAll(".layer-country").nodes();
                for (const country of countries) {
                    if (country.__data__.properties.NAME === 'Fakeland') {
                        country.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                        break;
                    }
                }
            }
        """)
        confirm_btn.click()
        expect(picker_panel).to_be_hidden(timeout=2000)
        print("Test Case 4 Passed: Location 2 confirmed.")

        # 6. Verify the final connection is created
        expect(page.locator(".connection-group")).to_have_count(1, timeout=5000)
        expect(page.locator(".connection-label")).to_contain_text("2025-02-01, 交易, to")
        page.screenshot(path='jules-scratch/verification/3_final_connection.png')
        print("Test Case 5 Passed: Final connection created successfully.")

        browser.close()
        print("\nVerification PASSED: Sequential interactive event creation is working correctly.")

if __name__ == "__main__":
    run_verification()