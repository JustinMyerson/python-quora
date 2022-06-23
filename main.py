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
from pydantic import BaseModel
import redis
import yagmail
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse

from config import config
from user import User, resetPassword
from user_data import USERS

app = FastAPI(openapi_url="/openapi.json")
api_router = APIRouter()

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

global token

load_dotenv()

r = redis.Redis()


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


@app.post("/auth/password-reset", status_code=200)
def reset_password(token):
    try:
        decoded_jwt = jwt.decode(token, key=os.environ.get(
            'JWT_KEY'), algorithms=['HS256', ])
        email = decoded_jwt['email']
        reset_token = int(
            ''.join(["{}".format(random.randint(0, 9)) for num in range(0, 5)]))
        send_reset_password_email(reset_token)
        key = "password-reset-token-{}".format(email[1: len(email)-1])
        r.set("key", key)
        r.set("reset_token", reset_token)
        message_data = {
            "token": token,
            "Message": "You will receive a reset token on your email that will allow you to reset your password"
        }
        return JSONResponse(message_data, status_code=200)
    except:
        error_data = {
            "Error": "There was an unforseen error that was encountered"}
        print(error_data)
        return JSONResponse(error_data, status_code=400)


@app.post("/auth/password-reset/confirm")
def confirm_reset_password(resetPasswordData: resetPassword):
    try:
        user_reset_token = int(r.get('reset_token'))
        user_email = str(r.get("key"))
    except:
        error_data = {
            "Error": "No reset token could be found in the database"}
        return JSONResponse(error_data, status_code=400)
    if user_reset_token == int(resetPasswordData.reset_token):
        if (resetPasswordData.email in user_email):
            if (len(resetPasswordData.new_password) >= 8):
                payload_data = {
                    "email": resetPasswordData.email,
                    "reset_token": resetPasswordData.reset_token,
                    "message": "Passed, password reset token matches one in Redis"
                }
                return JSONResponse(payload_data, status_code=201)
            else:
                error_data = {
                    "Error": "Password is not valid, please re-enter a valid password"
                }
                return JSONResponse(error_data, status_code=400)
        else:
            error_data = {
                "Error": "Token does not match the email that was provided"
            }
            return JSONResponse(error_data, status_code=400)
    else:
        error_data = {
            "Error": "The reset password code entered was incorrect or has expired"}
        return JSONResponse(error_data, status_code=400)


app.include_router(api_router)

if __name__ == '__main__':
    # add_user_to_db('ababa@gmail.com', 'Aba', 'Saba', 'password')
    login_user("lamyerson@gmail.com", 'Kratos23')
    print(r.get("key"))
    # change_password(token, 'Kratos22', 'Kratos23')
    reset_password(token)
    # confirm_reset_password("27806")
