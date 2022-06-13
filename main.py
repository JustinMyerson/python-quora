import email
from fastapi import FastAPI, APIRouter

from user import User
from user_data import USERS

app = FastAPI(openapi_url="/openapi.json")
api_router = APIRouter()


@app.get("/", status_code=200)
async def root():
    return {"message": "Hello User"}


@app.post("/auth/register", status_code=201, response_model=User)
async def register_user(*, userCreated: User) -> dict:
    user_entry = User(
        email=user_email,
        firstName=user_first_name,
        lastName=user_last_name,
        password=user_password,
    )
    USERS.append(user_entry.dict())

    return user_entry

app.include_router(api_router)
