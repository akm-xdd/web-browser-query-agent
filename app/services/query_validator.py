import google.generativeai as genai
from app.core.config import settings

class QueryValidator:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    async def validate_query(self, query: str) -> tuple[bool, str]:
        """
        Validate if the query is a valid search query
        Returns: (is_valid, message)
        """
        try:
            prompt = f"""
            You are a query validator for a web search agent. 
            Determine if the following query is a valid web search query.
            
            A valid query should be:
            - A question or request for information that can be searched on the web
            - Something that would return meaningful search results
            - Not a personal task or command (like "walk my pet", "add to grocery list")
            - It does NOT require private context (e.g., queries about specific people like "Rahul", exact times like "at 5 PM", or private locations). Generic terms like "my coworker" or "someone" are allowed.

            📌 Examples:

VALID:
  • "How to cook pasta"
  • "Best headphones under ₹5000"
  • "Why do dogs bark at night"
  • "How to schedule a Google Calendar meeting"
  • "Top restaurants in Gurgaon"
  • "Where is ice cream near Dwarka"
  • "Best cafes in Connaught Place"
  • "I am in Delhi, what are the best places to visit?"

INVALID:
  • "cook pasta" ← command
  • "walk my pet, buy groceries" ← multiple intents
  • "alksdj123@!!" ← gibberish
  • " " ← empty/whitespace
  • "" or [] or {{}} ← empty input
  • "123456" ← number-only
  • "schedule meeting with Raj tomorrow" ← too specific
  • "What is my IP address" ← depends on private context
  • "Open Spotify" ← action/command
  • "😭😭😭😭" ← emojis only

---

🧠 Edge Cases to Watch:
  - "How to meet John today" → ❌ INVALID (private context)
  - "How to meet someone professionally" → ✅ VALID (general)
  - "Top gyms near Saket" → ✅ VALID (public location-based)
  - "Find me the nearest ATM to my house" → ❌ INVALID (personalized)
  - "Weather in Delhi today" → ✅ VALID
  - "What’s Rahul’s phone number" → ❌ INVALID (private info)
  - "How do I send an email to my coworker?" ← generic role, valid

---
            
            Query: "{query}"
            
            Respond with only "VALID" or "INVALID" followed by a brief reason.
            Examples:
            - "Best places to visit in Delhi" → VALID - searchable information request
            - "walk my pet, add apples to grocery" → INVALID - personal tasks, not searchable
            """
            
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            if result.upper().startswith("VALID"):
                return True, "Query is valid for web search"
            else:
                return False, "This is not a valid search query"
                
        except Exception as e:
            return False, f"Error validating query: {str(e)}"