import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import List, Dict
import re
import time

class WebScraper:
    def __init__(self):
        self.max_results = 5
        self.search_timeout = 30000  # Keep original timeout for search
        self.page_timeout = 30000    # Increased timeout for page loading
        self.retry_count = 1         
        self.max_concurrent_scrapes = 3  # Limit concurrent scraping
    
    async def search_duckduckgo(self, query: str) -> List[Dict[str, str]]:
        """Search DuckDuckGo and return top results (fallback)"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-images', '--disable-javascript']
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()
                
                # Block images and unnecessary resources
                await page.route("**/*.{png,jpg,jpeg,gif,webp,svg,css,woff,woff2}", lambda route: route.abort())
                
                # Search on DuckDuckGo
                search_url = f"https://duckduckgo.com/?q={query}"
                await page.goto(search_url, timeout=self.search_timeout)
                
                # Wait for results with reasonable timeout
                await page.wait_for_selector('[data-testid="result"]', timeout=15000)
                
                # Extract search results
                results = []
                search_results = await page.query_selector_all('[data-testid="result"]')
                
                for result in search_results[:self.max_results]:
                    try:
                        # Extract title
                        title_element = await result.query_selector('h2 a')
                        title = await title_element.inner_text() if title_element else "No title"
                        
                        # Extract URL
                        url = await title_element.get_attribute('href') if title_element else ""
                        
                        # Extract snippet
                        snippet_element = await result.query_selector('[data-result="snippet"]')
                        snippet = await snippet_element.inner_text() if snippet_element else ""
                        
                        if title and url:
                            results.append({
                                'title': title.strip(),
                                'url': url.strip(),
                                'snippet': snippet.strip()
                            })
                    except Exception as e:
                        print(f"Error extracting DuckDuckGo result: {e}")
                        continue
                
                await browser.close()
                return results
                
        except Exception as e:
            print(f"Error searching DuckDuckGo: {e}")
            return []
    
    async def search_google(self, query: str) -> List[Dict[str, str]]:
        """Search Google and return top results"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-images', '--disable-javascript']
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
                page = await context.new_page()
                
                # Block images and unnecessary resources
                await page.route("**/*.{png,jpg,jpeg,gif,webp,svg,css,woff,woff2}", lambda route: route.abort())
                
                # Search on Google
                search_url = f"https://www.google.com/search?q={query}&num=10&hl=en"
                await page.goto(search_url, timeout=self.search_timeout)
                
                # Wait for results with reasonable timeout
                try:
                    await page.wait_for_selector('div.g, .g', timeout=15000)
                except:
                    await page.wait_for_selector('[data-ved]', timeout=12000)
                
                # Extract search results
                results = []
                search_results = await page.query_selector_all('div.g')
                
                for result in search_results[:self.max_results]:
                    try:
                        # Extract title
                        title_element = await result.query_selector('h3')
                        title = await title_element.inner_text() if title_element else "No title"
                        
                        # Extract URL
                        link_element = await result.query_selector('a')
                        url = await link_element.get_attribute('href') if link_element else ""
                        
                        # Extract snippet - try multiple selectors
                        snippet = ""
                        snippet_selectors = [
                            '.VwiC3b', '.s3v9rd', '.st', '[data-ved] span'
                        ]
                        
                        for selector in snippet_selectors:
                            snippet_element = await result.query_selector(selector)
                            if snippet_element:
                                snippet = await snippet_element.inner_text()
                                break
                        
                        if title and url and not url.startswith('/search'):
                            results.append({
                                'title': title.strip(),
                                'url': url.strip(),
                                'snippet': snippet.strip()
                            })
                    except Exception as e:
                        print(f"Error extracting Google result: {e}")
                        continue
                
                await browser.close()
                return results
                
        except Exception as e:
            print(f"Error searching Google: {e}")
            return []
    
    async def scrape_page_content(self, url: str, semaphore: asyncio.Semaphore) -> str:
        """Scrape content from a single page with concurrency control - no aggressive timeouts"""
        async with semaphore:  # Limit concurrent requests
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-images']
                    )
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    )
                    page = await context.new_page()
                    
                    # Block only images for faster loading, keep CSS/JS for better content extraction
                    await page.route("**/*.{png,jpg,jpeg,gif,webp,svg,mp4,mp3,pdf}", lambda route: route.abort())
                    
                    # Use reasonable timeout for page loading
                    await page.goto(url, timeout=self.page_timeout)
                    
                    # Wait for content to load properly
                    try:
                        await page.wait_for_load_state('domcontentloaded', timeout=10000)
                    except:
                        pass  # Continue even if timeout, we might still have some content
                    
                    # Get page content
                    content = await page.content()
                    
                    # Extract text using BeautifulSoup with better content prioritization
                    soup = BeautifulSoup(content, 'lxml')  # Use lxml for faster parsing
                    
                    # Remove script and style elements but keep more content
                    for script in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript"]):
                        script.decompose()
                    
                    # Try to extract structured content first (articles, main content)
                    main_content = ""
                    for selector in ['article', 'main', '[role="main"]', '.content', '.post-content', '.article-content']:
                        main_element = soup.select_one(selector)
                        if main_element:
                            main_content = main_element.get_text()
                            break
                    
                    # Fallback to full page text if no main content found
                    if not main_content:
                        main_content = soup.get_text()
                    
                    # Clean up text more efficiently
                    lines = (line.strip() for line in main_content.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk and len(chunk) > 10)  # Filter out very short chunks
                    
                    await browser.close()
                    
                    # Keep substantial content for better summarization
                    return text[:5000] if text else ""
                    
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                return ""
    
    async def scrape_search_results(self, query: str) -> List[Dict[str, str]]:
        """Main method to search and scrape content with optimizations"""
        start_time = time.time()
        print(f"Starting search for: {query}")

        # Try DuckDuckGo first (usually faster than Google)
        search_results = await self.search_duckduckgo(query)

        # If DuckDuckGo fails, try Google
        if not search_results:
            print("DuckDuckGo search failed, trying Google...")
            search_results = await self.search_google(query)

        if not search_results:
            print("Both search engines failed")
            return []
        
        search_time = time.time() - start_time
        print(f"Found {len(search_results)} search results in {search_time:.2f}s")
        
        # Create semaphore to limit concurrent scraping
        semaphore = asyncio.Semaphore(self.max_concurrent_scrapes)
        
        # Scrape content concurrently with limited concurrency
        scrape_start = time.time()
        tasks = []
        for result in search_results:
            task = self.scrape_page_content_with_result(result, semaphore)
            tasks.append(task)
        
        # Wait for all scraping tasks with generous timeout
        try:
            enriched_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), 
                timeout=60.0  # Increased timeout to allow proper scraping
            )
            
            # Filter out exceptions and empty results
            valid_results = []
            for result in enriched_results:
                if isinstance(result, dict) and result.get('title'):
                    valid_results.append(result)
            
            scrape_time = time.time() - scrape_start
            total_time = time.time() - start_time
            print(f"Scraping completed in {scrape_time:.2f}s, total time: {total_time:.2f}s")
            print(f"Successfully scraped {len(valid_results)} results")
            
            return valid_results
            
        except asyncio.TimeoutError:
            print("Scraping timed out, returning partial results")
            return search_results  # Return at least the search results with snippets
    
    async def scrape_page_content_with_result(self, result: Dict[str, str], semaphore: asyncio.Semaphore) -> Dict[str, str]:
        """Helper method to scrape content and return enriched result"""
        try:
            content = await self.scrape_page_content(result['url'], semaphore)
            return {
                'title': result['title'],
                'url': result['url'],
                'snippet': result['snippet'],
                'content': content
            }
        except Exception as e:
            print(f"Error processing {result['url']}: {e}")
            # Return original result without content
            return {
                'title': result['title'],
                'url': result['url'],
                'snippet': result['snippet'],
                'content': ""
            }