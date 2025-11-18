#!/usr/bin/env python3
"""
Endpoint Discovery Tool for GSU CS Department
Helps find relevant pages automatically by analyzing site structure
"""

import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Set
import time

class EndpointDiscovery:
    def __init__(self, base_domain: str = "csds.gsu.edu"):
        self.base_domain = base_domain
        self.base_url = f"https://{base_domain}"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def discover_from_sitemap(self) -> List[str]:
        """Extract URLs from sitemap"""
        urls = []
        try:
            # Try main sitemap first
            response = self.session.get(f"{self.base_url}/sitemap.xml", timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                # Handle different sitemap formats
                for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                    loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc is not None:
                        urls.append(loc.text)
                
                # Also check for sitemap index
                for sitemap_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                    loc = sitemap_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc is not None:
                        # Get sub-sitemap
                        sub_response = self.session.get(loc.text, timeout=10)
                        if sub_response.status_code == 200:
                            sub_root = ET.fromstring(sub_response.content)
                            for url_elem in sub_root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                                sub_loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                                if sub_loc is not None:
                                    urls.append(sub_loc.text)
        except Exception as e:
            print(f"Error reading sitemap: {e}")
        
        return urls
    
    def discover_from_crawling(self, start_urls: List[str], max_depth: int = 2) -> Set[str]:
        """Crawl starting from given URLs to find more pages"""
        discovered = set()
        to_visit = [(url, 0) for url in start_urls]
        visited = set()
        
        while to_visit:
            url, depth = to_visit.pop(0)
            
            if url in visited or depth > max_depth:
                continue
                
            visited.add(url)
            
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find all links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(url, href)
                        
                        # Only include URLs from the same domain
                        if urlparse(full_url).netloc == self.base_domain:
                            discovered.add(full_url)
                            if depth < max_depth:
                                to_visit.append((full_url, depth + 1))
                
                time.sleep(0.5)  # Be polite
                
            except Exception as e:
                print(f"Error crawling {url}: {e}")
        
        return discovered
    
    def filter_relevant_urls(self, urls: List[str], keywords: List[str]) -> Dict[str, List[str]]:
        """Filter URLs by relevance using keywords"""
        categories = {
            'faculty': ['faculty', 'staff', 'people', 'directory', 'professor', 'research', 'bio'],
            'research': ['research', 'lab', 'project', 'publication', 'area'],
            'graduate': ['graduate', 'grad', 'phd', 'masters', 'ms', 'doctoral'],
            'admissions': ['admission', 'apply', 'application', 'requirement', 'deadline'],
            'courses': ['course', 'curriculum', 'class', 'schedule'],
            'general': ['about', 'overview', 'program', 'department']
        }
        
        results = {category: [] for category in categories}
        
        for url in urls:
            url_lower = url.lower()
            for category, category_keywords in categories.items():
                if any(keyword in url_lower for keyword in category_keywords):
                    results[category].append(url)
                    break
        
        return results
    
    def suggest_endpoints(self) -> Dict[str, List[str]]:
        """Main method to suggest relevant endpoints"""
        print("🔍 Discovering endpoints from sitemap...")
        sitemap_urls = self.discover_from_sitemap()
        print(f"Found {len(sitemap_urls)} URLs in sitemap")
        
        print("🕷️ Crawling for additional URLs...")
        current_urls = [
            "https://csds.gsu.edu/graduate/",
            "https://csds.gsu.edu/graduate-faqs/", 
            "https://cas.gsu.edu/program/computer-science-phd/",
            "https://csds.gsu.edu/research/"
        ]
        crawled_urls = self.discover_from_crawling(current_urls, max_depth=1)
        print(f"Found {len(crawled_urls)} URLs from crawling")
        
        # Combine all URLs
        all_urls = list(set(sitemap_urls + list(crawled_urls)))
        
        # Filter to CS department URLs only
        cs_urls = [url for url in all_urls if 'csds.gsu.edu' in url or 'computer-science' in url]
        
        print(f"🎯 Filtering {len(cs_urls)} CS-related URLs...")
        categorized = self.filter_relevant_urls(cs_urls, [])
        
        return categorized

def main():
    discovery = EndpointDiscovery()
    suggestions = discovery.suggest_endpoints()
    
    print("\n" + "="*60)
    print("📋 SUGGESTED ENDPOINTS BY CATEGORY")
    print("="*60)
    
    for category, urls in suggestions.items():
        if urls:
            print(f"\n🔹 {category.upper()} ({len(urls)} URLs):")
            for url in urls[:10]:  # Show first 10
                print(f"  • {url}")
            if len(urls) > 10:
                print(f"  ... and {len(urls)-10} more")
    
    print(f"\n💡 RECOMMENDATION:")
    print("Add these high-value endpoints to your document_processor.py:")
    
    # Suggest most valuable endpoints
    priority_urls = []
    for category in ['faculty', 'research', 'graduate']:
        priority_urls.extend(suggestions[category][:3])
    
    print("\nHigh Priority:")
    for url in priority_urls[:8]:
        print(f'    "{url}",')

if __name__ == "__main__":
    main()