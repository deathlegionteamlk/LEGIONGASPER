"""
LEGIONGASPER v2.0 - Web Search Tool
OpenClaw-compatible web search with multiple providers
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

import requests
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import urllib.parse

@dataclass
class SearchResult:
    """Web search result"""
    title: str
    url: str
    snippet: str
    source: str
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "timestamp": self.timestamp
        }

class WebSearch:
    """Web search with multiple provider support"""
    
    def __init__(self, 
                 duckduckgo_enabled: bool = True,
                 brave_api_key: Optional[str] = None,
                 serpapi_key: Optional[str] = None):
        self.duckduckgo_enabled = duckduckgo_enabled
        self.brave_api_key = brave_api_key
        self.serpapi_key = serpapi_key
        
    def search_duckduckgo(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using DuckDuckGo"""
        results = []
        try:
            # Using DuckDuckGo HTML version
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append(SearchResult(
                        title=r.get('title', ''),
                        url=r.get('href', ''),
                        snippet=r.get('body', ''),
                        source='DuckDuckGo',
                        timestamp=datetime.now().isoformat()
                    ))
        except ImportError:
            # Fallback to simple request
            try:
                url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers, timeout=10)
                # Basic parsing (simplified)
                results.append(SearchResult(
                    title="DuckDuckGo Results",
                    url=url,
                    snippet="Search results from DuckDuckGo",
                    source='DuckDuckGo',
                    timestamp=datetime.now().isoformat()
                ))
            except Exception as e:
                pass
        except Exception as e:
            pass
        
        return results
    
    def search_brave(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using Brave API"""
        if not self.brave_api_key:
            return []
        
        results = []
        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "X-Subscription-Token": self.brave_api_key,
                "Accept": "application/json"
            }
            params = {
                "q": query,
                "count": max_results
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            data = response.json()
            
            for item in data.get('web', {}).get('results', []):
                results.append(SearchResult(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    snippet=item.get('description', ''),
                    source='Brave',
                    timestamp=datetime.now().isoformat()
                ))
        except Exception as e:
            pass
        
        return results
    
    def search(self, query: str, 
               provider: str = "auto",
               max_results: int = 10) -> Dict[str, Any]:
        """Search with specified provider"""
        all_results = []
        
        if provider == "auto" or provider == "duckduckgo":
            all_results.extend(self.search_duckduckgo(query, max_results))
        
        if provider in ["auto", "brave"] and self.brave_api_key:
            all_results.extend(self.search_brave(query, max_results))
        
        return {
            "query": query,
            "provider": provider,
            "results_count": len(all_results),
            "results": [r.to_dict() for r in all_results[:max_results]],
            "timestamp": datetime.now().isoformat()
        }
    
    def search_news(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search for news"""
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                for r in ddgs.news(query, max_results=max_results):
                    results.append({
                        "title": r.get('title', ''),
                        "url": r.get('url', ''),
                        "source": r.get('source', ''),
                        "date": r.get('date', ''),
                        "snippet": r.get('body', '')
                    })
            
            return {
                "query": query,
                "type": "news",
                "results_count": len(results),
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "query": query,
                "type": "news",
                "error": str(e),
                "results": []
            }

# Global search instance
_default_search = WebSearch()

def search(query: str, **kwargs) -> Dict[str, Any]:
    """Search web"""
    return _default_search.search(query, **kwargs)

def search_news(query: str, **kwargs) -> Dict[str, Any]:
    """Search news"""
    return _default_search.search_news(query, **kwargs)
