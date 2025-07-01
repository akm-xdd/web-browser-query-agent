import aiohttp
import asyncio
import google.generativeai as genai
from app.core.config import settings
from typing import List, Dict

class QueryClassifier:
    """Simple query classifier for better AI responses"""
    
    def classify_query(self, query: str) -> str:
        """Classify query type for better formatting"""
        query_lower = query.lower()
        
        # Recommendation queries
        if any(word in query_lower for word in ['best', 'top', 'recommend', 'should i buy', 'which is better']):
            return 'recommendation'
        
        # How-to queries
        if any(phrase in query_lower for phrase in ['how to', 'how do', 'steps to', 'guide', 'tutorial']):
            return 'how_to'
        
        # Comparison queries
        if any(word in query_lower for word in ['vs', 'versus', 'compare', 'difference', 'better than']):
            return 'comparison'
        
        # Location queries
        if any(phrase in query_lower for phrase in ['near me', ' in ', 'local', 'restaurants in', 'places in']):
            return 'location'
        
        # Factual queries
        if query_lower.startswith(('what is', 'what are', 'when did', 'where is', 'who is', 'why')):
            return 'factual'
        
        # News/current events
        if any(word in query_lower for word in ['latest', 'recent', 'news', 'today', 'current', 'updates']):
            return 'news'
        
        # Troubleshooting
        if any(word in query_lower for word in ['fix', 'solve', 'problem', 'error', 'not working', 'help']):
            return 'troubleshooting'
        
        return 'general'

class WebScraperClient:
    def __init__(self):
        self.scraper_url = "http://localhost:8001"  # Docker container URL
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.classifier = QueryClassifier()
    
    async def scrape_and_summarize(self, query: str) -> str:
        """Scrape web results and summarize them with optimizations"""
        try:
            # Reasonable timeout - give it time to work properly
            timeout = aiohttp.ClientTimeout(total=90)  # Increased back to 90s  
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.scraper_url}/scrape",
                    json={"query": query}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return f"Error: Failed to scrape results for '{query}'. Status: {response.status}, Details: {error_text}"
                    
                    data = await response.json()
                    results = data.get('results', [])
            
            if not results:
                return f"No results found for '{query}'. This might be due to search engine blocking or network issues."
            
            # Filter results more efficiently
            valid_results = [r for r in results if r.get('snippet') or r.get('content')]
            
            if not valid_results:
                return f"Found search results for '{query}' but could not extract meaningful content."
            
            # Prepare content for summarization (optimized)
            combined_content = self._prepare_content_for_summary(query, valid_results)
            
            # Summarize using Gemini with reasonable timeout
            try:
                summary = await asyncio.wait_for(
                    self._summarize_content(combined_content, query),
                    timeout=25.0  # Increased timeout for summarization
                )
                return summary
            except asyncio.TimeoutError:
                return f"Found results for '{query}' but summarization took too long. Here are the key findings from the search results: {self._create_fallback_summary(valid_results)}"
            
        except asyncio.TimeoutError:
            return f"Search timed out for '{query}'. The query might be too complex or there are network issues."
        except Exception as e:
            print(f"Error in scrape_and_summarize: {e}")
            return f"Error occurred while searching for '{query}': {str(e)}"
    
    def _prepare_content_for_summary(self, query: str, results: List[Dict]) -> str:
        """Prepare scraped content for summarization - optimized version"""
        content_parts = [f"Search Query: {query}\n\nTop search results:\n"]
        
        for i, result in enumerate(results[:5], 1):  # Back to 5 results for better coverage
            content_parts.append(f"\n--- Result {i} ---")
            content_parts.append(f"Title: {result.get('title', 'No title')}")
            content_parts.append(f"URL: {result.get('url', 'No URL')}")
            
            # Prioritize snippet over content if both exist (snippets are more concise)
            snippet = result.get('snippet', '')
            content = result.get('content', '')
            
            if snippet:
                content_parts.append(f"Summary: {snippet}")
            
            # Add content if available for richer context
            if content:
                # Increased content limit for better summarization
                content_parts.append(f"Content: {content[:1000]}")
        
        return "\n".join(content_parts)
    
    def _create_fallback_summary(self, results: List[Dict]) -> str:
        """Create a simple fallback summary without AI when summarization fails"""
        summary_parts = []
        for i, result in enumerate(results[:5], 1):  # Show all 5 results
            title = result.get('title', 'No title')
            snippet = result.get('snippet', '')
            url = result.get('url', '')
            
            summary_parts.append(f"{i}. {title}")
            if snippet:
                summary_parts.append(f"   {snippet[:200]}...")  # Show more snippet text
            summary_parts.append(f"   Source: {url}")
            summary_parts.append("")
        
        return "\n".join(summary_parts)
    
    async def _summarize_content(self, content: str, query: str) -> str:
        """Summarize the scraped content using Gemini with dynamic format based on query type"""
        try:
            # Classify query type for better formatting
            query_type = self.classifier.classify_query(query)
            
            # Create dynamic prompt based on query type
            base_prompt = f"""
            You are a helpful research assistant. Based on the search results below, provide a comprehensive and actionable answer to the user's query: "{query}"

            QUERY TYPE DETECTED: {query_type.upper()}
            """
            
            # Add specific instructions based on query type
            if query_type == 'recommendation':
                format_instructions = """
                FORMAT FOR RECOMMENDATIONS:
                • Start with a direct answer listing top 2-3 specific options
                • For each recommendation include: name/model, price range, key features, why it's good
                • Add a "Key Factors to Consider" section
                • Include where to buy or get more info
                • Use bullet points and clear structure
                """
            
            elif query_type == 'how_to':
                format_instructions = """
                FORMAT FOR HOW-TO:
                • Provide clear step-by-step instructions (numbered list)
                • Include any prerequisites or requirements
                • Add tips, warnings, or common mistakes to avoid
                • Mention tools or materials needed
                • Keep steps actionable and specific
                """
            
            elif query_type == 'comparison':
                format_instructions = """
                FORMAT FOR COMPARISONS:
                • Create clear side-by-side comparison
                • Highlight key differences and similarities
                • Include pros and cons for each option
                • Provide recommendation for different use cases
                • Use tables or structured format when helpful
                """
            
            elif query_type == 'location':
                format_instructions = """
                FORMAT FOR LOCATION QUERIES:
                • List specific places with names and addresses
                • Include ratings, hours, contact info when available
                • Mention key features (price range, specialties, etc.)
                • Add transportation/parking information
                • Group by area or category if relevant
                """
            
            elif query_type == 'factual':
                format_instructions = """
                FORMAT FOR FACTUAL QUERIES:
                • Start with a direct, concise answer
                • Provide context and background information
                • Include relevant dates, numbers, statistics
                • Add related information that might be useful
                • Structure with clear sections if topic is complex
                """
            
            elif query_type == 'news':
                format_instructions = """
                FORMAT FOR NEWS/CURRENT EVENTS:
                • Start with the most recent/important update
                • Provide timeline of key events
                • Include key people or organizations involved
                • Mention sources and dates
                • Add context about significance or impact
                """
            
            elif query_type == 'troubleshooting':
                format_instructions = """
                FORMAT FOR TROUBLESHOOTING:
                • Start with the most common/likely solution
                • Provide multiple approaches (basic to advanced)
                • Include diagnostic steps to identify the issue
                • Mention when to seek professional help
                • Add prevention tips for the future
                """
            
            else:  # general
                format_instructions = """
                FORMAT FOR GENERAL QUERIES:
                • Provide comprehensive information structured clearly
                • Use appropriate headers and bullet points
                • Include specific details, numbers, names when relevant
                • Structure logically based on the information found
                • Make it easy to scan and understand
                """
            
            full_prompt = f"""
            {base_prompt}
            
            {format_instructions}
            
            GENERAL GUIDELINES:
            • Be specific and actionable - avoid vague statements
            • Include concrete details: names, numbers, prices, dates
            • Use markdown formatting for better readability
            • Cite sources when mentioning specific claims
            • Keep the user's exact question in mind
            
            ---
            Search Results:
            {content[:4000]}
            
            Provide your response in the appropriate format for a {query_type} query:
            """
            
            response = self.model.generate_content(full_prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error in summarization: {e}")
            return f"Found results for '{query}' but failed to summarize them."