from fastapi import FastAPI, APIRouter, HTTPException

from user import User
from user_data import USERS

app = FastAPI(openapi_url="/openapi.json")
api_router = APIRouter()


@app.get("/", status_code=200)
def root():
    return {"message": "Hello User"}


@api_router.get("/user/{user_email}", status_code=200, response_model=User)
def fetch_recipe(*, user_email: str):
    result = [user for user in USERS if user["email"] == user_email]
    if not result:
        raise HTTPException(
            status_code=404, detail=f"User with email: {user_email} not found"
        )
    return result[0]


@api_router.post("/auth/register/", status_code=201, response_model=User)
def register_user(*, userCreated: User) -> dict:
    new_user_id = len(USERS + 1)
    user_entry = User(
        id=new_user_id,
        email=userCreated.email,
        firstName=userCreated.firstName,
        lastName=userCreated.lastName,
        password=userCreated.password,
    )
    USERS.append(user_entry.dict())

    return user_entry


app.include_router(api_router)
