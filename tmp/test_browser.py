#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '/app/legiongasper_framework_0813')

from tools.browser import BrowserAutomation

async def test_browser():
    print("=" * 60)
    print("BROWSER AUTOMATION TEST")
    print("=" * 60)
    
    browser = BrowserAutomation()
    
    # Test 1: Initialize browser
    print("\n[1/4] Initializing browser (headless)...")
    success = await browser.initialize(headless=True)
    if not success:
        print("FAILED: Browser initialization failed")
        return False
    print("SUCCESS: Browser initialized")
    
    # Test 2: Navigate to example.com
    print("\n[2/4] Navigating to https://example.com...")
    result = await browser.navigate("https://example.com")
    if not result.get("success"):
        print(f"FAILED: Navigation failed - {result.get('error')}")
        await browser.close()
        return False
    print(f"SUCCESS: Navigated to {result['url']}")
    print(f"  Title: {result['title']}")
    print(f"  Status: {result['status']}")
    
    # Test 3: Take screenshot
    print("\n[3/4] Taking screenshot...")
    result = await browser.screenshot(path="/app/legiongasper_framework_0813/tmp/test_screenshot.png")
    if not result.get("success"):
        print(f"FAILED: Screenshot failed - {result.get('error')}")
        await browser.close()
        return False
    print(f"SUCCESS: Screenshot saved ({result['size']} bytes)")
    
    # Test 4: Get page text (h1)
    print("\n[4/4] Extracting page content...")
    result = await browser.get_text("h1")
    if not result.get("success"):
        print(f"FAILED: Text extraction failed - {result.get('error')}")
        await browser.close()
        return False
    print(f"SUCCESS: Found text: '{result['text']}'")
    
    # Cleanup
    await browser.close()
    
    print("\n" + "=" * 60)
    print("ALL BROWSER TESTS PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = asyncio.run(test_browser())
    sys.exit(0 if success else 1)
