from cgitb import reset
import email
import json
import os
import random
import re
from email import message
from encodings import utf_8

import bcrypt
import jwt
import psycopg2
import redis
import yagmail
from dotenv import load_dotenv
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


def send_reset_password_email(reset_code):
    contents = [
        "Here is your requested code to reset your password",
        "Code: {}".format(reset_code),
        "If you received this email erroneously please ignore it"
    ]
    yag = yagmail.SMTP('jamyersondev@gmail.com',
                       os.environ.get("GMAIL_APP_PASSWORD"))
    yag.send('jamyersondev@gmail.com',
             'Quora Reset Password Request', contents)


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


def get_decoded_jwt_token(jwt_token):
    return jwt.decode(jwt_token, key=os.environ.get(
        'JWT_KEY'), algorithms=['HS256', ])


@app.get("/", status_code=200)
def root():
    return {"message": "Hello justin"}


@api_router.post("/auth/register/", status_code=201)
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

        error_data = {
            "Error": "Enter a valid password that is longer or equal to 8 characters"
        }
        return JSONResponse(error_data, status_code=400)

    error_data = {
        "Error": "Enter a valid email address"
    }
    return JSONResponse(error_data, status_code=400)


@app.get("/auth/login/", status_code=200)
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
            return JSONResponse(payload_data, status_code=200)

        else:
            error_data = {
                "email": email,
                "Error": "Password is incorrect"
            }
            return JSONResponse(error_data, status_code=400)

    except:
        error_data = {
            "Error": "Email address was not found"
        }
        return JSONResponse(error_data, status_code=400)


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


@api_router.post("/auth/password-reset", status_code=200)
def reset_password(new_password, token):
    try:
        r = redis.Redis()
        decoded_jwt = jwt.decode(token, key=os.environ.get(
            'JWT_KEY'), algorithms=['HS256', ])
        email = decoded_jwt['email']
        reset_token = int(
            ''.join(["{}".format(random.randint(0, 9)) for num in range(0, 5)]))
        send_reset_password_email(reset_token)
        key = "password-reset-token-{}".format(email[1: len(email)-1])
        r.set("key", key)
        r.set("reset-token", reset_token)
        message_data = {
            "new_password": new_password,
            "token": token,
            "Message": "You will receive a reset token on your email that will allow you to reset your password"
        }
        return JSONResponse(message_data, status_code=200)
    except:
        error_data = {
            "Error": "There was an unforseen error that was encountered"}
        print(error_data)
        return JSONResponse(error_data, status_code=400)


app.include_router(api_router)

if __name__ == '__main__':
    # add_user_to_db('ababa@gmail.com', 'Aba', 'Saba', 'password')
    login_user("lamyerson@gmail.com", 'Kratos23')
    # change_password(token, 'Kratos22', 'Kratos23')
    reset_password("Test", token)
