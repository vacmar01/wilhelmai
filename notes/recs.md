# Architecture Recommendations for wilhelm.ai

## Philosophy: Pragmatic Python, Not Enterprise Java

Keep your functional approach with DSPy. Don't over-abstract. If it works, it works.

## 🎯 Pragmatic Improvements (Stay Functional)

### 1. Simple Configuration (5 minutes)
**Problem**: Hardcoded values scattered across files
**Solution**: Single config file

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/cache.db")
MODEL_PATH = os.getenv("MODEL_PATH", "models/kimi_finder.json") 
DSPY_MODEL = os.getenv("DSPY_MODEL", "groq/moonshotai/kimi-k2-instruct")
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))
RADIOPAEDIA_COOKIE = os.getenv("RADIOPAEDIA_COOKIE", "")
```

### 2. Connection Reuse (10 minutes)
**Problem**: Creating new HTTP clients for each request
**Solution**: Module-level client reuse

```python
# lib.py - add this at module level
_http_client = None

def get_http_client():
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)
    return _http_client

# Usage: client = get_http_client() instead of httpx.AsyncClient()
```

### 3. Better Error Handling (15 minutes)
**Problem**: Exceptions crash the entire request
**Solution**: Graceful failure with logging

```python
# lib.py
import logging

logger = logging.getLogger(__name__)

async def safe_get_article(url: str, cursor) -> str | None:
    try:
        return await get_article_text(url, cursor)
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None  # Let caller decide what to do
```

### 4. Extract Secrets (2 minutes)
**Problem**: Session cookie hardcoded in source
**Solution**: Environment variable

```python
# Move the giant radiopaedia cookie to .env file
RADIOPAEDIA_HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "cookie": os.getenv("RADIOPAEDIA_COOKIE", ""),  # Move to .env
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "de-DE,de;q=0.7",
}
```

### 5. Simple Retry (10 minutes)
**Problem**: Single failures kill requests
**Solution**: Exponential backoff retry

```python
import time
import random

async def retry_on_failure(func, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(wait_time)

# Usage: result = await retry_on_failure(search_radiopaedia, query, cursor)
```

### 6. File Organization (Keep It Simple)
**Current**: Everything mixed together
**Suggested**: Light separation without over-engineering

```
├── main.py          # UI only - FastHTML routes and components
├── lib.py           # Core DSPy logic - keep as is mostly
├── config.py        # Settings and environment variables
├── database.py      # Just the DB setup and operations
└── http_utils.py    # HTTP helpers and retry logic
```

### 7. Better Logging (10 minutes)
**Problem**: `print()` statements for debugging
**Solution**: Structured logging

```python
# Replace print() with proper logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Instead of: print(f"answered query in {end_time - start_time:.2f} seconds")
# Use: logger.info(f"Query answered in {end_time - start_time:.2f}s", extra={"query": query})
```

## 🚀 What NOT to Change

- ✅ Keep your functional approach with DSPy
- ✅ Keep the simple FastHTML structure  
- ✅ Keep using module-level variables where it makes sense
- ✅ Don't create classes for everything
- ✅ Don't add dependency injection containers
- ✅ Don't create abstract interfaces unless you need them

## 🎯 Priority Order (Pragmatic)

### Phase 1: Reliability (1 hour total)
1. **Move secrets to .env** (2 min) - Security fix
2. **Reuse HTTP connections** (10 min) - Performance win
3. **Add basic retry to critical HTTP calls** (15 min) - Reliability
4. **Better logging instead of print()** (10 min) - Debugging
5. **Extract database code** (20 min) - Organization

### Phase 2: Polish (Optional, 30 min)
6. **Add graceful error handling** (15 min) - User experience
7. **Cache optimization with TTL** (15 min) - Performance

## 🎖️ Expected Benefits

- **Reliability**: HTTP failures won't crash the app
- **Performance**: Connection reuse reduces latency
- **Maintainability**: Cleaner separation without over-engineering  
- **Security**: Secrets out of source code
- **Debuggability**: Proper logging instead of print statements

## 🤝 Implementation Notes

- Keep changes incremental - don't refactor everything at once
- Test each change independently 
- Maintain the functional style you already have
- Focus on **robust simplicity**, not enterprise complexity
- If something works well, don't change it just to be "cleaner"

The goal is making your existing functional code more resilient to real-world failures, not turning it into Spring Boot.
