from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryValidationResponse, SimilarQueryResponse, ProcessQueryResponse, RetryRequest
from app.services.query_validator import QueryValidator
from app.services.similarity_checker import SimilarityChecker
from app.services.web_scraper import WebScraperClient
from app.services.cache_manager import query_cache

router = APIRouter()
validator = QueryValidator()
similarity_checker = SimilarityChecker()
web_scraper = WebScraperClient()

@router.post("/validate-query", response_model=QueryValidationResponse)
async def validate_query(request: QueryRequest):
    try:
        is_valid, message = await validator.validate_query(request.query)
        
        return QueryValidationResponse(
            is_valid=is_valid,
            message=message,
            query=request.query
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/check-similarity", response_model=SimilarQueryResponse)
async def check_similarity(request: QueryRequest):
    try:
        found_similar, similar_query, similarity_score, cached_result = await similarity_checker.check_similarity(request.query)
        
        return SimilarQueryResponse(
            found_similar=found_similar,
            similar_query=similar_query if found_similar else None,
            similarity_score=similarity_score if found_similar else None,
            cached_result=cached_result if found_similar else None
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/process-query", response_model=ProcessQueryResponse)
async def process_query(request: QueryRequest):
    """
    Complete query processing: validation + similarity check
    """
    try:
        # Step 1: Validate query
        is_valid, validation_message = await validator.validate_query(request.query)
        
        if not is_valid:
            return ProcessQueryResponse(
                is_valid=False,
                validation_message=validation_message,
                found_similar=False,
                result=None,
                query=request.query
            )
        
        # Step 2: Check similarity
        found_similar, similar_query, similarity_score, cached_result = await similarity_checker.check_similarity(request.query)
        
        if found_similar:
            return ProcessQueryResponse(
                is_valid=True,
                validation_message=validation_message,
                found_similar=True,
                similar_query=similar_query,
                similarity_score=similarity_score,
                result=cached_result,
                query=request.query
            )
        
        # Step 3: New query - scrape web and summarize
        print(f"Processing new query: {request.query}")
        result = await web_scraper.scrape_and_summarize(request.query)
        
        # Cache this result for future queries
        similarity_checker.cache_query_result(request.query, result)
        
        return ProcessQueryResponse(
            is_valid=True,
            validation_message=validation_message,
            found_similar=False,
            result=result,
            query=request.query
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/cache-stats")
async def get_cache_stats():
    return query_cache.get_cache_stats()

@router.delete("/clear-cache")
async def clear_cache():
    query_cache.clear_cache()
    return {"message": "Cache cleared successfully"}


@router.post("/cleanup-cache")
async def cleanup_cache(max_entries: int = 50):
    query_cache.cleanup_old_entries(max_entries)
    return {"message": f"Cache cleaned up, keeping latest {max_entries} entries"}

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Web Browser Query Agent"}