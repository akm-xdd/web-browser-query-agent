# Web Browser Query Agent - Backend

An intelligent web search agent that validates user queries, detects similar cached queries using AI embeddings, and scrapes the web for fresh results when needed.

## 🏗️ Architecture Overview

```
┌─────────────────┐
│   USER QUERY    │
└─────────┬───────┘
          ▼
    ┌──────────┐
    │ VALIDATE │ ──→ ❌ Invalid Query
    └─────┬────┘
          ▼ ✅ Valid
    ┌──────────────┐
    │ CHECK CACHE  │ ──→ 💾 Return Cached Result
    └─────┬────────┘
          ▼ ❌ Cache Miss
    ┌──────────────┐
    │ WEB SCRAPING │ (Playwright + Docker)
    └─────┬────────┘
          ▼
    ┌──────────────┐
    │ AI SUMMARY   │ (Gemini AI)
    └─────┬────────┘
          ▼
    ┌──────────────┐
    │ CACHE & SHOW │
    └──────────────┘
```

### Microservices Architecture
- **Main API Service** (Port 8000): Query validation, similarity checking, cache management
- **Web Scraper Service** (Port 8001): Isolated Playwright-based scraping in Docker
- **AI Processing**: Gemini API for validation, embeddings, and summarization

## 📜 Features

- **Query Validation**: Classifies queries as valid search requests or personal commands using Gemini AI.
- **Similarity Detection**: Uses AI embeddings to find semantically similar queries, caching results for quick access.
- **Web Scraping**: Playwright-based service that scrapes Google/DuckDuckGo for fresh results, with anti-detection measures.
- **AI Summarization**: Generates structured summaries based on query type (recommendations, how-to, comparisons, etc.).
- **Caching System**: Stores recent queries and results in a JSON file, with auto-cleanup for efficiency.
- **Health Checks**: Built-in endpoints to monitor service health and performance.
- **Dockerized Services**: Easy deployment and scaling using Docker Compose.


## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- Google Gemini API Key

### 1. Environment Setup
```bash
# Clone the repository
git clone <repository-url>
cd web-browser-query-agent

# Create environment file
cp .env.example .env
# Add your GEMINI_API_KEY to .env
```

### 2. Install Dependencies
```bash
# Main API dependencies
pip install -r requirements.txt

# Scraper service dependencies (for local development)
pip install -r requirements-playwright.txt
```

### 3. Start Services
```bash
# Start web scraper service (Docker)
docker-compose up web-scraper -d

# Start main API service
python run.py

# Or run both with docker-compose
docker-compose up
```

### 4. Verify Setup
```bash
# Check main API
curl http://localhost:8000/health

# Check scraper service
curl http://localhost:8001/health

# Test query processing
curl -X POST http://localhost:8000/api/v1/process-query \
  -H "Content-Type: application/json" \
  -d '{"query": "best restaurants in Delhi"}'
```

## 📁 Project Structure

```
├── app/
│   ├── api/
│   │   └── routes.py              # FastAPI routes
│   ├── core/
│   │   └── config.py              # Configuration settings
│   ├── models/
│   │   └── schemas.py             # Pydantic models
│   └── services/
│       ├── query_validator.py     # AI-powered query validation
│       ├── similarity_checker.py  # Vector similarity detection
│       ├── web_scraper.py         # Web scraper client
│       └── cache_manager.py       # Query caching system
├── scraper/
│   ├── main.py                    # Scraper service FastAPI app
│   └── scraper_service.py         # Playwright automation
├── docker-compose.yml             # Service orchestration
├── Dockerfile.playwright          # Scraper service container
├── requirements.txt               # Main API dependencies
├── requirements-playwright.txt    # Scraper dependencies
└── run.py                         # Application entry point
```

## 🔧 Core Components

### 1. Query Validation Engine
Uses Gemini AI to intelligently classify queries as valid search requests vs personal commands.

**Examples:**
- ✅ Valid: `"Best restaurants in Delhi"`, `"How to cook pasta"`
- ❌ Invalid: `"Walk my pet"`, `"Add milk to grocery list"`

### 2. Similarity Detection System
Leverages Gemini's `text-embedding-004` model to detect semantically similar queries.

**How it works:**
- Converts queries to 768-dimensional vectors
- Uses cosine similarity with 75% threshold
- Caches results for instant responses

**Example:**
```
"Best places in Delhi" ↔ "Top Delhi attractions" → 85% similar (cache hit)
"Delhi restaurants" ↔ "Delhi hotels" → 45% similar (cache miss)
```

### 3. Web Scraping Pipeline
Playwright-based scraping service running in isolated Docker container.

**Features:**
- Searches Google/DuckDuckGo
- Extracts top 5 results
- Anti-detection measures
- Graceful fallback handling

### 4. AI Summarization
Query-type aware summarization using Gemini AI.

**Query Types:**
- **Recommendations**: Structured product/service lists
- **How-to**: Step-by-step instructions
- **Comparisons**: Side-by-side analysis
- **Location**: Places with addresses and ratings
- **News**: Timeline of events
- **General**: Comprehensive information

## 🛠️ API Endpoints

### Main Service (Port 8000)

#### Process Query (Primary Endpoint)
```bash
POST /api/v1/process-query
{
  "query": "best headphones under $100",
  "force_refresh": false
}
```

#### Validate Query
```bash
POST /api/v1/validate-query
{
  "query": "how to learn programming"
}
```

#### Check Similarity
```bash
POST /api/v1/check-similarity
{
  "query": "top programming tutorials"
}
```

#### Cache Management
```bash
GET /api/v1/cache-stats        # View cache statistics
DELETE /api/v1/clear-cache     # Clear all cached queries
POST /api/v1/cleanup-cache     # Remove old entries
```

### Scraper Service (Port 8001)

#### Scrape Web Results
```bash
POST /scrape
{
  "query": "machine learning tutorials"
}
```

## ⚙️ Configuration

### Environment Variables
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

### Cache Configuration
- **Storage**: JSON file (`query_cache.json`)
- **Similarity Threshold**: 75%
- **Auto-cleanup**: Keeps latest 50 entries
- **Persistence**: Survives service restarts

### Timeout Settings
- **Web Scraping**: 90 seconds
- **AI Summarization**: 25 seconds
- **Overall Request**: 120 seconds

## 🧪 Testing

### Manual Testing
```bash
# Test invalid query
curl -X POST http://localhost:8000/api/v1/process-query \
  -H "Content-Type: application/json" \
  -d '{"query": "walk my dog and buy groceries"}'

# Test valid new query
curl -X POST http://localhost:8000/api/v1/process-query \
  -H "Content-Type: application/json" \
  -d '{"query": "best pizza places in NYC"}'

# Test similar query (should hit cache)
curl -X POST http://localhost:8000/api/v1/process-query \
  -H "Content-Type: application/json" \
  -d '{"query": "top NYC pizza restaurants"}'
```

### Health Checks
```bash
# Check if services are healthy
curl http://localhost:8000/health
curl http://localhost:8001/health
```

## 🚧 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check if ports are available
netstat -tulpn | grep :8000
netstat -tulpn | grep :8001

# Check Docker container logs
docker-compose logs web-scraper
```

#### Scraping Failures
- **Rate Limiting**: Implement delays between requests
- **IP Blocking**: Use proxy rotation (production)
- **JavaScript Issues**: Ensure Playwright properly waits for content

#### Cache Issues
```bash
# Clear cache if corrupted
rm query_cache.json

# Check cache stats
curl http://localhost:8000/api/v1/cache-stats
```

#### Gemini API Issues
- Verify API key is correct
- Check quota limits in Google AI Studio
- Monitor rate limiting

## 🔄 Deployment

### Docker Deployment
```bash
# Build and run all services
docker-compose up --build

# Scale scraper service
docker-compose up --scale web-scraper=3
```

### Production Considerations
- Replace JSON cache with vector database (Pinecone, Weaviate)
- Add authentication and rate limiting
- Implement proper logging and monitoring
- Use environment-specific configurations
- Add CI/CD pipeline

## 🛡️ Security

### Current Measures
- Input sanitization and length limits
- URL validation for scraped content
- No personal data storage
- Rate limiting (planned)

### Production Enhancements Needed
- API authentication (JWT/OAuth)
- Request rate limiting
- Input validation middleware
- CORS configuration
- SSL/TLS encryption



## Scaling Strategies
- Horizontal scaling of scraper and API services
- Implement proper vector database
- Use Redis or similar for caching
- Load balancing for API service

### Potential Improvements
- Use advanced AI models for better query understanding
- Use structured output formats (JSON, Markdown) for results
- Implement user authentication and session management
- Rate limiting to prevent abuse

## 📄 License

This project is for interview/demo purposes.

## 🙋‍♂️ Support

For questions or issues:
- Check the troubleshooting section above
- Review logs: `docker-compose logs`
- Test individual components with curl commands

---

**Built with:** FastAPI, Playwright, Docker, Gemini AI, Python 3.9+