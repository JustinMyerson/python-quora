from fastapi import FastAPI, APIRouter

app = FastAPI(openapi_url="/openapi.json")
api_router = APIRouter()


@app.get("/", status_code=200)
async def root():
    return {"message": "Hello User"}


app.include_router(api_router)
