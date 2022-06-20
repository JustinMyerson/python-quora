from email import message
import email
import os
import re
from encodings import utf_8
from dotenv import load_dotenv
import jwt
import json

import bcrypt
import psycopg2
from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse

from config import config
from user import User
from user_data import USERS

app = FastAPI(openapi_url="/openapi.json")
api_router = APIRouter()

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

global token

load_dotenv()


def hash_password(password):
    bytePwd = bytes(password, encoding='utf-8')
    hashed_pw = bcrypt.hashpw(bytePwd, bcrypt.gensalt())
    return hashed_pw.decode('utf8')


def validate_user_password(actual_password_hashed, provided_password: str):
    return bcrypt.checkpw(provided_password.encode('utf-8'), actual_password_hashed)


def check_email_valid(email):
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False


@app.get("/", status_code=200)
def root():
    return {"message": "Hello justin"}


@api_router.post("/auth/register/", status_code=201, response_model=User)
def add_user_to_db(email, firstName, lastName, password):
    if check_email_valid(email):
        if (len(password) >= 8):
            params = config()
            conn = psycopg2.connect(**params)
            cur = conn.cursor()
            query = 'INSERT INTO users(email, firstName, lastName, password) VALUES (%s, %s, %s, %s)'
            cur.execute(query, (email, firstName,
                        lastName, hash_password(password)))
            conn.commit()
            print("Records created successfully")
            cur.close()
            conn.close()

            payload_data = {
                "email": email,
                "firstName": firstName,
                "lastName": lastName,
                "password": hash_password(password)
            }

            token = jwt.encode(
                payload=payload_data,
                key=os.environ.get('JWT_KEY')
            )

            print(token)

            return JSONResponse(content=payload_data, status_code=201)
        return JSONResponse(status_code=400, message="Enter a valid password that is longer or equal to 8 characters")
    return JSONResponse(status_code=400, message="Enter a valid email address")


@api_router.get("/auth/login/", status_code=200, response_model=User)
def login_user(email, password):
    user_password = None
    params = config()
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    try:
        email = "'{}'".format(email)
        query = "SELECT password FROM users WHERE email = {}".format(
            email)
        cur.execute(query)
        result = cur.fetchall()

        for row in result:
            user_password = row[0]

        if (validate_user_password(bytes(user_password, encoding='utf-8'), password)):
            print("hooray")

            payload_data = {
                "email": email,
                "password": user_password
            }

            global token
            token = jwt.encode(
                payload=payload_data,
                key=os.environ.get('JWT_KEY')
            )

            print(token)

        else:
            return {
                "errors": [
                    {
                        "status": "400",
                        "title":  "Password Incorrect"
                    }
                ]
            }

    except:
        return {
            "errors": [
                {
                    "status": "400",
                    "title":  "Email Not Found",
                    "detail": "Email address was not found in the DB"
                }
            ]
        }


def change_password(token, old_password, new_password):
    email = ""
    password = ""
    params = config()
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    if jwt.decode(token, key=os.environ.get('JWT_KEY'), algorithms=['HS256', ]):
        decoded_jwt = jwt.decode(token, key=os.environ.get(
            'JWT_KEY'), algorithms=['HS256', ])
        email = decoded_jwt['email']
        password = decoded_jwt['password']
        print(password, 'PASSWORD')

        if validate_user_password(bytes(password, encoding='utf-8'), old_password):
            new_password = "'{}'".format(hash_password(new_password))
            query = "UPDATE users SET password = {} WHERE email = {};".format(
                new_password, email)
            cur.execute(query)
            conn.commit()
            cur.close()
            conn.close()


app.include_router(api_router)

if __name__ == '__main__':
    #add_user_to_db('ababa@gmail.com', 'Aba', 'Saba', 'password')
    login_user("lamyerson@gmail.com", 'Kratos22')
    change_password(token, 'Kratos22', 'Kratos23')
