from encodings import utf_8
import psycopg2

from config import config
from fastapi import FastAPI, APIRouter, HTTPException

import bcrypt
import re
import jwt

from user import User
from user_data import USERS

app = FastAPI(openapi_url="/openapi.json")
api_router = APIRouter()

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'


@app.get("/", status_code=200)
def root():
    return {"message": "Hello User"}


def hash_password(password):
    bytePwd = password.encode('utf-8')
    hashed_pw = bcrypt.hashpw(bytePwd, bcrypt.gensalt())
    return hashed_pw


def validate_user_password(actual_password_hashed, provided_password: str):
    return bcrypt.checkpw(provided_password.encode('utf-8'), actual_password_hashed)


def check_email_valid(email):
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False


@api_router.post("/auth/register/", status_code=201, response_model=User)
def add_user_to_db(email, firstName, lastName, password):
    if check_email_valid(email):
        if (len(password) >= 8):
            params = config()
            conn = psycopg2.connect(**params)
            # create a cursor
            cur = conn.cursor()
            query = 'INSERT INTO users(email, firstName, lastName, password) VALUES (%s, %s, %s, %s)'
            cur.execute(query, (email, firstName,
                        lastName, hash_password(password)))
            conn.commit()
            print("Records created successfully")
            cur.close()
            conn.close()
            encoded = jwt.encode({"email": email}, "secret", algorithm="HS256")
            print(jwt.decode(encoded, "secret", algorithms=["HS256"]))


@api_router.post("/auth/login/", status_code=200, response_model=User)
def login_user(email, password):
    user_password = None
    params = config()
    conn = psycopg2.connect(**params)
    # create a cursor
    cur = conn.cursor()
    try:
        email = "'{}'".format(email)
        query = "SELECT password FROM users WHERE email = {}".format(
            email)
        cur.execute(query)
        result = cur.fetchall()
        for row in result:
            user_password = row[0]
    except:
        print("Error, user with email {} not found".format(email))

    print(user_password.encode('utf-8'))
    print(hash_password(password))

    validate_user_password(bytes(user_password), password)


app.include_router(api_router)

if __name__ == '__main__':
    # add_user_to_db('test@gmail.com', 'John', 'Doe', 'password')
    login_user("test@gmail.com", 'password')
