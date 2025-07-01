from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scraper_service import WebScraper
from typing import List, Dict
import uvicorn

app = FastAPI(title="Web Scraper Service", version="1.0.0")
scraper = WebScraper()

class ScrapeRequest(BaseModel):
    query: str

class ScrapeResponse(BaseModel):
    query: str
    results: List[Dict[str, str]]
    total_results: int

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_web(request: ScrapeRequest):
    """Scrape web results for a query"""
    try:
        results = await scraper.scrape_search_results(request.query)
        
        return ScrapeResponse(
            query=request.query,
            results=results,
            total_results=len(results)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Web Scraper"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)