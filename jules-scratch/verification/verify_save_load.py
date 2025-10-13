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

        # --- Step 1: Add content to the map ---
        page.evaluate("""
            () => {
                // Create a pin
                const pin = createPin([-58.38, -34.60], "Buenos Aires Pin"); // Buenos Aires
                pin.labelXOffset = 20;
                pin.labelYOffset = -30;
                updatePinLabel(pin);

                // Create a connection
                const conn = drawConnection(
                    [-74.0060, 40.7128], // New York
                    [116.4074, 39.9042], // Beijing
                    "NYC -> Beijing",
                    true,
                    "rgb(255, 0, 255)" // Magenta color
                );
                conn.labelXOffset = -50;
                conn.labelYOffset = 25;
                updateConnectionLabel(conn);
                scheduleUpdate();
            }
        """)

        # Verify content was added
        expect(page.locator(".pin-group")).to_have_count(1)
        expect(page.locator(".connection-group")).to_have_count(1)
        expect(page.locator(".pin-label-text")).to_contain_text("Buenos Aires Pin")
        expect(page.locator(".connection-label")).to_contain_text("NYC -> Beijing")

        page.screenshot(path='jules-scratch/verification/1_before_export.png')
        print("Step 1: Content added to map successfully.")

        # --- Step 2: Export the map state ---
        # Use Playwright's download handling
        with page.expect_download() as download_info:
            page.locator("#exportEvents").click()

        download = download_info.value
        # Save the downloaded file to our scratch directory
        saved_path = f"jules-scratch/verification/{download.suggested_filename}"
        download.save_as(saved_path)
        print(f"Step 2: Map state exported to {saved_path}")

        # --- Step 3: Clear the map and verify it's empty ---
        page.locator("#clearAllMarkings").click()
        expect(page.locator(".pin-group")).to_have_count(0)
        expect(page.locator(".connection-group")).to_have_count(0)
        page.screenshot(path='jules-scratch/verification/2_after_clear.png')
        print("Step 3: Map cleared successfully.")

        # --- Step 4: Import the saved state ---
        # Use Playwright's file chooser to upload the file
        with page.expect_file_chooser() as fc_info:
            page.locator("#importEvents").click()
        file_chooser = fc_info.value
        file_chooser.set_files(saved_path)
        print(f"Step 4: Importing map state from {saved_path}")

        # --- Step 5: Verify the map is restored ---
        expect(page.locator(".pin-group")).to_have_count(1, timeout=10000)
        expect(page.locator(".connection-group")).to_have_count(1)

        # Verify pin content
        expect(page.locator(".pin-label-text")).to_contain_text("Buenos Aires Pin")

        # Verify connection content
        expect(page.locator(".connection-label")).to_contain_text("NYC -> Beijing")

        # Verify connection color
        arc_color = page.locator(".connection-arc").first.evaluate("el => el.style.stroke")
        expect(arc_color).to_equal("rgb(255, 0, 255)")

        page.screenshot(path='jules-scratch/verification/3_after_import.png')
        print("Step 5: Map state restored successfully.")

        browser.close()
        print("\nVerification PASSED: Export and Import functionality is working correctly.")

if __name__ == "__main__":
    run_verification()