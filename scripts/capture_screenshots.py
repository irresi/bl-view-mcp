#!/usr/bin/env python3
"""Capture screenshots from HTML dashboards using Playwright."""

import os
from pathlib import Path

# HTML files to capture (filename, output_name)
DASHBOARDS = [
    ("tool1.html", "demo_optimization.png"),
    ("tool2.html", "demo_backtest.png"),
    ("tool3.html", "demo_strategy.png"),
    ("tool4.html", "demo_correlation.png"),
    ("tool5.html", "demo_sensitivity.png"),
]

def main():
    from playwright.sync_api import sync_playwright

    # Paths
    project_root = Path(__file__).parent.parent
    dashboards_dir = project_root / "examples" / "dashboards"
    screenshots_dir = project_root / "docs" / "screenshots"

    # Create output directory
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    print("📸 Capturing dashboard screenshots...\n")

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for html_file, png_file in DASHBOARDS:
            html_path = dashboards_dir / html_file
            png_path = screenshots_dir / png_file

            if not html_path.exists():
                print(f"  ⚠️  {html_file} not found, skipping...")
                continue

            # Create page with specific viewport
            page = browser.new_page(viewport={"width": 1200, "height": 900})

            # Navigate to file
            page.goto(f"file://{html_path.absolute()}")

            # Wait for any animations/rendering
            page.wait_for_timeout(500)

            # Take full page screenshot
            page.screenshot(path=str(png_path), full_page=True)

            print(f"  ✅ {html_file} → {png_file}")

            page.close()

        browser.close()

    print(f"\n🎉 Done! Screenshots saved to: {screenshots_dir}")


if __name__ == "__main__":
    main()
