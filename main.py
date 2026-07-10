from fastapi import FastAPI , Request
from fastapi.responses import JSONResponse
from authentication import route
from core.limiter import limiter
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

app = FastAPI()

app.state.limiter = limiter

app.include_router(route.router,prefix='/auth')

#Error Handle
@app.exception_handler(RateLimitExceeded)
def rate_limit_hander(request: Request, exc: RateLimitExceeded ):
    return JSONResponse(
        status_code=429,
        content={
            "detail":"Too many Requests"
        }
    )


app.add_exception_handler(
    RateLimitExceeded,
    rate_limit_hander
)

app.get("/health")
def health():
    return JSONResponse({
        "message":"API is active"
    })