"""
LEGIONGASPER v2.0 - Browser Automation Tool
CDP-based browser control with Playwright/Selenium support
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class BrowserType(Enum):
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"

@dataclass
class BrowserSession:
    """Browser session state"""
    session_id: str
    browser_type: BrowserType
    url: Optional[str] = None
    title: Optional[str] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class BrowserController:
    """CDP-based browser controller"""
    
    def __init__(self):
        self.sessions: Dict[str, BrowserSession] = {}
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        
    async def initialize(self, browser_type: BrowserType = BrowserType.CHROMIUM, headless: bool = True):
        """Initialize browser instance"""
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            
            if browser_type == BrowserType.CHROMIUM:
                self._browser = await self._playwright.chromium.launch(headless=headless)
            elif browser_type == BrowserType.FIREFOX:
                self._browser = await self._playwright.firefox.launch(headless=headless)
            else:
                self._browser = await self._playwright.webkit.launch(headless=headless)
            
            self._context = await self._browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            self._page = await self._context.new_page()
            
            return True
        except ImportError:
            return False
        except Exception as e:
            print(f"Browser initialization error: {e}")
            return False
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        """Navigate to URL"""
        if not self._page:
            return {"error": "Browser not initialized"}
        
        try:
            response = await self._page.goto(url, wait_until=wait_until)
            return {
                "url": self._page.url,
                "title": await self._page.title(),
                "status": response.status if response else None
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def screenshot(self, path: Optional[str] = None, full_page: bool = False) -> Dict[str, Any]:
        """Take screenshot"""
        if not self._page:
            return {"error": "Browser not initialized"}
        
        try:
            if path:
                await self._page.screenshot(path=path, full_page=full_page)
                return {"path": path, "success": True}
            else:
                screenshot = await self._page.screenshot(full_page=full_page)
                import base64
                return {
                    "base64": base64.b64encode(screenshot).decode(),
                    "success": True
                }
        except Exception as e:
            return {"error": str(e)}
    
    async def execute_js(self, script: str) -> Dict[str, Any]:
        """Execute JavaScript in browser"""
        if not self._page:
            return {"error": "Browser not initialized"}
        
        try:
            result = await self._page.evaluate(script)
            return {"result": result, "success": True}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_dom(self) -> Dict[str, Any]:
        """Get page DOM"""
        if not self._page:
            return {"error": "Browser not initialized"}
        
        try:
            html = await self._page.content()
            return {"html": html, "success": True}
        except Exception as e:
            return {"error": str(e)}
    
    async def click(self, selector: str) -> Dict[str, Any]:
        """Click element"""
        if not self._page:
            return {"error": "Browser not initialized"}
        
        try:
            await self._page.click(selector)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    
    async def fill(self, selector: str, value: str) -> Dict[str, Any]:
        """Fill input field"""
        if not self._page:
            return {"error": "Browser not initialized"}
        
        try:
            await self._page.fill(selector, value)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    
    async def close(self):
        """Close browser"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

# Global controller instance
_controller = BrowserController()

async def navigate(url: str, **kwargs) -> Dict[str, Any]:
    """Navigate to URL"""
    return await _controller.navigate(url, **kwargs)

async def screenshot(**kwargs) -> Dict[str, Any]:
    """Take screenshot"""
    return await _controller.screenshot(**kwargs)

async def execute_js(script: str) -> Dict[str, Any]:
    """Execute JavaScript"""
    return await _controller.execute_js(script)

async def get_dom() -> Dict[str, Any]:
    """Get DOM"""
    return await _controller.get_dom()
