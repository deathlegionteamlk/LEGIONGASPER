import asyncio
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from typing import Optional, Dict, Any, List
import json
from datetime import datetime

class BrowserAutomation:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.history: List[Dict[str, Any]] = []
        
    async def initialize(self, headless: bool = True) -> bool:
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=headless)
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = await self.context.new_page()
            return True
        except Exception as e:
            print(f"Browser init failed: {e}")
            return False
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        if not self.page:
            return {"success": False, "error": "Browser not initialized"}
        try:
            response = await self.page.goto(url, wait_until=wait_until)
            title = await self.page.title()
            self.history.append({"action": "navigate", "url": url, "time": datetime.now().isoformat()})
            return {
                "success": True,
                "url": url,
                "title": title,
                "status": response.status if response else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def click(self, selector: str) -> Dict[str, Any]:
        try:
            await self.page.click(selector)
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        try:
            await self.page.fill(selector, text)
            return {"success": True, "selector": selector, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_text(self, selector: str) -> Dict[str, Any]:
        try:
            text = await self.page.inner_text(selector)
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def screenshot(self, path: Optional[str] = None) -> Dict[str, Any]:
        try:
            if path:
                await self.page.screenshot(path=path, full_page=True)
            screenshot_bytes = await self.page.screenshot(full_page=True)
            return {"success": True, "path": path, "size": len(screenshot_bytes)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def scroll(self, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        try:
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{amount})")
            return {"success": True, "direction": direction, "amount": amount}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_links(self) -> List[Dict[str, str]]:
        try:
            links = await self.page.query_selector_all('a')
            results = []
            for link in links[:50]:
                href = await link.get_attribute('href')
                text = await link.inner_text()
                if href:
                    results.append({"text": text.strip()[:100], "href": href})
            return results
        except Exception as e:
            return []
    
    async def search_google(self, query: str) -> Dict[str, Any]:
        await self.navigate(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        results = await self.page.query_selector_all('div.g')
        output = []
        for result in results[:10]:
            try:
                title_elem = await result.query_selector('h3')
                title = await title_elem.inner_text() if title_elem else ""
                link_elem = await result.query_selector('a')
                link = await link_elem.get_attribute('href') if link_elem else ""
                snippet_elem = await result.query_selector('div.VwiC3b')
                snippet = await snippet_elem.inner_text() if snippet_elem else ""
                output.append({"title": title, "link": link, "snippet": snippet})
            except:
                continue
        return {"success": True, "results": output}
    
    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

browser = BrowserAutomation()
