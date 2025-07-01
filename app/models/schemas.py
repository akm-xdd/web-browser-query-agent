from pydantic import BaseModel
from typing import Optional, List

class QueryRequest(BaseModel):
    query: str
    force_refresh: bool = False

class RetryRequest(BaseModel):
    query: str
    max_retries: int = 3

class QueryValidationResponse(BaseModel):
    is_valid: bool
    message: str
    query: Optional[str] = None

class SimilarQueryResponse(BaseModel):
    found_similar: bool
    similar_query: Optional[str] = None
    similarity_score: Optional[float] = None
    cached_result: Optional[str] = None

class ProcessQueryResponse(BaseModel):
    is_valid: bool
    validation_message: str
    found_similar: bool
    similar_query: Optional[str] = None
    similarity_score: Optional[float] = None
    result: Optional[str] = None
    query: str