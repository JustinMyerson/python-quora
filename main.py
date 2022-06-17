import psycopg2

from config import config
from connect_db import connect
from fastapi import FastAPI, APIRouter, HTTPException

import bcrypt
import re

from user import User
from user_data import USERS

app = FastAPI(openapi_url="/openapi.json")
api_router = APIRouter()


# @app.get("/", status_code=200)
# def root():
#     return {"message": "Hello User"}


# @api_router.get("/user/{user_email}", status_code=200, response_model=User)
# def fetch_recipe(*, user_email: str):
#     result = [user for user in USERS if user["email"] == user_email]
#     if not result:
#         raise HTTPException(
#             status_code=404, detail=f"User with email: {user_email} not found"
#         )
#     return result[0]

def hash_password(password: str):
    bytePwd = password.encode('utf-8')
    # Generate salt
    mySalt = bcrypt.gensalt()
    # Hash password
    hash = bcrypt.hashpw(bytePwd, mySalt)


regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'


def check_email_valid(email):
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False


@api_router.post("/auth/register/", status_code=201, response_model=User)
def register_user(*, userCreated: User) -> dict:
    email = ""
    if check_email_valid(userCreated.email):
        email = userCreated.email
        user_entry = User(
            email=email,
            firstName=userCreated.firstName,
            lastName=userCreated.lastName,
            # Ensure that the password is stored in a hashed format
            password=hash_password(userCreated.password),
        )
    USERS.append(user_entry.dict())
    print(USERS)

    return user_entry


app.include_router(api_router)

if __name__ == '__main__':
    connect()
