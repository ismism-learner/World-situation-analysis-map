from playwright.sync_api import sync_playwright, expect
import os

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        file_path = os.path.abspath('naturalearth_map_viewer_with_draggable_labels_fixed.html')
        page.goto(f'file://{file_path}')

        expect(page.locator("#globe")).to_be_visible(timeout=10000)
        page.evaluate("document.getElementById('header').style.display = 'none'")
        page.evaluate("document.querySelector('.graticule').style.display = 'none'")


        # --- Create and verify a connection label ---
        conn_id = page.evaluate("""
            () => {
                projection.rotate([-90, -30, 0]);
                const point1 = [-74.0060, 40.7128]; // NYC
                const point2 = [116.4074, 39.9042];  // Beijing
                const conn = drawConnection(point1, point2, 'Connection Label', true);
                scheduleUpdate();
                return conn.id;
            }
        """)

        conn_label_group = page.locator(f"#{conn_id} .label-group")
        conn_connector_line = page.locator(f"#{conn_id} .connection-label-connector")

        # --- Drag connection label to make connector line visible ---
        conn_label_group.hover()
        page.mouse.down()
        page.mouse.move(200, 200)
        page.mouse.up()
        expect(conn_connector_line).to_be_visible()

        # --- Drag connection label again to verify hide/show ---
        conn_label_group.hover()
        page.mouse.down()
        expect(conn_connector_line).to_be_hidden()
        page.mouse.move(250, 250)
        page.screenshot(path='jules-scratch/verification/verification_dragging.png')
        page.mouse.up()
        expect(conn_connector_line).to_be_visible()

        # --- Create and verify a pin label ---
        pin_id = page.evaluate("""
            () => {
                const coords = [-20, 30]; // More central coordinates
                const pin = createPin(coords, 'Pin Label', true);
                pin.label = 'Pin Label';
                updatePinLabel(pin);
                scheduleUpdate();
                return pin.id;
            }
        """)

        pin_label_group = page.locator(f"#{pin_id} .pin-label")
        pin_connector_line = page.locator(f"#{pin_id} .pin-label-line")

        # --- Edit pin label ---
        pin_label_group.dblclick()
        input_selector = ".label-input"
        expect(page.locator(input_selector)).to_be_visible()
        page.locator(input_selector).fill("New Pin Label")
        page.keyboard.press("Enter")
        expect(page.locator(input_selector)).to_be_hidden()
        expect(pin_label_group).to_contain_text("New Pin Label")

        # --- Drag pin label ---
        pin_label_group.hover()
        page.mouse.down()
        page.mouse.move(300, 300)
        page.mouse.up()
        expect(pin_connector_line).to_be_visible()

        pin_label_group.hover()
        page.mouse.down()
        expect(pin_connector_line).to_be_hidden()
        page.mouse.move(350, 350)
        page.screenshot(path='jules-scratch/verification/verification_final.png')
        page.mouse.up()
        expect(pin_connector_line).to_be_visible()

        browser.close()
        print("Verification successful: Connector lines are hidden during drag and reappear after.")

if __name__ == "__main__":
    run_verification()