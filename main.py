from fastapi import FastAPI , Request
from fastapi.responses import JSONResponse
from auth import router
from limiter import limiter

app = FastAPI()

app.include_router(router,prefix='/auth')

from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

#Error Handle
@app.exception_handler(RateLimitExceeded)
def rate_limit_hander(request: Request, exc: RateLimitExceeded ):
    return JSONResponse(
        status_code=429,
        content={
            "detail":"Too many Requests"
        }
    )

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    rate_limit_hander
)

app.get("/health")
def health():
    return JSONResponse({
        "message":"API is active"
    })